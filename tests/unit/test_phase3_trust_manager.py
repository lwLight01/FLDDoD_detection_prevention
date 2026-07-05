"""
tests/unit/test_phase3_trust_manager.py
---------------------------------------
Unit tests for TrustManager (Milestone 17).

Tests:
  - Default trust score is 1.0 for unknown clients.
  - Cosine similarity updates scores via EMA.
  - Outlier (adversarial) clients receive penalised scores.
  - Client with persistently low score is auto-banned.
  - get_weight() returns 0 for banned clients.
  - Banned clients are excluded from get_banned_clients().
  - reset_client() restores trust score to 1.0.

Ref: docs/DevelopmentRoadmap.md — Milestone 17
"""

import numpy as np
import pytest

from src.fl_server.trust_manager import TrustManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tm() -> TrustManager:
    """Return a TrustManager with tight thresholds for test isolation."""
    return TrustManager(
        penalty_threshold=0.7,
        auto_ban_threshold=0.1,
        ema_alpha=0.5,
    )


def _random_arrays(n_params: int = 100, seed: int = 0) -> list:
    """Create a list of 1-D numpy arrays for a simulated model update."""
    rng = np.random.default_rng(seed)
    return [rng.standard_normal(n_params)]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDefaultBehaviour:
    def test_default_score_is_one(self, tm: TrustManager) -> None:
        assert tm.get_score("unknown_client") == pytest.approx(1.0)

    def test_not_banned_by_default(self, tm: TrustManager) -> None:
        assert tm.is_banned("unknown_client") is False

    def test_get_weight_proportional_to_examples(self, tm: TrustManager) -> None:
        # New client has trust 1.0, so weight == num_examples
        w = tm.get_weight("new_client", num_examples=500)
        assert w == pytest.approx(500.0)


class TestUpdateRound:
    def test_identical_updates_keep_high_score(self, tm: TrustManager) -> None:
        """All clients send the same update → cosine sim = 1.0 → score stays ~1.0."""
        shared = _random_arrays(seed=42)
        updates = {
            "client_0": shared,
            "client_1": shared,
            "client_2": shared,
        }
        scores = tm.update_round(updates)
        for score in scores.values():
            assert score >= 0.9, f"Expected high score, got {score}"

    def test_outlier_client_gets_lower_score(self, tm: TrustManager) -> None:
        """A client sending an inverse gradient should receive a lower trust score."""
        honest = _random_arrays(seed=1)
        adversarial = [-arr for arr in honest]  # Opposite direction

        updates = {
            "honest_0": honest,
            "honest_1": honest,
            "honest_2": honest,
            "attacker": adversarial,
        }
        scores = tm.update_round(updates)

        assert scores["attacker"] < scores["honest_0"], (
            f"Attacker score {scores['attacker']:.4f} should be less than "
            f"honest score {scores['honest_0']:.4f}"
        )

    def test_score_bounded_between_zero_and_one(self, tm: TrustManager) -> None:
        """Trust scores must always be in [0.0, 1.0]."""
        rng = np.random.default_rng(99)
        for round_num in range(10):
            updates = {
                f"c{i}": [rng.standard_normal(50)] for i in range(5)
            }
            scores = tm.update_round(updates)
            for cid, score in scores.items():
                assert 0.0 <= score <= 1.0, (
                    f"Score out of range: {cid}={score}"
                )

    def test_empty_update_dict_returns_empty(self, tm: TrustManager) -> None:
        scores = tm.update_round({})
        assert scores == {}

    def test_single_client_update(self, tm: TrustManager) -> None:
        """Single client: median equals itself → cosine sim = 1.0."""
        updates = {"solo_client": _random_arrays(seed=7)}
        scores = tm.update_round(updates)
        assert "solo_client" in scores
        assert scores["solo_client"] >= 0.9


class TestAutoban:
    def test_persistently_outlier_client_gets_banned(self) -> None:
        """A client sending consistently adversarial updates is auto-banned."""
        tm = TrustManager(
            penalty_threshold=0.7,
            auto_ban_threshold=0.3,
            ema_alpha=0.3,  # Faster decay for test
        )
        honest = _random_arrays(seed=1)
        adversarial = [-arr for arr in honest]

        for _ in range(20):  # Repeated rounds of adversarial behaviour
            tm.update_round({
                "honest_0": honest,
                "honest_1": honest,
                "honest_2": honest,
                "attacker": adversarial,
            })

        assert tm.is_banned("attacker"), "Attacker should have been auto-banned"

    def test_banned_client_weight_is_zero(self, tm: TrustManager) -> None:
        """Banned clients contribute zero weight to aggregation."""
        tm._banned["evil_client"] = True
        assert tm.get_weight("evil_client", num_examples=10000) == 0.0

    def test_get_banned_clients_lists_banned(self) -> None:
        tm = TrustManager()
        tm._banned["alice"] = True
        tm._banned["bob"] = False
        banned = tm.get_banned_clients()
        assert "alice" in banned
        assert "bob" not in banned


class TestResetClient:
    def test_reset_restores_score(self, tm: TrustManager) -> None:
        tm._scores["suspect"] = 0.05
        tm._banned["suspect"] = True
        tm.reset_client("suspect")
        assert tm.get_score("suspect") == pytest.approx(1.0)
        assert tm.is_banned("suspect") is False

    def test_reset_unknown_client_sets_one(self, tm: TrustManager) -> None:
        tm.reset_client("never_seen")
        assert tm.get_score("never_seen") == pytest.approx(1.0)


class TestGetAllScores:
    def test_returns_copy_not_reference(self, tm: TrustManager) -> None:
        tm._scores["c0"] = 0.8
        snapshot = tm.get_all_scores()
        snapshot["c0"] = 0.0  # Mutate snapshot
        assert tm.get_score("c0") == pytest.approx(0.8)  # Original unchanged

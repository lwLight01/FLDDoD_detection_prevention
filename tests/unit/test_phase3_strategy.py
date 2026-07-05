"""
tests/unit/test_phase3_strategy.py
-----------------------------------
Unit tests for AdaptiveTrustStrategy (Milestones 15, 17, 18).

Tests:
  - Strategy aggregates correctly with homogeneous clients.
  - Adversarial client's contribution is reduced.
  - Banned clients are excluded from aggregation.
  - Empty results return (None, {}).
  - Aggregated parameters have correct shapes.
  - Metrics dict contains expected keys.

Ref: docs/DevelopmentRoadmap.md — Milestones 15, 17, 18
"""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from flwr.common import (
    Code,
    FitRes,
    Parameters,
    Status,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy

from src.fl_server.strategy import AdaptiveTrustStrategy
from src.fl_server.trust_manager import TrustManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client_proxy(cid: str) -> ClientProxy:
    """Create a mock ClientProxy with a given client ID."""
    proxy = MagicMock(spec=ClientProxy)
    proxy.cid = cid
    return proxy


def _make_fit_res(
    parameters: List[np.ndarray],
    num_examples: int = 100,
) -> FitRes:
    """Create a FitRes from a list of numpy arrays."""
    return FitRes(
        status=Status(code=Code.OK, message="OK"),
        parameters=ndarrays_to_parameters(parameters),
        num_examples=num_examples,
        metrics={},
    )


def _random_params(n: int = 50, seed: int = 0) -> List[np.ndarray]:
    """Generate a list with one random numpy array of length n."""
    rng = np.random.default_rng(seed)
    return [rng.standard_normal(n).astype(np.float32)]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def strategy() -> AdaptiveTrustStrategy:
    tm = TrustManager(
        penalty_threshold=0.7,
        auto_ban_threshold=0.1,
        ema_alpha=0.5,
    )
    return AdaptiveTrustStrategy(
        trust_manager=tm,
        fraction_fit=1.0,
        min_fit_clients=1,
        min_available_clients=1,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAggregateEmpty:
    def test_no_results_returns_none(self, strategy: AdaptiveTrustStrategy) -> None:
        aggregated, metrics = strategy.aggregate_fit(
            server_round=1, results=[], failures=[]
        )
        assert aggregated is None
        assert metrics == {}


class TestAggregateHomogeneous:
    def test_homogeneous_clients_aggregate(self, strategy: AdaptiveTrustStrategy) -> None:
        """Three clients with identical updates → aggregation succeeds."""
        params = _random_params(seed=1)
        results = [
            (_make_client_proxy(f"c{i}"), _make_fit_res(params, num_examples=100))
            for i in range(3)
        ]

        aggregated, metrics = strategy.aggregate_fit(
            server_round=1, results=results, failures=[]
        )

        assert aggregated is not None
        agg_arrays = parameters_to_ndarrays(aggregated)
        assert len(agg_arrays) == len(params)
        assert agg_arrays[0].shape == params[0].shape

    def test_aggregated_matches_input_for_identical_params(
        self, strategy: AdaptiveTrustStrategy
    ) -> None:
        """When all clients send the same params, the aggregate should match."""
        params = _random_params(seed=5)
        results = [
            (_make_client_proxy(f"c{i}"), _make_fit_res(params, num_examples=100))
            for i in range(3)
        ]

        aggregated, _ = strategy.aggregate_fit(
            server_round=1, results=results, failures=[]
        )
        assert aggregated is not None
        agg = parameters_to_ndarrays(aggregated)[0]
        np.testing.assert_array_almost_equal(agg, params[0], decimal=4)

    def test_metrics_dict_has_expected_keys(self, strategy: AdaptiveTrustStrategy) -> None:
        params = _random_params(seed=2)
        results = [
            (_make_client_proxy(f"c{i}"), _make_fit_res(params))
            for i in range(2)
        ]
        _, metrics = strategy.aggregate_fit(
            server_round=3, results=results, failures=[]
        )
        assert "round" in metrics
        assert "active_clients" in metrics
        assert "banned_clients" in metrics
        assert int(metrics["round"]) == 3
        assert int(metrics["active_clients"]) == 2


class TestAggregateAdversarial:
    def test_adversarial_client_reduces_global_loss(
        self, strategy: AdaptiveTrustStrategy
    ) -> None:
        """After penalising an adversarial client, its trust weight should be < honest."""
        honest_params = _random_params(seed=10)
        adversarial_params = [-p for p in honest_params]

        results = [
            (_make_client_proxy("honest_0"), _make_fit_res(honest_params)),
            (_make_client_proxy("honest_1"), _make_fit_res(honest_params)),
            (_make_client_proxy("honest_2"), _make_fit_res(honest_params)),
            (_make_client_proxy("attacker"), _make_fit_res(adversarial_params)),
        ]

        _, metrics = strategy.aggregate_fit(
            server_round=1, results=results, failures=[]
        )

        trust_attacker = strategy.trust_manager.get_score("attacker")
        trust_honest = strategy.trust_manager.get_score("honest_0")
        assert trust_attacker < trust_honest, (
            f"Attacker trust {trust_attacker:.4f} should be less than "
            f"honest trust {trust_honest:.4f}"
        )


class TestBannedClientFiltering:
    def test_banned_client_excluded_from_aggregation(self) -> None:
        """A banned client should not contribute to the aggregated parameters."""
        tm = TrustManager(auto_ban_threshold=0.9)  # Very high threshold → ban easily
        tm._banned["evil"] = True  # Pre-ban

        strategy = AdaptiveTrustStrategy(
            trust_manager=tm,
            fraction_fit=1.0,
            min_fit_clients=1,
            min_available_clients=1,
        )

        honest_params = _random_params(seed=20)
        # Evil client sends all-ones (easily distinguishable)
        evil_params = [np.ones(50, dtype=np.float32)]

        results = [
            (_make_client_proxy("honest"), _make_fit_res(honest_params)),
            (_make_client_proxy("evil"), _make_fit_res(evil_params)),
        ]

        aggregated, metrics = strategy.aggregate_fit(
            server_round=1, results=results, failures=[]
        )

        assert aggregated is not None
        agg = parameters_to_ndarrays(aggregated)[0]
        # Aggregate should be close to honest_params only
        np.testing.assert_array_almost_equal(agg, honest_params[0], decimal=4)
        assert int(metrics["banned_clients"]) >= 1

    def test_all_banned_returns_none(self) -> None:
        tm = TrustManager()
        tm._banned["c0"] = True
        tm._banned["c1"] = True

        strategy = AdaptiveTrustStrategy(
            trust_manager=tm,
            fraction_fit=1.0,
            min_fit_clients=1,
            min_available_clients=1,
        )

        results = [
            (_make_client_proxy("c0"), _make_fit_res(_random_params())),
            (_make_client_proxy("c1"), _make_fit_res(_random_params())),
        ]

        aggregated, _ = strategy.aggregate_fit(
            server_round=1, results=results, failures=[]
        )
        assert aggregated is None

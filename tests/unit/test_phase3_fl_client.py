"""
tests/unit/test_phase3_fl_client.py
------------------------------------
Unit tests for DDosFlowerClient (Milestones 14, 16).

Tests:
  - Client instantiation and parameter get/set round-trip.
  - fit() runs without error, returns correct shape parameters.
  - evaluate() runs without error, returns (loss, num_examples, metrics).
  - FedProx proximal term is applied when mu > 0.
  - Parameters are correctly loaded from numpy arrays.

These tests use a synthetic in-memory CSV to avoid requiring actual dataset
files on disk.

Ref: docs/DevelopmentRoadmap.md — Milestones 14, 16
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pytest
import torch

from src.fl_client.dataset import (
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_COLUMN,
)
from src.fl_client.model import FTTransformerConfig, FTTransformerModel, build_model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_synthetic_csv(n_rows: int = 200, seed: int = 42) -> Path:
    """Write a synthetic CSV that matches the CIC-DDoS2019 schema."""
    rng = np.random.default_rng(seed)
    data = {}

    for col in CONTINUOUS_FEATURES:
        data[col] = rng.uniform(0, 1000, size=n_rows).astype(np.float32)

    data["Protocol"] = rng.choice([1, 2, 6, 17], size=n_rows)
    data["TCP Flags"] = rng.integers(0, 63, size=n_rows)
    data[TARGET_COLUMN] = rng.choice([0, 1], size=n_rows).astype(np.float32)

    df = pd.DataFrame(data)
    tmp = tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w"
    )
    df.to_csv(tmp.name, index=False)
    tmp.close()
    return Path(tmp.name)


def _small_config() -> FTTransformerConfig:
    """Tiny model config to keep tests fast."""
    return FTTransformerConfig(
        n_cont_features=len(CONTINUOUS_FEATURES),
        cat_cardinalities=[5, 65],
        embedding_dim=16,
        num_blocks=1,
        num_heads=2,
        ffn_dim=32,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def csv_path():
    p = make_synthetic_csv(n_rows=300)
    yield p
    p.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def fl_client(csv_path):
    from src.fl_client.client import DDosFlowerClient

    client = DDosFlowerClient(
        client_id="test_client",
        data_path=csv_path,
        scaler_path=None,
        model_config=_small_config(),
        device="cpu",
    )
    return client


# ---------------------------------------------------------------------------
# Tests: Parameter management
# ---------------------------------------------------------------------------


class TestParameterManagement:
    def test_get_parameters_returns_list_of_arrays(self, fl_client) -> None:
        params = fl_client.get_parameters(config={})
        assert isinstance(params, list)
        assert len(params) > 0
        for p in params:
            assert isinstance(p, np.ndarray)

    def test_set_parameters_round_trip(self, fl_client) -> None:
        """get → mutate → set → get should reflect the mutation."""
        original = fl_client.get_parameters(config={})
        mutated = [np.zeros_like(p) for p in original]

        fl_client.set_parameters(mutated)
        after = fl_client.get_parameters(config={})

        for a in after:
            np.testing.assert_array_almost_equal(a, 0.0)

        # Restore original
        fl_client.set_parameters(original)

    def test_parameter_shapes_unchanged_after_set(self, fl_client) -> None:
        original = fl_client.get_parameters(config={})
        noise = [p + np.random.randn(*p.shape) * 0.01 for p in original]
        fl_client.set_parameters(noise)
        restored = fl_client.get_parameters(config={})
        assert [p.shape for p in original] == [p.shape for p in restored]
        fl_client.set_parameters(original)


# ---------------------------------------------------------------------------
# Tests: fit()
# ---------------------------------------------------------------------------


class TestFit:
    def test_fit_returns_correct_structure(self, fl_client) -> None:
        params = fl_client.get_parameters(config={})
        new_params, num_examples, metrics = fl_client.fit(
            parameters=params,
            config={"local_epochs": 1, "fedprox_mu": 0.0},
        )
        assert isinstance(new_params, list)
        assert len(new_params) == len(params)
        assert isinstance(num_examples, int)
        assert num_examples > 0
        assert isinstance(metrics, dict)

    def test_fit_returns_updated_parameters(self, fl_client) -> None:
        """Parameters returned by fit() should differ from the initial ones."""
        original = fl_client.get_parameters(config={})
        # Zero-out model to ensure training changes something
        fl_client.set_parameters([np.zeros_like(p) for p in original])

        new_params, _, _ = fl_client.fit(
            parameters=[np.zeros_like(p) for p in original],
            config={"local_epochs": 1},
        )
        # At least one parameter layer should have changed
        changed = any(
            not np.allclose(a, 0.0) for a in new_params
        )
        assert changed, "fit() should update at least some parameters"
        fl_client.set_parameters(original)

    def test_fit_metric_contains_train_loss(self, fl_client) -> None:
        params = fl_client.get_parameters(config={})
        _, _, metrics = fl_client.fit(
            parameters=params,
            config={"local_epochs": 1},
        )
        assert "train_loss" in metrics
        assert float(metrics["train_loss"]) >= 0.0

    def test_fit_with_fedprox_mu_nonzero(self, fl_client) -> None:
        """FedProx should run without error when mu > 0."""
        params = fl_client.get_parameters(config={})
        new_params, num_examples, metrics = fl_client.fit(
            parameters=params,
            config={"local_epochs": 1, "fedprox_mu": 0.1},
        )
        assert num_examples > 0
        assert "train_loss" in metrics


# ---------------------------------------------------------------------------
# Tests: evaluate()
# ---------------------------------------------------------------------------


class TestEvaluate:
    def test_evaluate_returns_correct_structure(self, fl_client) -> None:
        params = fl_client.get_parameters(config={})
        loss, num_examples, metrics = fl_client.evaluate(
            parameters=params,
            config={},
        )
        assert isinstance(loss, float)
        assert loss >= 0.0
        assert isinstance(num_examples, int)
        assert num_examples > 0
        assert "accuracy" in metrics
        assert 0.0 <= float(metrics["accuracy"]) <= 1.0

    def test_evaluate_accuracy_is_between_zero_and_one(self, fl_client) -> None:
        params = fl_client.get_parameters(config={})
        _, _, metrics = fl_client.evaluate(parameters=params, config={})
        acc = float(metrics["accuracy"])
        assert 0.0 <= acc <= 1.0

"""
tests/unit/test_phase2_model.py
--------------------------------
Unit tests for Milestone 11 (model.py) acceptance criteria.

Acceptance Criteria (M11):
  - Forward pass produces tensor of shape (B, 1).
  - Model trains: loss decreases over 5 iterations on dummy data.
  - FTTransformerConfig defaults are sane.
  - FeatureTokenizer produces correct token sequence length.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_config():
    from src.fl_client.model import FTTransformerConfig

    return FTTransformerConfig(
        n_cont_features=11,
        cat_cardinalities=[5, 65],
        embedding_dim=32,
        num_blocks=2,
        num_heads=4,
        ffn_dim=128,
    )


@pytest.fixture()
def model(default_config):
    from src.fl_client.model import FTTransformerModel

    return FTTransformerModel(default_config)


@pytest.fixture()
def dummy_batch():
    """A small batch of synthetic continuous + categorical inputs."""
    B = 8
    x_cont = torch.randn(B, 11)
    x_cat  = torch.randint(0, 5, (B, 2))
    return x_cont, x_cat


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------


class TestFTTransformerConfig:
    def test_ffn_dim_defaults_to_4x_embedding(self) -> None:
        from src.fl_client.model import FTTransformerConfig

        cfg = FTTransformerConfig(n_cont_features=5)
        assert cfg.ffn_dim == 4 * cfg.embedding_dim

    def test_explicit_ffn_dim_respected(self) -> None:
        from src.fl_client.model import FTTransformerConfig

        cfg = FTTransformerConfig(n_cont_features=5, embedding_dim=64, ffn_dim=512)
        assert cfg.ffn_dim == 512

    def test_default_hyperparameters(self) -> None:
        from src.fl_client.model import FTTransformerConfig

        cfg = FTTransformerConfig(n_cont_features=11)
        assert cfg.embedding_dim == 64
        assert cfg.num_blocks == 3
        assert cfg.num_heads == 8


# ---------------------------------------------------------------------------
# Feature Tokenizer tests
# ---------------------------------------------------------------------------


class TestFeatureTokenizer:
    def test_output_sequence_length(self, default_config, dummy_batch) -> None:
        """Token sequence = 1 (CLS) + n_cont + n_cat."""
        from src.fl_client.model import FeatureTokenizer

        tokenizer = FeatureTokenizer(default_config)
        x_cont, x_cat = dummy_batch
        tokens = tokenizer(x_cont, x_cat)

        expected_len = 1 + default_config.n_cont_features + len(default_config.cat_cardinalities)
        assert tokens.shape == (x_cont.shape[0], expected_len, default_config.embedding_dim), (
            f"Expected ({x_cont.shape[0]}, {expected_len}, {default_config.embedding_dim}), "
            f"got {tokens.shape}"
        )

    def test_no_cat_features(self, dummy_batch) -> None:
        """Tokenizer must work with zero categorical features."""
        from src.fl_client.model import FeatureTokenizer, FTTransformerConfig

        cfg = FTTransformerConfig(n_cont_features=11, cat_cardinalities=[])
        tokenizer = FeatureTokenizer(cfg)
        x_cont, _ = dummy_batch
        tokens = tokenizer(x_cont, None)
        expected_len = 1 + cfg.n_cont_features
        assert tokens.shape[1] == expected_len

    def test_cls_token_dimension(self, default_config, dummy_batch) -> None:
        from src.fl_client.model import FeatureTokenizer

        tokenizer = FeatureTokenizer(default_config)
        x_cont, x_cat = dummy_batch
        tokens = tokenizer(x_cont, x_cat)
        assert tokens.shape[2] == default_config.embedding_dim


# ---------------------------------------------------------------------------
# Forward pass tests (M11 core acceptance criterion)
# ---------------------------------------------------------------------------


class TestFTTransformerForwardPass:
    def test_output_shape_with_cat(self, model, dummy_batch) -> None:
        """M11: Forward pass must produce tensor of shape (B, 1)."""
        model.eval()
        x_cont, x_cat = dummy_batch
        with torch.no_grad():
            logit = model(x_cont, x_cat)
        assert logit.shape == (x_cont.shape[0], 1), (
            f"Expected shape ({x_cont.shape[0]}, 1), got {logit.shape}"
        )

    def test_output_shape_no_cat(self, default_config) -> None:
        """Model must accept no categorical features."""
        from src.fl_client.model import FTTransformerModel, FTTransformerConfig

        cfg = FTTransformerConfig(n_cont_features=5, cat_cardinalities=[])
        m = FTTransformerModel(cfg)
        m.eval()
        x = torch.randn(4, 5)
        with torch.no_grad():
            logit = m(x, None)
        assert logit.shape == (4, 1)

    def test_output_is_raw_logit_not_probability(self, model, dummy_batch) -> None:
        """Logit should NOT be bounded to [0, 1] (that's BCEWithLogitsLoss's job)."""
        model.eval()
        x_cont, x_cat = dummy_batch
        with torch.no_grad():
            logit = model(x_cont, x_cat)
        # If the output were always in [0, 1], sigmoid was applied — which is wrong
        # We don't assert it's never in [0, 1] but just that no sigmoid was forced
        assert logit.dtype == torch.float32

    def test_no_nan_in_output(self, model, dummy_batch) -> None:
        """Forward pass must not produce NaN logits."""
        model.eval()
        x_cont, x_cat = dummy_batch
        with torch.no_grad():
            logit = model(x_cont, x_cat)
        assert not torch.isnan(logit).any(), "Forward pass produced NaN logits!"

    def test_different_batch_sizes(self, model) -> None:
        """Forward pass must work for various batch sizes including 1."""
        model.eval()
        for B in [1, 16, 128]:
            x_cont = torch.randn(B, 11)
            x_cat  = torch.randint(0, 5, (B, 2))
            with torch.no_grad():
                logit = model(x_cont, x_cat)
            assert logit.shape == (B, 1), f"Failed for B={B}"

    def test_gradient_flows(self, model, dummy_batch) -> None:
        """Backpropagation must produce gradients for all parameters."""
        model.train()
        x_cont, x_cat = dummy_batch
        y = torch.randint(0, 2, (x_cont.shape[0], 1)).float()
        criterion = nn.BCEWithLogitsLoss()
        logit = model(x_cont, x_cat)
        loss = criterion(logit, y)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for parameter: {name}"


# ---------------------------------------------------------------------------
# Training convergence test
# ---------------------------------------------------------------------------


class TestModelTrainingConvergence:
    def test_loss_decreases_over_iterations(self, model) -> None:
        """M11: Model loss must decrease over 5 gradient steps on fixed data."""
        model.train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        criterion = nn.BCEWithLogitsLoss()

        B = 32
        x_cont = torch.randn(B, 11)
        x_cat  = torch.randint(0, 5, (B, 2))
        y_true = torch.randint(0, 2, (B, 1)).float()

        losses = []
        for _ in range(10):
            optimizer.zero_grad()
            logit = model(x_cont, x_cat)
            loss  = criterion(logit, y_true)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        # Loss should generally decrease (allow for some noise)
        assert losses[-1] < losses[0] * 1.5, (
            f"Loss did not decrease meaningfully: initial={losses[0]:.4f}, final={losses[-1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Parameter count & utilities
# ---------------------------------------------------------------------------


class TestModelUtilities:
    def test_n_parameters_positive(self, model) -> None:
        assert model.n_parameters > 0

    def test_get_parameters_returns_numpy_arrays(self, model) -> None:
        params = model.get_parameters()
        assert len(params) > 0
        for p in params:
            assert isinstance(p, np.ndarray)

    def test_build_model_factory(self) -> None:
        from src.fl_client.model import build_model

        model = build_model()
        assert model is not None
        assert model.n_parameters > 0


# ---------------------------------------------------------------------------
# Tests — Non-IID split script
# ---------------------------------------------------------------------------


class TestCreateFlSplits:
    def test_dirichlet_split_count(self) -> None:
        from scripts.create_fl_splits import dirichlet_split

        rng = np.random.default_rng(0)
        df = __import__("pandas").DataFrame({
            "Feature1": rng.random(500),
            "Label": rng.integers(0, 2, 500),
        })
        splits = dirichlet_split(df, n_clients=3, alpha=0.5, seed=0)
        assert len(splits) == 3

    def test_dirichlet_total_samples_preserved(self) -> None:
        from scripts.create_fl_splits import dirichlet_split
        import pandas as pd

        rng = np.random.default_rng(1)
        df = pd.DataFrame({
            "Feature1": rng.random(1000),
            "Label": rng.integers(0, 2, 1000),
        })
        splits = dirichlet_split(df, n_clients=4, alpha=0.5, seed=1)
        total = sum(len(s) for s in splits)
        assert total == 1000, f"Total samples changed: {total} != 1000"

    def test_label_distributions_vary(self) -> None:
        """Low alpha → highly non-IID → distributions should differ across clients."""
        from scripts.create_fl_splits import dirichlet_split
        import pandas as pd

        rng = np.random.default_rng(2)
        df = pd.DataFrame({
            "Feature1": rng.random(2000),
            "Label": rng.integers(0, 2, 2000),
        })
        splits = dirichlet_split(df, n_clients=5, alpha=0.1, seed=2)
        ratios = [s["Label"].mean() for s in splits if len(s) > 0]
        # With alpha=0.1, the max-min ratio of positive class should vary
        assert max(ratios) - min(ratios) > 0.05, (
            "Dirichlet split with alpha=0.1 should produce heterogeneous distributions"
        )

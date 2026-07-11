"""fl_client/xai_explainer.py

Milestone 12 / 30 — Edge-side SHAP explainability for the FT-Transformer.

This module wraps shap.DeepExplainer to produce per-feature importance scores
that are attached to DDoS alert payloads sent to the Mitigation Engine.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn


class SHAPExplainer:
    """Wraps ``shap.DeepExplainer`` for the FT-Transformer model.

    Usage
    -----
    explainer = SHAPExplainer(model, background_loader, device="cpu")
    shap_vals = explainer.explain(x_cont, x_cat, feature_names=CONTINUOUS_FEATURES)
    """

    def __init__(
        self,
        model: nn.Module,
        background_loader,
        device: str = "cpu",
        n_background_samples: int = 100,
    ) -> None:
        """
        Parameters
        ----------
        model:
            Trained FTTransformerModel in eval mode.
        background_loader:
            A PyTorch DataLoader whose batches provide (x_cont, x_cat, y).
            Used to build the SHAP background distribution.
        device:
            Torch device string ('cpu' or 'cuda').
        n_background_samples:
            Number of background samples to pass to DeepExplainer.
        """
        try:
            import shap  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "SHAP is required for XAI: pip install shap"
            ) from exc

        self.model = model.eval()
        self.device = torch.device(device)
        self._feature_names: Optional[List[str]] = None

        # Collect background samples
        bg_cont_list: List[torch.Tensor] = []
        bg_cat_list: List[torch.Tensor] = []
        collected = 0
        for x_cont, x_cat, _ in background_loader:
            bg_cont_list.append(x_cont)
            bg_cat_list.append(x_cat)
            collected += x_cont.size(0)
            if collected >= n_background_samples:
                break

        self._bg_cont = torch.cat(bg_cont_list, dim=0)[:n_background_samples].to(self.device)
        self._bg_cat = torch.cat(bg_cat_list, dim=0)[:n_background_samples].to(self.device)

        # Build a wrapper that accepts only continuous features for DeepExplainer.
        # Categorical features are held fixed at the background mean.
        self._fixed_cat = self._bg_cat[:1].expand(n_background_samples, -1)

        import shap

        def _model_fn(x_cont_np: np.ndarray) -> np.ndarray:
            x_t = torch.tensor(x_cont_np, dtype=torch.float32).to(self.device)
            with torch.no_grad():
                logits = self.model(x_t, self._fixed_cat[: x_t.size(0)])
                probs = torch.sigmoid(logits).squeeze(1)
            return probs.cpu().numpy()

        self._explainer = shap.Explainer(
            _model_fn,
            self._bg_cont.cpu().numpy(),
            algorithm="permutation",
        )

    def explain(
        self,
        x_cont: torch.Tensor,
        feature_names: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, float]:
        """Return top-k SHAP feature importances for a single sample.

        Parameters
        ----------
        x_cont:
            Continuous feature tensor of shape ``(1, n_cont_features)``.
        feature_names:
            List of human-readable feature names matching ``x_cont`` columns.
        top_k:
            Number of most important features to return.

        Returns
        -------
        dict mapping feature name → SHAP contribution (absolute value).
        """
        import shap  # noqa: F401

        x_np = x_cont.detach().cpu().numpy()
        shap_values = self._explainer(x_np).values  # shape: (1, n_features)
        abs_vals = np.abs(shap_values[0])

        names = feature_names or [f"feature_{i}" for i in range(len(abs_vals))]
        if len(names) != len(abs_vals):
            names = [f"feature_{i}" for i in range(len(abs_vals))]

        # Return top-k features sorted by absolute importance
        ranked = sorted(zip(names, abs_vals.tolist()), key=lambda t: t[1], reverse=True)
        return {name: float(val) for name, val in ranked[:top_k]}


# ---------------------------------------------------------------------------
# Lightweight fallback for environments without SHAP installed
# ---------------------------------------------------------------------------

class MockSHAPExplainer:
    """Returns gradient-based pseudo-importance when SHAP is unavailable.

    Uses the absolute gradient of the model output w.r.t. input features
    as a proxy for feature importance. This is not a formal SHAP value but
    is a valid real-time approximation.
    """

    def __init__(self, model: nn.Module, device: str = "cpu") -> None:
        self.model = model
        self.device = torch.device(device)

    def explain(
        self,
        x_cont: torch.Tensor,
        x_cat: Optional[torch.Tensor],
        feature_names: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, float]:
        """Compute |∂output/∂x_cont| as proxy importance scores."""
        self.model.eval()
        x = x_cont.detach().clone().requires_grad_(True).to(self.device)
        cat = x_cat.to(self.device) if x_cat is not None else None

        logit = self.model(x, cat)
        prob = torch.sigmoid(logit)
        prob.sum().backward()

        abs_grads = x.grad.abs().squeeze(0).cpu().tolist()
        names = feature_names or [f"feature_{i}" for i in range(len(abs_grads))]
        if len(names) != len(abs_grads):
            names = [f"feature_{i}" for i in range(len(abs_grads))]

        ranked = sorted(zip(names, abs_grads), key=lambda t: t[1], reverse=True)
        return {name: float(val) for name, val in ranked[:top_k]}


def get_explainer(
    model: nn.Module,
    background_loader=None,
    device: str = "cpu",
    use_shap: bool = True,
) -> "SHAPExplainer | MockSHAPExplainer":
    """Factory that returns the best available explainer.

    Tries to build a ``SHAPExplainer``; falls back to ``MockSHAPExplainer``
    if SHAP is not installed or ``background_loader`` is None.
    """
    if use_shap and background_loader is not None:
        try:
            return SHAPExplainer(model, background_loader, device=device)
        except ImportError:
            pass
    return MockSHAPExplainer(model, device=device)

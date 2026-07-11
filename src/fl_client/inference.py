"""fl_client/inference.py

Milestone 30 — Active edge inference agent.

Processes network flow feature dictionaries through the FT-Transformer model,
generates SHAP-based explainability (or gradient-based fallback), and sends
DDoS alert payloads to the central Mitigation Engine API.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch

from fl_client.alert_sender import AlertSender
from fl_client.dataset import CONTINUOUS_FEATURES, CATEGORICAL_FEATURES, encode_categoricals
from fl_client.model import FTTransformerModel, build_model, FTTransformerConfig
from fl_client.xai_explainer import get_explainer


class InferenceAgent:
    """Runs FT-Transformer inference on live network flows and dispatches alerts.

    Parameters
    ----------
    client_id:
        UUID identifying this edge node in the FL system.
    alert_sender:
        Pre-configured :class:`AlertSender` instance.
    model:
        Optional pre-loaded FTTransformerModel. If None, a fresh model is built.
    model_path:
        Optional path to a ``.pt`` checkpoint file to load weights from.
    threshold:
        Sigmoid probability above which a flow is classified as DDoS.
    device:
        Torch device string ('cpu' or 'cuda').
    background_loader:
        DataLoader for SHAP background samples. If None, falls back to gradient-
        based pseudo-importance.
    """

    def __init__(
        self,
        client_id: uuid.UUID,
        alert_sender: AlertSender,
        model: Optional[FTTransformerModel] = None,
        model_path: Optional[Path] = None,
        threshold: float = 0.85,
        device: str = "cpu",
        background_loader=None,
    ) -> None:
        self.client_id = client_id
        self.alert_sender = alert_sender
        self.threshold = threshold
        self.device = torch.device(device)

        # Build / load model
        if model is not None:
            self.model = model.to(self.device)
        else:
            self.model = build_model().to(self.device)

        if model_path is not None and Path(model_path).exists():
            state = torch.load(model_path, map_location=self.device, weights_only=False)
            if isinstance(state, list):
                # Flower saves a list of numpy arrays
                for param, arr in zip(self.model.parameters(), state):
                    param.data = torch.tensor(arr, dtype=param.dtype).to(self.device)
            elif isinstance(state, dict):
                self.model.load_state_dict(state, strict=False)

        self.model.eval()

        # Build explainer (SHAP if background_loader provided, else gradient proxy)
        self.explainer = get_explainer(
            model=self.model,
            background_loader=background_loader,
            device=device,
            use_shap=(background_loader is not None),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_flow(
        self,
        src_ip: str,
        flow_features: Dict[str, float],
        dst_ip: Optional[str] = None,
    ) -> Optional[Dict]:
        """Run inference on a single network flow feature dict.

        Parameters
        ----------
        src_ip:
            Source IP address of the flow (used in the alert payload).
        flow_features:
            Dict mapping CICFlowMeter column names to numeric values.
            At minimum must contain the keys in ``CONTINUOUS_FEATURES``.
        dst_ip:
            Optional destination IP for the alert payload.

        Returns
        -------
        The alert payload dict if an alert was sent, else ``None``.
        """
        x_cont, x_cat = self._prepare_tensors(flow_features)

        # --- Inference ---
        with torch.no_grad():
            logit = self.model(x_cont, x_cat)
            prob = float(torch.sigmoid(logit).squeeze())

        if prob < self.threshold:
            return None  # Benign flow — no alert

        # --- Explainability ---
        shap_values = self._explain(x_cont, x_cat)

        # --- Alert ---
        sent = await self.alert_sender.send_alert(
            client_id=self.client_id,
            src_ip=src_ip,
            prob=prob,
            shap_values=shap_values,
        )

        if sent:
            return {
                "src_ip": src_ip,
                "probability": prob,
                "shap_values": shap_values,
                "alert_sent": True,
            }
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prepare_tensors(
        self, flow_features: Dict[str, float]
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Convert a raw feature dict into model-ready tensors."""
        import pandas as pd
        from fl_client.dataset import load_scaler

        # Build single-row DataFrame
        row: Dict = {}
        for col in CONTINUOUS_FEATURES:
            row[col] = flow_features.get(col, 0.0)
        for col in CATEGORICAL_FEATURES:
            row[col] = flow_features.get(col, 0)
        row["Label"] = 0  # Placeholder

        df = pd.DataFrame([row])
        df = encode_categoricals(df)

        cont_vals = df[CONTINUOUS_FEATURES].values.astype(np.float32)
        cat_vals = df[CATEGORICAL_FEATURES].values.astype(np.int64)

        x_cont = torch.tensor(cont_vals, dtype=torch.float32).to(self.device)
        x_cat = torch.tensor(cat_vals, dtype=torch.long).to(self.device)
        return x_cont, x_cat

    def _explain(
        self,
        x_cont: torch.Tensor,
        x_cat: torch.Tensor,
    ) -> Dict[str, float]:
        """Generate feature importance scores using the configured explainer."""
        from fl_client.xai_explainer import SHAPExplainer, MockSHAPExplainer

        if isinstance(self.explainer, SHAPExplainer):
            return self.explainer.explain(x_cont, feature_names=CONTINUOUS_FEATURES)
        else:
            # MockSHAPExplainer (gradient-based)
            return self.explainer.explain(
                x_cont, x_cat, feature_names=CONTINUOUS_FEATURES
            )


# ---------------------------------------------------------------------------
# CLI entry-point for manual testing
# ---------------------------------------------------------------------------

async def _demo() -> None:
    """Simulate a single anomalous flow through the full pipeline."""
    client_id = uuid.uuid4()
    sender = AlertSender(api_url="http://localhost:8000")
    agent = InferenceAgent(client_id=client_id, alert_sender=sender)

    anomalous_flow = {
        "Flow Duration": 0.5,
        "Total Fwd Packets": 8000,
        "Total Bwd Packets": 2,
        "Fwd Packet Length Max": 60.0,
        "Fwd Packet Length Min": 40.0,
        "Fwd Packet Length Mean": 52.0,
        "Flow Bytes/s": 500000.0,
        "Flow Packets/s": 16000.0,
        "Init_Win_bytes_forward": 64240,
        "Active Mean": 0.0,
        "Idle Mean": 0.0,
        "Protocol": 6,   # TCP
        "TCP Flags": 2,  # SYN
    }

    print("[InferenceAgent] Processing anomalous flow ...")
    result = await agent.process_flow(
        src_ip="192.168.1.100",
        flow_features=anomalous_flow,
        dst_ip="10.0.0.1",
    )
    if result:
        print(f"[InferenceAgent] Alert sent: {result}")
    else:
        print("[InferenceAgent] Flow classified as benign (below threshold).")


if __name__ == "__main__":
    asyncio.run(_demo())

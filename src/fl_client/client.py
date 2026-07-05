"""fl_client/client.py"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from flwr.client import NumPyClient

from src.fl_client.dataset import (
    NetworkFlowDataset,
    build_dataloaders,
    load_scaler,
)
from src.fl_client.model import FTTransformerConfig, FTTransformerModel, build_model


class DDosFlowerClient(NumPyClient):
    """Flower NumPyClient wrapping the FT-Transformer (Milestones 14 & 16).

    Supports:
    - Standard local training (FedAvg) via ``fit()``.
    - FedProx proximal regularisation when ``config["fedprox_mu"] > 0``.
    - Local evaluation via ``evaluate()``.
    """

    def __init__(
        self,
        client_id: str,
        data_path: Path,
        model_config: Optional[FTTransformerConfig] = None,
        scaler_path: Optional[Path] = None,
        device: str = "cpu",
        batch_size: int = 256,
        lr: float = 3e-4,
    ) -> None:
        self.client_id = client_id
        self.data_path = Path(data_path)
        self.device = torch.device(device)
        self.batch_size = batch_size
        self.lr = lr

        # Load optional scaler
        scaler = load_scaler(scaler_path) if scaler_path else None
        fit_new = scaler is None

        # Build data loaders
        self.train_loader, self.val_loader, self.scaler = build_dataloaders(
            csv_path=self.data_path,
            scaler=scaler,
            batch_size=self.batch_size,
            fit_new_scaler=fit_new,
            use_weighted_sampler=True,
        )

        # Build model
        self.model: nn.Module = build_model(model_config).to(self.device)
        self.criterion = nn.BCEWithLogitsLoss()
        self._dp_engine = None

    # ------------------------------------------------------------------
    # Flower NumPyClient interface
    # ------------------------------------------------------------------

    def get_parameters(self, config: Dict) -> List[np.ndarray]:
        """Return model parameters as a list of numpy arrays."""
        return [p.detach().cpu().numpy() for p in self.model.parameters()]

    def set_parameters(self, parameters: List[np.ndarray]) -> None:
        """Load parameters from a list of numpy arrays into the model."""
        for param, arr in zip(self.model.parameters(), parameters):
            param.data = torch.tensor(arr, dtype=param.dtype).to(self.device)

    def fit(
        self,
        parameters: List[np.ndarray],
        config: Dict,
    ) -> Tuple[List[np.ndarray], int, Dict]:
        """Train the model locally for one FL round.

        Config keys
        -----------
        local_epochs : int   Number of local training epochs (default 1).
        learning_rate: float Override default LR.
        fedprox_mu   : float FedProx proximal coefficient (0 → plain FedAvg).
        dp_enabled   : bool  Whether to use Opacus DP-SGD.
        """
        self.set_parameters(parameters)

        local_epochs: int = int(config.get("local_epochs", 1))
        lr: float = float(config.get("learning_rate", self.lr))
        mu: float = float(config.get("fedprox_mu", 0.0))
        dp_enabled: bool = bool(config.get("dp_enabled", False))

        # 1. DP prep: fix LayerNorms if using DP for the first time
        if dp_enabled and not hasattr(self.model, "_is_dp_fixed"):
            from opacus.validators import ModuleValidator
            if not ModuleValidator.is_valid(self.model):
                self.model = ModuleValidator.fix(self.model).to(self.device)
            self.model._is_dp_fixed = True

        optimizer = AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)

        # 2. DP Engine attach (we do this once)
        if dp_enabled and self._dp_engine is None:
            from opacus import PrivacyEngine
            self._dp_engine = PrivacyEngine()
            
            # make_private modifies model, optimizer, train_loader in-place
            self.model, optimizer, self.train_loader = self._dp_engine.make_private(
                module=self.model,
                optimizer=optimizer,
                data_loader=self.train_loader,
                noise_multiplier=float(config.get("dp_noise_multiplier", 1.0)),
                max_grad_norm=float(config.get("dp_max_grad_norm", 1.0)),
            )

        # Keep a copy of the global parameters for the FedProx proximal term
        global_params: Optional[List[torch.Tensor]] = None
        if mu > 0.0:
            global_params = [
                p.detach().clone() for p in self.model.parameters()
            ]

        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for _ in range(local_epochs):
            for x_cont, x_cat, y in self.train_loader:
                x_cont = x_cont.to(self.device)
                x_cat = x_cat.to(self.device)
                y = y.to(self.device)

                optimizer.zero_grad()
                logits = self.model(x_cont, x_cat).squeeze(1)
                loss = self.criterion(logits, y)

                # FedProx proximal term: (mu/2) * ||w - w_global||^2
                if mu > 0.0 and global_params is not None:
                    prox = sum(
                        ((p - g) ** 2).sum()
                        for p, g in zip(self.model.parameters(), global_params)
                    )
                    loss = loss + (mu / 2.0) * prox

                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()

                total_loss += loss.item()
                n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        num_examples = len(self.train_loader.dataset)
        
        metrics = {"train_loss": float(avg_loss)}
        if dp_enabled and self._dp_engine is not None:
            epsilon = self._dp_engine.get_epsilon(float(config.get("dp_target_delta", 1e-5)))
            metrics["dp_epsilon"] = float(epsilon)

        return (
            self.get_parameters(config={}),
            num_examples,
            metrics,
        )

    def evaluate(
        self,
        parameters: List[np.ndarray],
        config: Dict,
    ) -> Tuple[float, int, Dict]:
        """Evaluate the model on the local validation split."""
        self.set_parameters(parameters)
        self.model.eval()

        total_loss = 0.0
        correct = 0
        n_samples = 0

        with torch.no_grad():
            for x_cont, x_cat, y in self.val_loader:
                x_cont = x_cont.to(self.device)
                x_cat = x_cat.to(self.device)
                y = y.to(self.device)

                logits = self.model(x_cont, x_cat).squeeze(1)
                loss = self.criterion(logits, y)
                total_loss += loss.item() * len(y)

                preds = (torch.sigmoid(logits) >= 0.5).float()
                correct += (preds == y).sum().item()
                n_samples += len(y)

        avg_loss = total_loss / max(n_samples, 1)
        accuracy = correct / max(n_samples, 1)

        return (
            float(avg_loss),
            n_samples,
            {"accuracy": float(accuracy)},
        )

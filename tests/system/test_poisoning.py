"""
tests/system/test_poisoning.py
------------------------------
System test for Poisoning Attack Simulation (Milestone 45).

Simulates a malicious client that sends corrupted (inverse/noisy) gradients
and verifies that the Adaptive Trust Manager isolates the client by dropping
its trust score, thus preventing the global model from significant degradation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import numpy as np
import pandas as pd
import flwr as flw
from flwr.common import Context

try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

from src.fl_client.client import DDosFlowerClient
from src.fl_client.dataset import CONTINUOUS_FEATURES, TARGET_COLUMN
from src.fl_client.model import FTTransformerConfig
from src.fl_server.strategy import AdaptiveTrustStrategy
from src.fl_server.trust_manager import TrustManager


def _small_config() -> FTTransformerConfig:
    return FTTransformerConfig(
        n_cont_features=len(CONTINUOUS_FEATURES),
        cat_cardinalities=[5, 65],
        embedding_dim=16,
        num_blocks=1,
        num_heads=2,
        ffn_dim=32,
    )


def _make_csv(n_rows: int = 150, seed: int = 0) -> Path:
    rng = np.random.default_rng(seed)
    data = {col: rng.uniform(0, 500, n_rows).astype(np.float32) for col in CONTINUOUS_FEATURES}
    data["Protocol"] = rng.choice([1, 2, 6, 17], n_rows)
    data["TCP Flags"] = rng.integers(0, 63, n_rows)
    data[TARGET_COLUMN] = rng.choice([0, 1], n_rows).astype(np.float32)
    df = pd.DataFrame(data)
    f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    df.to_csv(f.name, index=False)
    f.close()
    return Path(f.name)


class MaliciousDDosFlowerClient(DDosFlowerClient):
    """A malicious client that sends inverted model parameters."""
    
    def fit(self, parameters: List[np.ndarray], config: Dict) -> Tuple[List[np.ndarray], int, Dict]:
        # Perform normal training
        updated_params, num_examples, metrics = super().fit(parameters, config)
        
        # Corrupt the parameters by inverting the updates (sending negative of current params)
        corrupted_params = [-1.0 * p for p in updated_params]
        
        return corrupted_params, num_examples, metrics


_CSV_PATHS: List[Path] = []


def client_fn(context: Context) -> flw.client.Client:
    """Factory called by Flower simulation.
    Makes the client with ID '1' a malicious client.
    """
    cid = context.node_config.get("partition-id", "0")
    csv_path = _CSV_PATHS[int(cid) % len(_CSV_PATHS)]
    
    if str(cid) == "1":
        # Malicious client
        client = MaliciousDDosFlowerClient(
            client_id=str(cid),
            data_path=csv_path,
            model_config=_small_config(),
            device="cpu",
        )
    else:
        # Benign client
        client = DDosFlowerClient(
            client_id=str(cid),
            data_path=csv_path,
            model_config=_small_config(),
            device="cpu",
        )
    return client.to_client()


@pytest.fixture(scope="module", autouse=True)
def setup_csv_paths():
    global _CSV_PATHS
    _CSV_PATHS = [_make_csv(n_rows=200, seed=i) for i in range(2)]
    yield
    for p in _CSV_PATHS:
        p.unlink(missing_ok=True)


@pytest.mark.system
@pytest.mark.skipif(not HAS_RAY, reason="ray is required for flwr.simulation")
class TestPoisoningAttack:
    
    def test_trust_manager_isolates_malicious_client(self):
        """Run simulation with 1 benign and 1 malicious client."""
        tm = TrustManager(
            penalty_threshold=0.5,
            auto_ban_threshold=0.1,
        )

        def on_fit_config(server_round: int) -> Dict:
            return {"local_epochs": 1, "learning_rate": 3e-4}

        strategy = AdaptiveTrustStrategy(
            trust_manager=tm,
            fraction_fit=1.0,
            fraction_evaluate=1.0,
            min_fit_clients=2,
            min_evaluate_clients=2,
            min_available_clients=2,
            on_fit_config_fn=on_fit_config,
        )

        history = flw.simulation.start_simulation(
            client_fn=client_fn,
            num_clients=2,
            config=flw.server.ServerConfig(num_rounds=3),
            strategy=strategy,
            client_resources={"num_cpus": 1, "num_gpus": 0.0},
        )
        
        # Verify the trust manager has assigned a low score to the malicious client (cid 1)
        scores = tm.get_all_scores()
        
        benign_score = scores.get("0", 1.0)
        malicious_score = scores.get("1", 1.0)
        
        assert malicious_score < 0.5, f"Malicious client trust score should be low, got {malicious_score}"
        assert benign_score > malicious_score, "Benign client should have higher trust than malicious client"

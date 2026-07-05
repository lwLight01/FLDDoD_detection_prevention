"""
tests/unit/test_phase3_dp_client.py
------------------------------------
Unit tests for Differential Privacy (Milestone 19).

Tests:
  - Client handles DP config and wraps model correctly.
  - Metrics returned by fit() include dp_epsilon.
"""

import pytest
import numpy as np
from src.fl_client.client import DDosFlowerClient
from src.fl_client.model import FTTransformerConfig

@pytest.fixture
def dp_client(tmp_path):
    # Create a small synthetic dataset for testing
    csv_path = tmp_path / "data.csv"
    import pandas as pd
    from src.fl_client.dataset import CONTINUOUS_FEATURES, TARGET_COLUMN
    
    data = {col: np.random.uniform(0, 100, 50).astype(np.float32) for col in CONTINUOUS_FEATURES}
    data["Protocol"] = np.random.choice([1, 2, 6], 50)
    data["TCP Flags"] = np.random.randint(0, 63, 50)
    data[TARGET_COLUMN] = np.random.choice([0, 1], 50).astype(np.float32)
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    config = FTTransformerConfig(
        n_cont_features=len(CONTINUOUS_FEATURES),
        cat_cardinalities=[5, 65],
        embedding_dim=8,
        num_blocks=1,
        num_heads=1,
        ffn_dim=16,
    )
    
    client = DDosFlowerClient(
        client_id="dp_test_client",
        data_path=csv_path,
        model_config=config,
        device="cpu",
    )
    return client

def test_dp_sgd_fit(dp_client, mocker):
    """Test that fit() executes successfully when DP is enabled."""
    
    import torch
    import torch.nn as nn
    
    # Opacus has limited support for custom nn.Parameter usage (like in FeatureTokenizer).
    # To test the client's DP wrapper logic, we use a simple Opacus-compatible model.
    class MockModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(13, 1) # 11 cont + 2 cat = 13 features
            
        def forward(self, x_cont, x_cat=None):
            if x_cat is not None:
                x = torch.cat([x_cont, x_cat.float()], dim=1)
            else:
                x = x_cont
            return self.linear(x)
            
    dp_client.model = MockModel()
    
    # Get mock parameters
    params = [p.detach().numpy() for p in dp_client.model.parameters()]
    
    config = {
        "local_epochs": 1,
        "dp_enabled": True,
        "dp_noise_multiplier": 0.5,
        "dp_max_grad_norm": 1.0,
        "dp_target_delta": 1e-4,
    }
    
    new_params, num_examples, metrics = dp_client.fit(parameters=params, config=config)
    
    # Assert successful run
    assert num_examples > 0
    assert "train_loss" in metrics
    # Assert DP epsilon was calculated and returned
    assert "dp_epsilon" in metrics
    assert metrics["dp_epsilon"] > 0.0
    
    # Assert model was wrapped
    assert dp_client._dp_engine is not None

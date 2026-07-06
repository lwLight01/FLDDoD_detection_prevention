import sys
import torch
import numpy as np
import shap

from src.fl_client.dataset import build_dataloaders
from src.fl_client.model import build_model

# Just a quick dummy test to see expected_value type
model = build_model()
dummy_cont = torch.randn(10, 11)
explainer = shap.DeepExplainer(model, dummy_cont)
val = explainer.expected_value
print(f"expected_value type: {type(val)}")
if isinstance(val, (list, np.ndarray, torch.Tensor)):
    print(f"expected_value shape/len: {len(val) if isinstance(val, list) else val.shape}")

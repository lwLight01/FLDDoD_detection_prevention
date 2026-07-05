"""fl_server/dp_manager.py"""

from typing import Dict
from flwr.common import Scalar

class DPManager:
    """Manages Differential Privacy configuration for FL clients (Milestone 19).
    
    Provides the necessary configuration parameters to the clients during the
    `on_fit_config_fn` so they can initialize Opacus PrivacyEngine.
    """

    def __init__(
        self,
        dp_enabled: bool = True,
        target_epsilon: float = 3.0,
        target_delta: float = 1e-5,
        max_grad_norm: float = 1.0,
        noise_multiplier: float = 1.0,
    ) -> None:
        self.dp_enabled = dp_enabled
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.max_grad_norm = max_grad_norm
        self.noise_multiplier = noise_multiplier

    def get_fit_config(self) -> Dict[str, Scalar]:
        """Returns DP parameters to be merged into the client's fit config."""
        return {
            "dp_enabled": self.dp_enabled,
            "dp_target_epsilon": self.target_epsilon,
            "dp_target_delta": self.target_delta,
            "dp_max_grad_norm": self.max_grad_norm,
            "dp_noise_multiplier": self.noise_multiplier,
        }

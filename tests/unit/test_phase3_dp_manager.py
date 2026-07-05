"""
tests/unit/test_phase3_dp_manager.py
------------------------------------
Unit tests for DPManager (Milestone 19).

Tests:
  - DPManager initializes with correct default values.
  - get_fit_config returns the expected dictionary format.
"""

from src.fl_server.dp_manager import DPManager


def test_dp_manager_initialization():
    manager = DPManager(
        dp_enabled=True,
        target_epsilon=5.0,
        target_delta=1e-4,
        max_grad_norm=2.0,
        noise_multiplier=0.5,
    )
    assert manager.dp_enabled is True
    assert manager.target_epsilon == 5.0
    assert manager.target_delta == 1e-4
    assert manager.max_grad_norm == 2.0
    assert manager.noise_multiplier == 0.5


def test_get_fit_config():
    manager = DPManager(
        dp_enabled=True,
        target_epsilon=2.5,
        target_delta=1e-5,
        max_grad_norm=1.5,
        noise_multiplier=1.2,
    )
    config = manager.get_fit_config()
    assert config["dp_enabled"] is True
    assert config["dp_target_epsilon"] == 2.5
    assert config["dp_target_delta"] == 1e-5
    assert config["dp_max_grad_norm"] == 1.5
    assert config["dp_noise_multiplier"] == 1.2

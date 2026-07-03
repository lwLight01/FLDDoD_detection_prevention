"""
tests/unit/test_configs.py
---------------------------
Unit tests for all service configuration modules.

Acceptance Criteria (Milestone 1):
  - Configuration classes are importable with default values.
  - Default values match documented specifications.
  - Settings correctly read from environment overrides.
"""


class TestFLServerConfig:
    def test_default_values_match_spec(self):
        from fl_server.config import FLServerConfig

        cfg = FLServerConfig()
        # Ref: docs/FederatedLearning.md § 6
        assert cfg.fl_num_rounds == 100
        assert cfg.fl_min_fit_clients == 10
        assert cfg.fl_min_available_clients == 15
        assert cfg.fl_fraction_fit == 0.5
        assert cfg.fl_trust_penalty_threshold == 0.7

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("FL_NUM_ROUNDS", "50")
        from fl_server.config import FLServerConfig

        cfg = FLServerConfig()
        assert cfg.fl_num_rounds == 50


class TestMitigationEngineConfig:
    def test_default_risk_weights_sum_to_one(self):
        from mitigation_engine.config import MitigationEngineConfig

        cfg = MitigationEngineConfig()
        total = (
            cfg.risk_score_weight_prob + cfg.risk_score_weight_freq + cfg.risk_score_weight_decay
        )
        assert abs(total - 1.0) < 1e-9, f"Risk weights must sum to 1.0, got {total}"

    def test_default_threshold_values(self):
        from mitigation_engine.config import MitigationEngineConfig

        cfg = MitigationEngineConfig()
        # Ref: docs/Mitigation.md § 3
        assert cfg.risk_stage1_threshold == 50.0
        assert cfg.risk_stage2_threshold == 70.0
        assert cfg.risk_stage3_threshold == 90.0
        # Ref: docs/FTTransformer.md § 4
        assert cfg.alert_probability_threshold == 0.85

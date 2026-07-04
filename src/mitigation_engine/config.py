"""mitigation_engine/config.py"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class MitigationEngineConfig(BaseSettings):
    """Mitigation Engine runtime settings."""

    # --- Database ---
    database_url: str = "postgresql://ddos_user:password@db:5432/ddos_db"

    # --- Authentication ---
    jwt_secret_key: str = "insecure-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # --- Service Dependencies ---
    ryu_rest_api_url: str = "http://ryu_controller:8080"
    flower_server_url: str = "fl_server:8080"

    # --- Inference Thresholds ---
    alert_probability_threshold: float = 0.85

    # --- Risk Scoring Weights (ref: docs/Mitigation.md § 2.1) ---
    risk_score_weight_prob: float = 0.6
    risk_score_weight_freq: float = 0.3
    risk_score_weight_decay: float = 0.1

    # --- Risk Score Stage Thresholds ---
    risk_stage1_threshold: float = 50.0  # RATE_LIMIT
    risk_stage2_threshold: float = 70.0  # ISOLATE
    risk_stage3_threshold: float = 90.0  # (Summary comment)
    default_mitigation_ttl_seconds: int = 3600

    # --- Logging ---
    log_level: str = "INFO"

    # --- CORS (for dashboard dev server) ---
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Module-level singleton
settings = MitigationEngineConfig()

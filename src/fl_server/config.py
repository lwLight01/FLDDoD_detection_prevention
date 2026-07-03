"""
fl_server/config.py
-------------------
Server-side configuration loaded from environment variables.
All values have documented defaults — override via .env or Docker environment.

Ref: docs/FederatedLearning.md § 6 (Client Failure & Dropouts)
     docs/Deployment.md § 7 (Environment Variables)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class FLServerConfig(BaseSettings):
    """
    Federated Learning Server runtime configuration.
    Values are read from environment variables (case-insensitive).
    """

    # --- Federated Learning Rounds ---
    fl_num_rounds: int = 100
    fl_min_fit_clients: int = 10
    fl_min_available_clients: int = 15
    fl_fraction_fit: float = 0.5

    # --- Trust Scoring ---
    # Cosine similarity below this threshold triggers a trust penalty.
    fl_trust_penalty_threshold: float = 0.7
    # A client whose trust score drops below this is auto-banned.
    fl_auto_ban_threshold: float = 0.1

    # --- Server Address ---
    fl_server_host: str = "0.0.0.0"
    fl_server_port: int = 8080

    # --- Checkpoint Storage ---
    checkpoint_dir: str = "checkpoints"

    # --- Database (for logging round metrics) ---
    database_url: str = "postgresql://ddos_user:password@db:5432/ddos_db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Module-level singleton — import this in main.py and strategy.py
settings = FLServerConfig()

"""fl_server/config.py"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class FLServerConfig(BaseSettings):
    """Federated Learning Server runtime configuration."""

    # --- Federated Learning Rounds ---
    fl_num_rounds: int = 100
    fl_min_fit_clients: int = 10
    fl_min_available_clients: int = 15
    fl_fraction_fit: float = 0.5

    # (Summary comment)
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

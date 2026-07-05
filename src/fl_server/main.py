"""fl_server/main.py"""

from __future__ import annotations

import os
import argparse
import sys

import flwr as flwr_lib

from src.fl_server.config import settings
from src.fl_server.strategy import AdaptiveTrustStrategy
from src.fl_server.trust_manager import TrustManager
from src.fl_server.dp_manager import DPManager


def build_strategy() -> AdaptiveTrustStrategy:
    """Construct the AdaptiveTrustStrategy with values from settings."""
    trust_manager = TrustManager(
        penalty_threshold=settings.fl_trust_penalty_threshold,
        auto_ban_threshold=settings.fl_auto_ban_threshold,
    )
    # Instantiate DPManager (Milestone 19)
    dp_manager = DPManager(
        dp_enabled=True,
        target_epsilon=3.0,
        target_delta=1e-5,
        max_grad_norm=1.0,
        noise_multiplier=1.0,
    )
    return AdaptiveTrustStrategy(
        trust_manager=trust_manager,
        dp_manager=dp_manager,
        fraction_fit=settings.fl_fraction_fit,
        min_fit_clients=settings.fl_min_fit_clients,
        min_available_clients=settings.fl_min_available_clients,
    )


def main() -> None:
    """Start the Flower FL aggregation server (Milestone 13)."""
    parser = argparse.ArgumentParser(description="Flower FL Server")
    parser.add_argument(
        "--rounds",
        type=int,
        default=settings.fl_num_rounds,
        help="Number of FL rounds to run.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.fl_server_host,
        help="Server bind host.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.fl_server_port,
        help="Server gRPC port.",
    )
    args = parser.parse_args()

    server_address = f"{args.host}:{args.port}"
    strategy = build_strategy()

    # Milestone 22: Configure mTLS if certificates are present
    certificates = None
    cert_dir = os.environ.get("CERTS_DIR", "certs")
    if os.path.exists(os.path.join(cert_dir, "ca.crt")):
        print("[FL Server] Loading mTLS certificates...")
        with open(os.path.join(cert_dir, "ca.crt"), "rb") as f:
            ca_cert = f.read()
        with open(os.path.join(cert_dir, "server.crt"), "rb") as f:
            server_cert = f.read()
        with open(os.path.join(cert_dir, "server.key"), "rb") as f:
            server_key = f.read()
            
        certificates = (
            ca_cert,
            server_cert,
            server_key
        )

    print(f"[FL Server] Starting on {server_address} for {args.rounds} rounds.")

    flwr_lib.server.start_server(
        server_address=server_address,
        config=flwr_lib.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
        certificates=certificates,
    )

    print("[FL Server] Training complete.")


if __name__ == "__main__":
    main()

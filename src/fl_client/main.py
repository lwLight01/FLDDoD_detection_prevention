"""fl_client/main.py"""

import os
import argparse
import flwr as flwr_lib

from src.fl_client.client import DDosFlowerClient


def main() -> None:
    """Start the Flower FL edge client (Milestone 14, 21, 22)."""
    parser = argparse.ArgumentParser(description="Flower FL Client")
    parser.add_argument(
        "--client-id",
        type=str,
        default=os.environ.get("CLIENT_ID", "client_0"),
        help="Unique ID for this client.",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=os.environ.get("DATA_PATH", "data/client_0.csv"),
        help="Path to the client's local data partition.",
    )
    parser.add_argument(
        "--scaler-path",
        type=str,
        default=os.environ.get("SCALER_PATH", "data/quantile_scaler.pkl"),
        help="Path to the quantile scaler.",
    )
    parser.add_argument(
        "--server-address",
        type=str,
        default=os.environ.get("SERVER_ADDRESS", "127.0.0.1:8080"),
        help="Address of the FL server.",
    )
    args = parser.parse_args()

    # Milestone 22: Configure mTLS if certificates are present
    root_certificates = None
    cert_dir = os.environ.get("CERTS_DIR", "certs")
    if os.path.exists(os.path.join(cert_dir, "ca.crt")):
        print(f"[FL Client {args.client_id}] Loading mTLS certificates...")
        with open(os.path.join(cert_dir, "ca.crt"), "rb") as f:
            root_certificates = f.read()

    print(f"[FL Client {args.client_id}] Starting client, connecting to {args.server_address}")

    client = DDosFlowerClient(
        client_id=args.client_id,
        data_path=args.data_path,
        scaler_path=args.scaler_path if os.path.exists(args.scaler_path) else None,
        device="cpu", # Assume CPU for edge devices in simulation
    )

    flwr_lib.client.start_client(
        server_address=args.server_address,
        client=client,
        root_certificates=root_certificates,
    )


if __name__ == "__main__":
    main()

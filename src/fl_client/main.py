"""
fl_client/main.py
-----------------
Entry point for the Flower FL edge client.

Responsibilities:
  - Load local data partition
  - Instantiate FTTransformerModel
  - Instantiate DDosFlowerClient
  - Connect to FL server via gRPC (with mTLS)
  - Start the Flower training/evaluation loop

Implementation deferred to Milestone 14.

Ref: docs/FederatedLearning.md § 1.2
     docs/DevelopmentRoadmap.md — Milestone 14
"""

# TODO (Milestone 14): Implement main() with flwr.client.start_numpy_client()
# TODO (Milestone 22): Add mTLS certificates to gRPC channel


def main() -> None:
    """Start the Flower FL edge client. Implemented in Milestone 14."""
    raise NotImplementedError("fl_client.main is scaffolded. Implement in Milestone 14.")


if __name__ == "__main__":
    main()

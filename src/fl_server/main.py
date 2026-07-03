"""
fl_server/main.py
-----------------
Entry point for the Flower Federated Learning Server.

Responsibilities:
  - Initialise and start the gRPC Flower server
  - Apply the custom AdaptiveTrustStrategy
  - Log startup/shutdown to structured logger

Implementation will be completed in Milestone 13.
This stub ensures the module is importable and the package structure is valid.

Ref: docs/FederatedLearning.md § 1.1
     docs/DevelopmentRoadmap.md — Milestone 13
"""

# TODO (Milestone 13): Import and start flwr.server with AdaptiveTrustStrategy
# TODO (Milestone 13): Configure mTLS certificates for gRPC channel security
# TODO (Milestone 22): Enforce SecAgg via Flower SecAgg+ plugin


def main() -> None:
    """Start the Flower FL aggregation server. Implemented in Milestone 13."""
    raise NotImplementedError(
        "fl_server.main is scaffolded. Implement in Milestone 13."
    )


if __name__ == "__main__":
    main()

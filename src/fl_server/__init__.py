"""
fl_server/__init__.py
---------------------
Flower Federated Learning Aggregation Server package.
Responsible for:
  - Coordinating federated training rounds via gRPC
  - Adaptive Trust Scoring (cosine-similarity-based aggregation)
  - Global model checkpointing and version tagging
  - Logging round metrics to PostgreSQL

Ref: docs/FederatedLearning.md
"""

"""
fl_client/dataset.py
--------------------
PyTorch Dataset and DataLoader for tabular network flow data.

Responsibilities:
  - Load a local CSV partition (Non-IID split) into a PyTorch Dataset.
  - Apply preprocessing transformations consistently with the global
    normalization parameters (frozen QuantileTransformer state from the
    centralized training phase).
  - Handle class imbalance via WeightedRandomSampler.

Data Schema (CIC-DDoS2019 features, ref: docs/FTTransformer.md § 1.1):
  Continuous: Flow Duration, Total Fwd Packets, Total Bwd Packets,
              Fwd Packet Length Max/Min/Mean, Flow Bytes/s, Flow Packets/s,
              Init_Win_bytes_forward, Active Mean, Idle Mean
  Categorical: Protocol, TCP Flags (encoded as ordinal)
  Target:     Label (0=Benign, 1=DDoS)

Implementation deferred to Milestone 8.

Ref: docs/FTTransformer.md § 1, docs/DevelopmentRoadmap.md — Milestone 8
"""

# TODO (Milestone 8): Implement NetworkFlowDataset(torch.utils.data.Dataset)
# TODO (Milestone 8): Implement build_dataloaders(csv_path, config) -> (train, val)
# TODO (Milestone 9): Integrate non-IID split loading logic

"""
sdn_controller/flow_extractor.py
----------------------------------
Parses raw OpenFlow FlowStats messages from Ryu into tabular feature rows
matching the FT-Transformer input schema (docs/FTTransformer.md § 1.1).

Output: pandas DataFrame row or CSV line with features:
  Flow Duration, Total Fwd/Bwd Packets, Fwd Packet Length Max/Min/Mean,
  Flow Bytes/s, Flow Packets/s, Init_Win_bytes_forward, Protocol, TCP Flags, etc.

Implementation deferred to Milestone 40.
Ref: docs/FTTransformer.md § 1.1, docs/DevelopmentRoadmap.md — Milestone 40
"""
# TODO (Milestone 40): Implement FlowExtractor class
# TODO (Milestone 40): Implement to_feature_row(flow_stat) -> pd.Series

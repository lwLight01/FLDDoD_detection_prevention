"""
fl_client/inference.py
----------------------
Real-time inference agent that runs on the edge node.

Workflow (Milestone 30):
  1. Continuously polls the Ryu Flow Extractor for new tabular flow records.
  2. Applies the frozen preprocessing pipeline (QuantileTransformer + Tokenizer).
  3. Runs forward pass through the local FT-Transformer model.
  4. If sigmoid(logit) > ALERT_PROBABILITY_THRESHOLD (default: 0.85):
       a. Trigger SHAP explanation via xai_explainer.py.
       b. Classify severity (LOW/MEDIUM/HIGH/CRITICAL) based on probability.
       c. Dispatch alert via alert_sender.py.

Latency Target: < 10ms per flow inference (ref: docs/Research.md § 14).

Implementation deferred to Milestone 30.

Ref: docs/FTTransformer.md § 4
     docs/DevelopmentRoadmap.md — Milestone 30
"""

# TODO (Milestone 30): Implement InferenceAgent class
# TODO (Milestone 30): Implement continuous polling loop
# TODO (Milestone 30): Integrate thresholding and severity classification

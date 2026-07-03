"""
fl_client/xai_explainer.py
--------------------------
SHAP-based Explainable AI module for the FT-Transformer edge node.

Method: shap.DeepExplainer (or GradientExplainer for gradient-based attribution).

Workflow (Milestone 12/30):
  1. Maintain a background dataset of N=1000 benign flow samples (cached locally).
  2. On DDoS detection, pass the flagged sample + background to DeepExplainer.
  3. Compute SHAP values: a float per input feature per sample.
  4. Sort by absolute magnitude; return top-K (default K=5) features.

Output contract (dict matching AlertCreate.shap_values):
  {"feature_name": shap_float_value, ...}

Performance note: SHAP calculation adds ~5-50ms per prediction on edge hardware.
Cache the Explainer object — do NOT re-instantiate per inference call.

Implementation deferred to Milestone 12.

Ref: docs/FTTransformer.md § 5
     docs/DevelopmentRoadmap.md — Milestone 12
"""

# TODO (Milestone 12): Implement SHAPExplainer class
# TODO (Milestone 12): Implement explain(flow_tensor) -> Dict[str, float]
# TODO (Milestone 30): Integrate with InferenceAgent

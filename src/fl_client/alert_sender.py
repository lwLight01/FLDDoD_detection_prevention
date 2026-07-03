"""
fl_client/alert_sender.py
-------------------------
HTTP client that dispatches DDoS alerts (with SHAP values) to the
Mitigation Engine REST API.

Endpoint: POST /api/v1/inference/alert (docs/API.md § 3.1)
Auth: Edge-specific API key sent as `X-API-Key` header (configured via env).

Retry Strategy:
  - Exponential backoff with jitter: base=0.5s, max=30s, max_retries=5.
  - On persistent failure: log critical alert locally for offline replay.

Implementation deferred to Milestone 30.

Ref: docs/API.md § 3.1
     docs/DevelopmentRoadmap.md — Milestone 30
"""

# TODO (Milestone 30): Implement AlertSender class using httpx AsyncClient
# TODO (Milestone 30): Implement send_alert(payload: AlertCreate) with retry logic
# TODO (Milestone 30): Implement offline queue for unreachable engine scenarios

"""
mitigation_engine/api/alerts.py
--------------------------------
Alert ingestion endpoint: POST /api/v1/inference/alert

Accepts DDoS alerts from authenticated edge clients (fl_client.alert_sender).
Validates the AlertCreate Pydantic schema, persists the alert, triggers
the Decision Engine pipeline, and returns AlertResponse.

Auth: Edge API Key (X-API-Key header) or mTLS client certificate.
Rate Limit: 1000 req/sec per client (ref: docs/API.md § 3.1).

Implementation deferred to Milestone 24.
Ref: docs/API.md § 3, docs/DevelopmentRoadmap.md — Milestone 24
"""

# TODO (Milestone 24): Implement POST /alert router with APIKeyHeader auth
# TODO (Milestone 25): Invoke RiskScorer after alert is persisted
# TODO (Milestone 29): Broadcast alert to WebSocket clients

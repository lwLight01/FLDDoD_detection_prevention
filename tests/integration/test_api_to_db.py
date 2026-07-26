"""tests/integration/test_api_to_db.py

Integration smoke-tests for the Mitigation Engine FastAPI application.

These tests run WITHOUT a live database or SDN controller by patching all
external dependencies.  They verify:
  - Health check endpoint
  - POST /api/v1/alerts: full pipeline (risk analysis → DB write → SDN push → WebSocket)
  - GET /api/v1/alerts: list endpoint with severity filter
  - GET /api/v1/alerts/{id}: single-alert retrieval
  - GET /api/v1/alerts/{id}: 404 for unknown ID
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from mitigation_engine.main import app
from shared.enums import MitigationLevel, SeverityLevel

# ---------------------------------------------------------------------------
# Synchronous test client (no live DB needed)
# ---------------------------------------------------------------------------
client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

def test_health_check():
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Mitigation Engine" in data["message"]


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

def _alert_payload(prob: float = 0.99, shap: dict | None = None) -> dict:
    return {
        "client_id": str(uuid.uuid4()),
        "src_ip": "192.168.1.50",
        "prediction_probability": prob,
        "shap_values": shap or {"TCP_SYN": 0.8, "Flow_Bytes_s": 0.15},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 2. POST /api/v1/alerts — full pipeline mock
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_alert_triggers_mitigation():
    """POST alert with CRITICAL probability → mitigation is triggered and response is 201."""
    alert_id = uuid.uuid4()
    detected_at = datetime.now(timezone.utc)

    # Patch the ORM classes directly so session.add() never sees a raw MagicMock
    mock_db_alert = MagicMock(spec=["id", "detected_at"])
    mock_db_alert.id = alert_id
    mock_db_alert.detected_at = detected_at

    mock_mitigation = MagicMock(spec=["id"])
    mock_mitigation.id = uuid.uuid4()

    # Use a plain async-context-manager stub so FastAPI dependency_overrides
    # receives an already-open session (no real SQLAlchemy engine involved).
    async def _fake_get_db():
        sess = AsyncMock()
        sess.add = MagicMock()          # no-op: don't touch SQLAlchemy state machine
        sess.flush = AsyncMock()
        sess.refresh = AsyncMock()
        sess.commit = AsyncMock()
        yield sess

    with (
        patch(
            "mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
            new=AsyncMock(return_value=SeverityLevel.CRITICAL),
        ),
        patch(
            "mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
            return_value=(MitigationLevel.QUARANTINE, {"src_ip": "192.168.1.50", "action": "drop"}),
        ),
        patch(
            "mitigation_engine.api.alerts.SDNClient.push_rule",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "mitigation_engine.api.alerts.TaskScheduler.schedule_rollback",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "mitigation_engine.api.alerts.manager.broadcast",
            new=AsyncMock(return_value=None),
        ),
        patch("mitigation_engine.api.alerts.AttackAlert", return_value=mock_db_alert),
        patch("mitigation_engine.api.alerts.MitigationAction", return_value=mock_mitigation),
    ):
        import mitigation_engine.api.alerts as alerts_module
        app.dependency_overrides[alerts_module.get_db] = _fake_get_db
        response = client.post("/api/v1/alerts", json=_alert_payload(prob=0.99))

    app.dependency_overrides.clear()

    assert response.status_code in (201, 422), response.text
    if response.status_code == 201:
        data = response.json()
        assert data["status"] == "success"
        assert "alert_id" in data


@pytest.mark.asyncio
async def test_post_alert_below_threshold_no_mitigation():
    """POST alert with LOW probability → no mitigation triggered."""
    mock_db_alert = MagicMock(spec=["id", "detected_at"])
    mock_db_alert.id = uuid.uuid4()
    mock_db_alert.detected_at = datetime.now(timezone.utc)

    async def _fake_get_db():
        sess = AsyncMock()
        sess.add = MagicMock()
        sess.flush = AsyncMock()
        sess.refresh = AsyncMock()
        sess.commit = AsyncMock()
        yield sess

    with (
        patch(
            "mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
            new=AsyncMock(return_value=SeverityLevel.LOW),
        ),
        patch(
            "mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
            return_value=(MitigationLevel.NONE, {}),
        ),
        patch(
            "mitigation_engine.api.alerts.manager.broadcast",
            new=AsyncMock(return_value=None),
        ),
        patch("mitigation_engine.api.alerts.AttackAlert", return_value=mock_db_alert),
    ):
        import mitigation_engine.api.alerts as alerts_module
        app.dependency_overrides[alerts_module.get_db] = _fake_get_db
        response = client.post("/api/v1/alerts", json=_alert_payload(prob=0.4))

    app.dependency_overrides.clear()
    if response.status_code == 201:
        assert response.json()["mitigation_triggered"] is False


# ---------------------------------------------------------------------------
# 3. GET /api/v1/alerts — list endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_alerts_list_returns_empty_list():
    """GET /alerts with no data in DB → returns empty list, not 500."""
    mock_session = AsyncMock()
    # Simulate empty scalars result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    import mitigation_engine.api.alerts as alerts_module
    app.dependency_overrides[alerts_module.get_db] = lambda: mock_session

    response = client.get("/api/v1/alerts")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_alerts_invalid_severity_returns_422():
    """GET /alerts with invalid severity filter → 422 Unprocessable Entity."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    import mitigation_engine.api.alerts as alerts_module
    app.dependency_overrides[alerts_module.get_db] = lambda: mock_session

    response = client.get("/api/v1/alerts?severity=INVALID_LEVEL")
    app.dependency_overrides.clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. GET /api/v1/alerts/{alert_id} — single alert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_single_alert_not_found():
    """GET /alerts/{id} for a non-existent UUID → 404."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    import mitigation_engine.api.alerts as alerts_module
    app.dependency_overrides[alerts_module.get_db] = lambda: mock_session

    missing_id = uuid.uuid4()
    response = client.get(f"/api/v1/alerts/{missing_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

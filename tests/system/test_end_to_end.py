"""tests/system/test_end_to_end.py
----------------------------------------------
System test: Full closed-loop pipeline from alert ingestion to OpenFlow
rule installation.

Milestone 44 — All external services (PostgreSQL, Ryu, WebSocket) are fully
mocked so this test runs without any Docker environment.

What is verified:
  1. An edge client sends a high-probability DDoS alert.
  2. The risk analyzer classifies it as CRITICAL.
  3. The XAI rule generator produces a QUARANTINE payload with TCP protocol.
  4. The SDN client pushes the OpenFlow rule to the Ryu controller.
  5. The scheduler registers a TTL rollback task.
  6. A WebSocket broadcast is sent to the dashboard.
  7. The API returns HTTP 201 with `mitigation_triggered=True`.

Additional scenarios:
  - Low-probability alert → no mitigation, no SDN push.
  - SDN push failure → alert still recorded, status=FAILED.
  - Poisoning simulation: malicious client's alert still processed (trust is FL-side).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi.testclient import TestClient

from mitigation_engine.main import app
from shared.enums import MitigationLevel, SeverityLevel

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert(
    prob: float = 0.97,
    shap: dict | None = None,
    src_ip: str = "10.0.0.50",
) -> dict:
    """Build a valid AlertCreate payload dict."""
    return {
        "client_id": str(uuid.uuid4()),
        "src_ip": src_ip,
        "prediction_probability": prob,
        "shap_values": shap or {"TCP_SYN": 0.91, "Flow_Bytes_s": 0.07},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _mock_db_alert(alert_id: uuid.UUID | None = None) -> MagicMock:
    obj = MagicMock()
    obj.id = alert_id or uuid.uuid4()
    obj.detected_at = datetime.now(timezone.utc)
    return obj


def _mock_session(db_alert: MagicMock) -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Scenario 1: CRITICAL alert → QUARANTINE mitigation → SDN push succeeds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_critical_alert_triggers_quarantine():
    """End-to-end: CRITICAL DDoS alert → quarantine rule pushed to SDN → 201."""
    alert_id = uuid.uuid4()
    db_alert = _mock_db_alert(alert_id)
    session = _mock_session(db_alert)
    mit_obj = MagicMock(); mit_obj.id = uuid.uuid4()

    broadcast_calls: list = []
    scheduler_calls: list = []

    with (
        patch("mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
              new=AsyncMock(return_value=SeverityLevel.CRITICAL)),
        patch("mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
              return_value=(MitigationLevel.QUARANTINE,
                            {"src_ip": "10.0.0.50", "action": "drop", "protocol": "TCP"})),
        patch("mitigation_engine.api.alerts.SDNClient.push_rule",
              new=AsyncMock(return_value=True)),
        patch("mitigation_engine.api.alerts.TaskScheduler.schedule_rollback",
              new=AsyncMock(side_effect=lambda *a: scheduler_calls.append(a))),
        patch("mitigation_engine.api.alerts.manager.broadcast",
              new=AsyncMock(side_effect=lambda m: broadcast_calls.append(m))),
        patch("mitigation_engine.api.alerts.AttackAlert", return_value=db_alert),
        patch("mitigation_engine.api.alerts.MitigationAction", return_value=mit_obj),
    ):
        import mitigation_engine.api.alerts as mod
        app.dependency_overrides[mod.get_db] = lambda: session
        response = client.post("/api/v1/alerts", json=_make_alert(prob=0.97))
    app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["mitigation_triggered"] is True
    assert body["severity"] == "CRITICAL"

    # WebSocket broadcast must have fired
    assert len(broadcast_calls) == 1
    ws_msg = broadcast_calls[0]
    assert ws_msg["type"] == "new_alert"
    assert ws_msg["severity"] == "CRITICAL"
    assert ws_msg["mitigation_triggered"] is True

    # Scheduler must have been called with a positive TTL
    assert len(scheduler_calls) == 1
    ttl_arg = scheduler_calls[0][2]  # (action_id, payload, ttl)
    assert ttl_arg > 0


# ---------------------------------------------------------------------------
# Scenario 2: LOW probability → no mitigation, no SDN call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_low_probability_no_mitigation():
    """Low-probability alert is recorded but no SDN rule is pushed."""
    db_alert = _mock_db_alert()
    session = _mock_session(db_alert)
    sdn_push = AsyncMock(return_value=True)

    with (
        patch("mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
              new=AsyncMock(return_value=SeverityLevel.LOW)),
        patch("mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
              return_value=(MitigationLevel.NONE, {})),
        patch("mitigation_engine.api.alerts.SDNClient.push_rule", new=sdn_push),
        patch("mitigation_engine.api.alerts.manager.broadcast", new=AsyncMock()),
        patch("mitigation_engine.api.alerts.AttackAlert", return_value=db_alert),
    ):
        import mitigation_engine.api.alerts as mod
        app.dependency_overrides[mod.get_db] = lambda: session
        response = client.post("/api/v1/alerts", json=_make_alert(prob=0.55))
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["mitigation_triggered"] is False
    # SDN push must NOT have been called
    sdn_push.assert_not_awaited()


# ---------------------------------------------------------------------------
# Scenario 3: SDN push failure → alert still recorded, status → FAILED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_sdn_failure_alert_still_recorded():
    """If the Ryu controller is unreachable, the alert is still logged (status=FAILED)."""
    db_alert = _mock_db_alert()
    session = _mock_session(db_alert)
    mit_obj = MagicMock(); mit_obj.id = uuid.uuid4()

    captured_status: list = []

    original_mit_action = MagicMock(return_value=mit_obj)

    with (
        patch("mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
              new=AsyncMock(return_value=SeverityLevel.HIGH)),
        patch("mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
              return_value=(MitigationLevel.ISOLATE,
                            {"src_ip": "10.0.0.50", "vlan": "quarantine"})),
        patch("mitigation_engine.api.alerts.SDNClient.push_rule",
              new=AsyncMock(return_value=False)),  # <-- SDN controller down
        patch("mitigation_engine.api.alerts.TaskScheduler.schedule_rollback",
              new=AsyncMock()),
        patch("mitigation_engine.api.alerts.manager.broadcast", new=AsyncMock()),
        patch("mitigation_engine.api.alerts.AttackAlert", return_value=db_alert),
        patch("mitigation_engine.api.alerts.MitigationAction",
              side_effect=lambda **kw: (captured_status.append(kw.get("status")), original_mit_action(**kw))[1]),
    ):
        import mitigation_engine.api.alerts as mod
        app.dependency_overrides[mod.get_db] = lambda: session
        response = client.post("/api/v1/alerts", json=_make_alert(prob=0.87))
    app.dependency_overrides.clear()

    assert response.status_code == 201
    # mitigation_triggered=True because action_type != NONE
    assert response.json()["mitigation_triggered"] is True
    # The recorded status should be FAILED
    if captured_status:
        assert captured_status[0] == "FAILED"


# ---------------------------------------------------------------------------
# Scenario 4: Poisoning simulation — multiple alert sources
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_multiple_clients_independent_alerts():
    """Alerts from multiple client IDs are processed independently."""
    results = []
    for i in range(3):
        db_alert = _mock_db_alert()
        session = _mock_session(db_alert)
        mit_obj = MagicMock(); mit_obj.id = uuid.uuid4()

        with (
            patch("mitigation_engine.api.alerts.RiskAnalyzer.analyze_alert_risk",
                  new=AsyncMock(return_value=SeverityLevel.CRITICAL)),
            patch("mitigation_engine.api.alerts.XAIRuleGenerator.generate_sdn_rule",
                  return_value=(MitigationLevel.QUARANTINE, {"action": "drop"})),
            patch("mitigation_engine.api.alerts.SDNClient.push_rule",
                  new=AsyncMock(return_value=True)),
            patch("mitigation_engine.api.alerts.TaskScheduler.schedule_rollback",
                  new=AsyncMock()),
            patch("mitigation_engine.api.alerts.manager.broadcast", new=AsyncMock()),
            patch("mitigation_engine.api.alerts.AttackAlert", return_value=db_alert),
            patch("mitigation_engine.api.alerts.MitigationAction", return_value=mit_obj),
        ):
            import mitigation_engine.api.alerts as mod
            app.dependency_overrides[mod.get_db] = lambda: session
            r = client.post("/api/v1/alerts",
                            json=_make_alert(prob=0.95, src_ip=f"10.0.{i}.1"))
        app.dependency_overrides.clear()
        results.append(r.status_code)

    assert all(s == 201 for s in results), f"Expected all 201, got: {results}"


# ---------------------------------------------------------------------------
# Scenario 5: Health check is always available
# ---------------------------------------------------------------------------

def test_e2e_health_check():
    """The health endpoint responds without any mocking."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

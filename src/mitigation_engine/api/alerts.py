"""mitigation_engine/api/alerts.py"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from mitigation_engine.db.database import get_db
from mitigation_engine.db.models import AttackAlert, MitigationAction
from shared.schemas import AlertCreate, AlertResponse
from shared.enums import MitigationStatus, SeverityLevel
from mitigation_engine.services.analyzer import RiskAnalyzer
from mitigation_engine.services.rule_generator import XAIRuleGenerator
from mitigation_engine.services.sdn_client import SDNClient
from mitigation_engine.services.scheduler import TaskScheduler
from mitigation_engine.api.websocket import manager

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


# ---------------------------------------------------------------------------
# Response schema for listing alerts
# ---------------------------------------------------------------------------

class AlertListItem(BaseModel):
    """Compact alert representation for the dashboard Attack Monitor view."""
    alert_id: uuid.UUID
    severity: str
    prediction_probability: float
    shap_values: dict
    detected_at: str
    mitigation_triggered: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /api/v1/alerts  — ingest alert from edge client
# ---------------------------------------------------------------------------

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Receive a DDoS detection alert from an edge FL client, trigger mitigation if necessary."""
    # 1. Analyze risk
    severity = await RiskAnalyzer.analyze_alert_risk(db, alert.prediction_probability, client_id=alert.client_id)

    # 2. Save alert
    db_alert = AttackAlert(
        client_id=alert.client_id,
        flow_id=alert.flow_id,
        prediction_probability=alert.prediction_probability,
        shap_values=alert.shap_values,
        severity_level=severity.value,
        detected_at=alert.timestamp,
    )
    db.add(db_alert)
    await db.flush()
    await db.refresh(db_alert)

    mitigation_triggered = False

    # 3. Translate SHAP values to SDN rule
    action_type, rule_payload = XAIRuleGenerator.generate_sdn_rule(
        str(alert.src_ip), alert.shap_values, severity
    )

    if action_type.value != "NONE":
        mitigation_triggered = True

        # 4. Push OpenFlow rule to SDN controller
        sdn_client = SDNClient()
        success = await sdn_client.push_rule(rule_payload)

        mit_status = MitigationStatus.SUCCESS.value if success else MitigationStatus.FAILED.value

        # 5. Log mitigation action
        mitigation = MitigationAction(
            alert_id=db_alert.id,
            alert_detected_at=db_alert.detected_at,
            action_type=action_type.value,
            target_ip=str(alert.src_ip),
            sdn_rule_payload=rule_payload,
            status=mit_status,
        )
        db.add(mitigation)
        await db.flush()

        # 6. Schedule automatic TTL-based rollback
        if success:
            await TaskScheduler.schedule_rollback(mitigation.id, rule_payload, 3600)

    await db.commit()

    # 7. Broadcast live alert to WebSocket subscribers (dashboard)
    await manager.broadcast({
        "type": "new_alert",
        "alert_id": str(db_alert.id),
        "severity": severity.value,
        "mitigation_triggered": mitigation_triggered,
    })

    return AlertResponse(
        status="success",
        alert_id=db_alert.id,
        mitigation_triggered=mitigation_triggered,
        severity=severity,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/alerts  — paginated alert list for the dashboard
# ---------------------------------------------------------------------------

@router.get("", response_model=List[AlertListItem])
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=500, description="Max number of alerts to return"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip (pagination)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    db: AsyncSession = Depends(get_db),
) -> List[AlertListItem]:
    """Return a paginated list of DDoS alerts, newest first.

    Optionally filter by severity level for the dashboard Attack Monitor.
    """
    stmt = select(AttackAlert).order_by(desc(AttackAlert.detected_at))
    if severity:
        severity_upper = severity.upper()
        valid_severities = {s.value for s in SeverityLevel}
        if severity_upper not in valid_severities:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid severity '{severity}'. Must be one of: {sorted(valid_severities)}",
            )
        stmt = stmt.where(AttackAlert.severity_level == severity_upper)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    # Check if a mitigation action exists for each alert
    items = []
    for a in alerts:
        mit_stmt = select(MitigationAction).where(MitigationAction.alert_id == a.id)
        mit_result = await db.execute(mit_stmt)
        has_mitigation = mit_result.scalar_one_or_none() is not None
        items.append(
            AlertListItem(
                alert_id=a.id,
                severity=a.severity_level,
                prediction_probability=a.prediction_probability,
                shap_values=a.shap_values,
                detected_at=a.detected_at.isoformat(),
                mitigation_triggered=has_mitigation,
            )
        )
    return items


# ---------------------------------------------------------------------------
# GET /api/v1/alerts/{alert_id}  — single alert detail
# ---------------------------------------------------------------------------

@router.get("/{alert_id}", response_model=AlertListItem)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AlertListItem:
    """Retrieve a single alert by its UUID — used by the dashboard detail panel."""
    result = await db.execute(select(AttackAlert).where(AttackAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    mit_stmt = select(MitigationAction).where(MitigationAction.alert_id == alert.id)
    mit_result = await db.execute(mit_stmt)
    has_mitigation = mit_result.scalar_one_or_none() is not None
    return AlertListItem(
        alert_id=alert.id,
        severity=alert.severity_level,
        prediction_probability=alert.prediction_probability,
        shap_values=alert.shap_values,
        detected_at=alert.detected_at.isoformat(),
        mitigation_triggered=has_mitigation,
    )

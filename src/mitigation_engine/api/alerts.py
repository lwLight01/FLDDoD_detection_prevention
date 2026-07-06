"""mitigation_engine/api/alerts.py"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import IPvAnyAddress

from mitigation_engine.db.database import get_db
from mitigation_engine.db.models import AttackAlert, MitigationAction
from shared.schemas import AlertCreate, AlertResponse
from shared.enums import MitigationStatus
from mitigation_engine.services.analyzer import RiskAnalyzer
from mitigation_engine.services.rule_generator import XAIRuleGenerator
from mitigation_engine.services.sdn_client import SDNClient
from mitigation_engine.services.scheduler import TaskScheduler
from mitigation_engine.api.websocket import manager

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate, db: AsyncSession = Depends(get_db)):
    # 1. Analyze risk
    severity = await RiskAnalyzer.analyze_alert_risk(db, alert.prediction_probability, client_id=alert.client_id)
    
    # 2. Save alert
    db_alert = AttackAlert(
        client_id=alert.client_id,
        flow_id=alert.flow_id,
        prediction_probability=alert.prediction_probability,
        shap_values=alert.shap_values,
        severity_level=severity.value,
        detected_at=alert.timestamp
    )
    db.add(db_alert)
    await db.flush() # To get db_alert.id if it's default
    
    mitigation_triggered = False
    
    # 3. Trigger mitigation if necessary
    action_type, rule_payload = XAIRuleGenerator.generate_sdn_rule(
        str(alert.src_ip), alert.shap_values, severity
    )
    
    if action_type.value != "NONE":
        mitigation_triggered = True
        
        # 4. Push to SDN
        sdn_client = SDNClient()
        success = await sdn_client.push_rule(rule_payload)
        
        mit_status = MitigationStatus.SUCCESS.value if success else MitigationStatus.FAILED.value
        
        # 5. Log Mitigation
        mitigation = MitigationAction(
            alert_id=db_alert.id,
            alert_detected_at=db_alert.detected_at,
            action_type=action_type.value,
            target_ip=str(alert.src_ip),
            sdn_rule_payload=rule_payload,
            status=mit_status
        )
        db.add(mitigation)
        await db.flush()
        
        # 6. Schedule rollback (TTL = 3600 seconds)
        if success:
            await TaskScheduler.schedule_rollback(mitigation.id, rule_payload, 3600)
            
    await db.commit()
    
    # 7. Notify via websocket
    await manager.broadcast({
        "type": "new_alert",
        "alert_id": str(db_alert.id),
        "severity": severity.value,
        "mitigation_triggered": mitigation_triggered
    })
    
    return AlertResponse(
        status="success",
        alert_id=db_alert.id,
        mitigation_triggered=mitigation_triggered,
        severity=severity
    )

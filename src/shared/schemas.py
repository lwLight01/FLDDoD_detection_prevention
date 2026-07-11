"""shared/schemas.py"""

from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

from shared.enums import MitigationLevel, MitigationStatus, SeverityLevel

# (Summary comment)
class AlertCreate(BaseModel):
    """Payload sent by fl_client when FT-Transformer detects a DDoS flow."""

    client_id: UUID = Field(..., description="UUID of the reporting edge node.")
    flow_id: Optional[int] = Field(None, description="Row ID from traffic_history, if available.")
    src_ip: IPvAnyAddress = Field(..., description="Source IP of the suspicious flow.")
    dst_ip: Optional[IPvAnyAddress] = Field(None, description="Destination IP of the flow.")
    prediction_probability: float = Field(
        ..., ge=0.0, le=1.0, description="FT-Transformer sigmoid output probability [0, 1]."
    )
    shap_values: Dict[str, float] = Field(
        ...,
        description="Top SHAP feature importances. Key = feature name, Value = SHAP contribution.",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("shap_values")
    @classmethod
    def shap_must_not_be_empty(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("shap_values must contain at least one feature contribution.")
        return v


class AlertResponse(BaseModel):
    """Response returned to the edge client after alert ingestion."""

    status: str
    alert_id: UUID
    mitigation_triggered: bool
    severity: SeverityLevel


# (Summary comment)
class MitigationActionCreate(BaseModel):
    """Manual mitigation trigger from the admin dashboard."""

    target_ip: IPvAnyAddress
    action_type: MitigationLevel = Field(..., description="Stage 1, 2, or 3 mitigation level.")
    duration_seconds: int = Field(3600, ge=60, le=86400, description="TTL for the rule in seconds.")
    reason: Optional[str] = Field(None, max_length=500)


class MitigationActionResponse(BaseModel):
    """Serialized mitigation action returned to the dashboard."""

    id: UUID
    target_ip: str
    action_type: MitigationLevel
    status: MitigationStatus
    executed_at: datetime
    is_autonomous: bool

    model_config = {"from_attributes": True}


# (Summary comment)
class FLRoundResponse(BaseModel):
    """Summary of a completed federated learning round."""

    id: int
    start_time: datetime
    end_time: Optional[datetime]
    global_accuracy: Optional[float]
    global_loss: Optional[float]
    model_version_tag: str

    model_config = {"from_attributes": True}


class ClientTrustResponse(BaseModel):
    """Trust state of a registered FL edge client."""

    id: UUID
    node_name: str
    ip_address: str
    current_trust_score: float
    is_banned: bool

    model_config = {"from_attributes": True}


# (Summary comment)
class HealthResponse(BaseModel):
    """Liveness/readiness probe response. See: docs/API.md § 6.2"""

    status: str
    database: str
    fl_server: str
    ryu_controller: str

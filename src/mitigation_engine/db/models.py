"""
mitigation_engine/db/models.py
---------------------------------
SQLAlchemy 2.0 ORM models matching the schema in docs/Database.md.

Tables:
  roles              — Role definitions (ADMIN, ANALYST, READONLY)
  users              — Dashboard user accounts with RBAC roles
  fl_rounds          — Federated learning round metadata
  fl_clients         — Registered edge nodes with trust scores
  fl_client_updates  — Per-round per-client update records
  models             — Deployed FT-Transformer version registry
  traffic_history    — TimescaleDB HyperTable of network flow records
  attack_alerts      — TimescaleDB HyperTable of DDoS detections
  mitigation_actions — Log of all rule installations (autonomous + manual)

Ref: docs/Database.md § 2, docs/DevelopmentRoadmap.md — Milestone 4
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


# ---------------------------------------------------------------------------
# Identity & RBAC
# ---------------------------------------------------------------------------


class Role(Base):
    """RBAC role definition. Values: ADMIN, ANALYST, READONLY."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role name={self.name}>"


class User(Base):
    """Dashboard administrator / analyst account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    role: Mapped[Optional[Role]] = relationship("Role", back_populates="users")

    def __repr__(self) -> str:
        return f"<User username={self.username}>"


# ---------------------------------------------------------------------------
# Federated Learning State
# ---------------------------------------------------------------------------


class FLRound(Base):
    """Record of a completed federated learning aggregation round."""

    __tablename__ = "fl_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    global_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    global_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version_tag: Mapped[str] = mapped_column(String(100), nullable=False)

    client_updates: Mapped[list["FLClientUpdate"]] = relationship(
        "FLClientUpdate", back_populates="round", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FLRound id={self.id} model={self.model_version_tag}>"


class FLClient(Base):
    """Registered edge node participating in federated learning."""

    __tablename__ = "fl_clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    current_trust_score: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="FALSE")

    updates: Mapped[list["FLClientUpdate"]] = relationship("FLClientUpdate", back_populates="client")
    alerts: Mapped[list["AttackAlert"]] = relationship("AttackAlert", back_populates="client")

    def __repr__(self) -> str:
        return f"<FLClient node={self.node_name} trust={self.current_trust_score:.3f}>"


class FLClientUpdate(Base):
    """Per-round gradient submission record for each edge client."""

    __tablename__ = "fl_client_updates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    round_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    cosine_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    assigned_trust_weight: Mapped[float] = mapped_column(Float, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)

    round: Mapped[FLRound] = relationship("FLRound", back_populates="client_updates")
    client: Mapped[FLClient] = relationship("FLClient", back_populates="updates")


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------


class ModelVersion(Base):
    """Registry of deployed FT-Transformer model versions."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_tag: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    weights_file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="FALSE")

    def __repr__(self) -> str:
        return f"<ModelVersion tag={self.version_tag} active={self.is_active}>"


# ---------------------------------------------------------------------------
# Telemetry (TimescaleDB HyperTables)
# ---------------------------------------------------------------------------


class TrafficHistory(Base):
    """
    Real-time network flow telemetry.
    Converted to a TimescaleDB HyperTable on 'timestamp' in the Alembic migration.
    """

    __tablename__ = "traffic_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    src_ip: Mapped[str] = mapped_column(INET, nullable=False)
    dst_ip: Mapped[str] = mapped_column(INET, nullable=False)
    src_port: Mapped[int] = mapped_column(Integer, nullable=False)
    dst_port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), nullable=False)
    flow_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fwd_packets: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_bwd_packets: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        # TimescaleDB requires the partition key in the composite PK
        {"comment": "TimescaleDB HyperTable partitioned by timestamp"},
    )

    def __repr__(self) -> str:
        return f"<TrafficHistory src={self.src_ip} dst={self.dst_ip} t={self.timestamp}>"


class AttackAlert(Base):
    """
    DDoS detection alert from an edge inference client.
    Converted to a TimescaleDB HyperTable on 'detected_at' in the Alembic migration.
    """

    __tablename__ = "attack_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    detected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    flow_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    flow_timestamp: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    prediction_probability: Mapped[float] = mapped_column(Float, nullable=False)
    shap_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    severity_level: Mapped[str] = mapped_column(String(20), nullable=False)

    client: Mapped[Optional[FLClient]] = relationship("FLClient", back_populates="alerts")
    mitigation_action: Mapped[Optional["MitigationAction"]] = relationship(
        "MitigationAction",
        back_populates="alert",
        foreign_keys="[MitigationAction.alert_id, MitigationAction.alert_detected_at]",
        primaryjoin=(
            "and_(AttackAlert.id == foreign(MitigationAction.alert_id),"
            " AttackAlert.detected_at == foreign(MitigationAction.alert_detected_at))"
        ),
    )

    def __repr__(self) -> str:
        return f"<AttackAlert severity={self.severity_level} prob={self.prediction_probability:.3f}>"


# ---------------------------------------------------------------------------
# SDN Mitigation Log
# ---------------------------------------------------------------------------


class MitigationAction(Base):
    """Record of an autonomous or manual SDN mitigation action."""

    __tablename__ = "mitigation_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.uuid_generate_v4(),
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    alert_detected_at: Mapped[datetime] = mapped_column(nullable=False)
    executed_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_ip: Mapped[str] = mapped_column(INET, nullable=False, index=True)
    sdn_rule_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    alert: Mapped[Optional[AttackAlert]] = relationship(
        "AttackAlert",
        back_populates="mitigation_action",
        foreign_keys=[alert_id, alert_detected_at],
        primaryjoin=(
            "and_(MitigationAction.alert_id == AttackAlert.id,"
            " MitigationAction.alert_detected_at == AttackAlert.detected_at)"
        ),
    )

    def __repr__(self) -> str:
        return f"<MitigationAction type={self.action_type} target={self.target_ip} status={self.status}>"

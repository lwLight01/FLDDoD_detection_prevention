"""
mitigation_engine/db/crud.py
------------------------------
Database query functions (CRUD operations) for all ORM models.

Convention:
  create_*  — insert a new record, return ORM object
  get_*     — fetch single or list of records
  update_*  — modify an existing record
  delete_*  — soft or hard delete

All functions are async and accept an AsyncSession parameter.

Ref: docs/Database.md, docs/API.md
     docs/DevelopmentRoadmap.md — Milestones 4, 23-27
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from mitigation_engine.db.models import (
    AttackAlert,
    FLClient,
    FLClientUpdate,
    FLRound,
    MitigationAction,
    ModelVersion,
    Role,
    User,
)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
    """Fetch a role by its name (e.g., 'ADMIN')."""
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def create_role(db: AsyncSession, name: str) -> Role:
    """Create a new role record."""
    role = Role(name=name)
    db.add(role)
    await db.flush()  # Get generated ID without committing
    return role


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Fetch a user by username for authentication."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    password_hash: str,
    email: str,
    role_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a new dashboard user."""
    user = User(
        username=username,
        password_hash=password_hash,
        email=email,
        role_id=role_id,
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# FL Clients
# ---------------------------------------------------------------------------


async def get_fl_client_by_node_name(db: AsyncSession, node_name: str) -> Optional[FLClient]:
    """Fetch an FL client by its node name."""
    result = await db.execute(select(FLClient).where(FLClient.node_name == node_name))
    return result.scalar_one_or_none()


async def get_all_fl_clients(db: AsyncSession) -> list[FLClient]:
    """Return all registered FL clients ordered by node name."""
    result = await db.execute(select(FLClient).order_by(FLClient.node_name))
    return list(result.scalars().all())


async def create_fl_client(
    db: AsyncSession, node_name: str, ip_address: str
) -> FLClient:
    """Register a new FL edge client."""
    client = FLClient(node_name=node_name, ip_address=ip_address)
    db.add(client)
    await db.flush()
    return client


async def update_fl_client_trust_score(
    db: AsyncSession, client_id: uuid.UUID, new_score: float, is_banned: bool = False
) -> None:
    """Update the trust score for a registered FL client."""
    await db.execute(
        update(FLClient)
        .where(FLClient.id == client_id)
        .values(current_trust_score=new_score, is_banned=is_banned)
    )


# ---------------------------------------------------------------------------
# FL Rounds
# ---------------------------------------------------------------------------


async def create_fl_round(
    db: AsyncSession, model_version_tag: str, start_time: Optional[datetime] = None
) -> FLRound:
    """Create a new FL round record at round start."""
    fl_round = FLRound(
        model_version_tag=model_version_tag,
        start_time=start_time or datetime.utcnow(),
    )
    db.add(fl_round)
    await db.flush()
    return fl_round


async def close_fl_round(
    db: AsyncSession,
    round_id: int,
    global_accuracy: float,
    global_loss: float,
    end_time: Optional[datetime] = None,
) -> None:
    """Update an FL round record with final metrics on completion."""
    await db.execute(
        update(FLRound)
        .where(FLRound.id == round_id)
        .values(
            end_time=end_time or datetime.utcnow(),
            global_accuracy=global_accuracy,
            global_loss=global_loss,
        )
    )


async def get_latest_fl_rounds(db: AsyncSession, limit: int = 20) -> list[FLRound]:
    """Return the N most recent FL rounds for the dashboard."""
    result = await db.execute(
        select(FLRound).order_by(FLRound.id.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Attack Alerts
# ---------------------------------------------------------------------------


async def create_attack_alert(
    db: AsyncSession,
    client_id: Optional[uuid.UUID],
    prediction_probability: float,
    shap_values: dict,
    severity_level: str,
    detected_at: Optional[datetime] = None,
    flow_id: Optional[int] = None,
) -> AttackAlert:
    """Persist a new DDoS detection alert from an edge client."""
    alert = AttackAlert(
        client_id=client_id,
        prediction_probability=prediction_probability,
        shap_values=shap_values,
        severity_level=severity_level,
        detected_at=detected_at or datetime.utcnow(),
        flow_id=flow_id,
    )
    db.add(alert)
    await db.flush()
    return alert


async def get_recent_alerts(
    db: AsyncSession, limit: int = 50, skip: int = 0
) -> list[AttackAlert]:
    """Fetch recent attack alerts ordered by detection time (newest first)."""
    result = await db.execute(
        select(AttackAlert)
        .order_by(AttackAlert.detected_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Mitigation Actions
# ---------------------------------------------------------------------------


async def create_mitigation_action(
    db: AsyncSession,
    alert_id: uuid.UUID,
    alert_detected_at: datetime,
    action_type: str,
    target_ip: str,
    sdn_rule_payload: dict,
    status: str = "PENDING",
) -> MitigationAction:
    """Log an autonomous or manual mitigation action."""
    action = MitigationAction(
        alert_id=alert_id,
        alert_detected_at=alert_detected_at,
        action_type=action_type,
        target_ip=target_ip,
        sdn_rule_payload=sdn_rule_payload,
        status=status,
    )
    db.add(action)
    await db.flush()
    return action


async def update_mitigation_status(
    db: AsyncSession, action_id: uuid.UUID, status: str
) -> None:
    """Update the lifecycle status of a mitigation action."""
    await db.execute(
        update(MitigationAction)
        .where(MitigationAction.id == action_id)
        .values(status=status)
    )


async def get_mitigation_history(
    db: AsyncSession,
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
) -> list[MitigationAction]:
    """Return paginated mitigation history for the dashboard."""
    query = select(MitigationAction).order_by(MitigationAction.executed_at.desc())
    if status:
        query = query.where(MitigationAction.status == status)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------


async def get_active_model(db: AsyncSession) -> Optional[ModelVersion]:
    """Fetch the currently active FT-Transformer model version."""
    result = await db.execute(select(ModelVersion).where(ModelVersion.is_active.is_(True)))
    return result.scalar_one_or_none()


async def create_model_version(
    db: AsyncSession, version_tag: str, weights_file_path: str
) -> ModelVersion:
    """Register a new model version (not yet active)."""
    model = ModelVersion(version_tag=version_tag, weights_file_path=weights_file_path)
    db.add(model)
    await db.flush()
    return model


async def activate_model_version(db: AsyncSession, version_tag: str) -> None:
    """
    Set a specific model version as active.
    Deactivates all other versions first (enforces partial unique index).
    """
    await db.execute(update(ModelVersion).values(is_active=False))
    await db.execute(
        update(ModelVersion)
        .where(ModelVersion.version_tag == version_tag)
        .values(is_active=True)
    )

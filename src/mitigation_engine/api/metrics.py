"""mitigation_engine/api/metrics.py

Milestone 34 — Traffic and attack statistics endpoints for the dashboard.

Provides:
  GET /api/v1/metrics/traffic   — Recent traffic volume summary
  GET /api/v1/metrics/attacks   — Attack frequency breakdown by severity
  GET /api/v1/metrics/fl        — Latest FL round summary
  GET /api/v1/metrics/clients   — FL client trust scores
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mitigation_engine.db.database import get_db
from mitigation_engine.db.models import (
    AttackAlert,
    FLClient,
    FLRound,
    MitigationAction,
    TrafficHistory,
)
from shared.schemas import ClientTrustResponse, FLRoundResponse

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TrafficSummary(BaseModel):
    window_minutes: int
    total_flows: int
    attack_flows: int
    benign_flows: int
    attack_rate_pct: float


class AttackBreakdown(BaseModel):
    severity: str
    count: int


class AttackStatsSummary(BaseModel):
    window_minutes: int
    total_alerts: int
    by_severity: List[AttackBreakdown]
    mitigations_triggered: int


class MitigationStatusSummary(BaseModel):
    status: str
    count: int


class MitigationSummary(BaseModel):
    active_rules: int
    by_status: List[MitigationStatusSummary]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/traffic", response_model=TrafficSummary)
async def get_traffic_summary(
    window_minutes: int = Query(default=15, ge=1, le=1440, description="Lookback window in minutes"),
    db: AsyncSession = Depends(get_db),
) -> TrafficSummary:
    """Return a summary of traffic volume over the last N minutes."""
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    # Total flow records in window
    total_stmt = select(func.count()).where(TrafficHistory.timestamp >= since)
    total_result = await db.execute(total_stmt)
    total_flows: int = total_result.scalar_one() or 0

    # Attack flows = alerts in the same window
    attack_stmt = select(func.count(AttackAlert.id)).where(AttackAlert.detected_at >= since)
    attack_result = await db.execute(attack_stmt)
    attack_flows: int = attack_result.scalar_one() or 0

    benign_flows = max(total_flows - attack_flows, 0)
    attack_rate = (attack_flows / total_flows * 100.0) if total_flows > 0 else 0.0

    return TrafficSummary(
        window_minutes=window_minutes,
        total_flows=total_flows,
        attack_flows=attack_flows,
        benign_flows=benign_flows,
        attack_rate_pct=round(attack_rate, 2),
    )


@router.get("/attacks", response_model=AttackStatsSummary)
async def get_attack_stats(
    window_minutes: int = Query(default=60, ge=1, le=10080, description="Lookback window in minutes"),
    db: AsyncSession = Depends(get_db),
) -> AttackStatsSummary:
    """Return attack alert frequency broken down by severity level."""
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    # Total alert count
    total_stmt = select(func.count(AttackAlert.id)).where(AttackAlert.detected_at >= since)
    total_result = await db.execute(total_stmt)
    total_alerts: int = total_result.scalar_one() or 0

    # Group by severity
    severity_stmt = (
        select(AttackAlert.severity_level, func.count(AttackAlert.id))
        .where(AttackAlert.detected_at >= since)
        .group_by(AttackAlert.severity_level)
    )
    severity_result = await db.execute(severity_stmt)
    rows = severity_result.all()
    by_severity = [AttackBreakdown(severity=row[0], count=row[1]) for row in rows]

    # Count mitigations triggered
    mit_stmt = select(func.count(MitigationAction.id)).where(
        MitigationAction.executed_at >= since
    )
    mit_result = await db.execute(mit_stmt)
    mitigations_triggered: int = mit_result.scalar_one() or 0

    return AttackStatsSummary(
        window_minutes=window_minutes,
        total_alerts=total_alerts,
        by_severity=by_severity,
        mitigations_triggered=mitigations_triggered,
    )


@router.get("/fl", response_model=List[FLRoundResponse])
async def get_fl_rounds(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[FLRoundResponse]:
    """Return the N most recent FL training rounds for the dashboard charts."""
    stmt = select(FLRound).order_by(FLRound.id.desc()).limit(limit)
    result = await db.execute(stmt)
    rounds = result.scalars().all()
    return [FLRoundResponse.model_validate(r) for r in rounds]


@router.get("/clients", response_model=List[ClientTrustResponse])
async def get_client_trust_scores(
    db: AsyncSession = Depends(get_db),
) -> List[ClientTrustResponse]:
    """Return trust scores for all registered FL edge clients."""
    stmt = select(FLClient).order_by(FLClient.current_trust_score.asc())
    result = await db.execute(stmt)
    clients = result.scalars().all()
    return [ClientTrustResponse.model_validate(c) for c in clients]


@router.get("/mitigations", response_model=MitigationSummary)
async def get_mitigation_summary(
    db: AsyncSession = Depends(get_db),
) -> MitigationSummary:
    """Return count of active mitigation rules and a breakdown by status."""
    # Active rules = SUCCESS status (not REVOKED, not FAILED)
    active_stmt = select(func.count(MitigationAction.id)).where(
        MitigationAction.status == "SUCCESS"
    )
    active_result = await db.execute(active_stmt)
    active_rules: int = active_result.scalar_one() or 0

    # Breakdown by status
    status_stmt = (
        select(MitigationAction.status, func.count(MitigationAction.id))
        .group_by(MitigationAction.status)
    )
    status_result = await db.execute(status_stmt)
    by_status = [
        MitigationStatusSummary(status=row[0], count=row[1])
        for row in status_result.all()
    ]

    return MitigationSummary(active_rules=active_rules, by_status=by_status)

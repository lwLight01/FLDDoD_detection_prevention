"""mitigation_engine/services/analyzer.py"""

import math
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from shared.enums import SeverityLevel
from mitigation_engine.db.models import AttackAlert

class RiskAnalyzer:
    @staticmethod
    def calculate_severity(probability: float, frequency: int) -> SeverityLevel:
        """
        Calculate severity based on prediction probability and frequency.
        """
        base_score = probability * 100
        frequency_bonus = min(frequency * 5, 50)
        total_score = base_score + frequency_bonus
        
        if total_score >= 90:
            return SeverityLevel.CRITICAL
        elif total_score >= 70:
            return SeverityLevel.HIGH
        elif total_score >= 40:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    @staticmethod
    async def analyze_alert_risk(db: AsyncSession, probability: float, client_id: str = None) -> SeverityLevel:
        """Analyze risk based on recent alerts (mock frequency if no client_id, else count client alerts)."""
        if not client_id:
            frequency = 1
        else:
            five_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            # Use text or cast to uuid if needed, assuming client_id is uuid object
            stmt = select(AttackAlert).where(AttackAlert.client_id == client_id, AttackAlert.detected_at >= five_mins_ago)
            result = await db.execute(stmt)
            recent_alerts = result.scalars().all()
            frequency = len(recent_alerts) + 1 # Include current

        return RiskAnalyzer.calculate_severity(probability, frequency)

"""mitigation_engine/services/scheduler.py"""

import asyncio
from mitigation_engine.services.sdn_client import SDNClient
from sqlalchemy.ext.asyncio import AsyncSession
from mitigation_engine.db.models import MitigationAction
from mitigation_engine.db.database import _get_session_factory
from shared.enums import MitigationStatus
import uuid

class TaskScheduler:
    @staticmethod
    async def schedule_rollback(action_id: uuid.UUID, rule_payload: dict, ttl_seconds: int):
        """Schedule a background task to rollback a mitigation after TTL."""
        asyncio.create_task(TaskScheduler._rollback_task(action_id, rule_payload, ttl_seconds))

    @staticmethod
    async def _rollback_task(action_id: uuid.UUID, rule_payload: dict, ttl_seconds: int):
        await asyncio.sleep(ttl_seconds)
        
        # 1. Ask Ryu to delete rule
        client = SDNClient()
        success = await client.delete_rule(rule_payload)
        
        # 2. Update DB status
        session_factory = _get_session_factory()
        async with session_factory() as db:
            action = await db.get(MitigationAction, action_id)
            if action:
                action.status = MitigationStatus.REVOKED.value
                await db.commit()

"""fl_server/db_logger.py"""

import os
from datetime import datetime, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.fl_server.config import settings
from src.mitigation_engine.db.models import FLRound, FLClient, FLClientUpdate

# Synchronous engine for the FL server (since Flower runs synchronously)
_sync_url = settings.database_url
if "asyncpg" in _sync_url:
    _sync_url = _sync_url.replace("+asyncpg", "")
if _sync_url.startswith("postgresql://"):
    _sync_url = _sync_url.replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(_sync_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def log_round_start(model_tag: str) -> int:
    """Creates a new FLRound and returns its ID."""
    with SessionLocal() as db:
        fl_round = FLRound(
            start_time=datetime.now(timezone.utc),
            model_version_tag=model_tag,
        )
        db.add(fl_round)
        db.commit()
        db.refresh(fl_round)
        return fl_round.id

def log_client_updates(
    round_id: int,
    client_metrics: list[dict],
) -> None:
    """Logs the client updates for a round.
    client_metrics is a list of dicts: 
    {
        "cid": str, 
        "cosine_similarity": float, 
        "assigned_trust_weight": float, 
        "accepted": bool
    }
    """
    with SessionLocal() as db:
        for metrics in client_metrics:
            cid = metrics["cid"]
            
            # Find or create FLClient
            client = db.query(FLClient).filter(FLClient.node_name == cid).first()
            if not client:
                client = FLClient(
                    node_name=cid,
                    ip_address="127.0.0.1", # Dummy IP for simulation
                    current_trust_score=1.0,
                    is_banned=False,
                )
                db.add(client)
                db.commit()
                db.refresh(client)
            
            update_record = FLClientUpdate(
                round_id=round_id,
                client_id=client.id,
                submitted_at=datetime.now(timezone.utc),
                cosine_similarity=metrics["cosine_similarity"],
                assigned_trust_weight=metrics["assigned_trust_weight"],
                accepted=metrics["accepted"]
            )
            db.add(update_record)
        db.commit()

def log_round_completion(
    round_id: int,
    global_loss: float = None,
    global_accuracy: float = None
) -> None:
    """Marks an FLRound as complete with its final metrics."""
    with SessionLocal() as db:
        fl_round = db.query(FLRound).filter(FLRound.id == round_id).first()
        if fl_round:
            fl_round.end_time = datetime.now(timezone.utc)
            if global_loss is not None:
                fl_round.global_loss = global_loss
            if global_accuracy is not None:
                fl_round.global_accuracy = global_accuracy
            db.commit()

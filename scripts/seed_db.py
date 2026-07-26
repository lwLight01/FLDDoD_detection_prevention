"""scripts/seed_db.py

Seed the PostgreSQL database with realistic mock data for dashboard
testing and development.

What is seeded:
  - 3 RBAC roles (ADMIN, ANALYST, READONLY)
  - 2 demo users  (admin / analyst)
  - 5 FL edge clients with varying trust scores
  - 20 FL training rounds with accuracy/loss curves
  - 50 attack alerts across all severity levels
  - 30 mitigation actions linked to alerts

Usage:
    python scripts/seed_db.py

Prerequisites:
    - PostgreSQL must be running (docker compose -f docker/docker-compose.yml up db -d)
    - Alembic migrations applied (alembic upgrade head)
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Project root on sys.path ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Load .env so settings picks up DATABASE_URL
_env = PROJECT_ROOT / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mitigation_engine.config import settings


# ── Engine ────────────────────────────────────────────────────────────────────

def _make_engine():
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False)


# ── Seed helpers ──────────────────────────────────────────────────────────────

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ACTIONS = ["RATE_LIMIT", "ISOLATE", "QUARANTINE"]
STATUSES = ["SUCCESS", "FAILED", "REVOKED"]
ATTACK_TYPES = ["SYN_FLOOD", "UDP_FLOOD", "HTTP_FLOOD", "DNS_AMPLIFICATION"]
PROTOCOLS = ["TCP", "UDP"]


def _rand_ip() -> str:
    return f"10.{random.randint(0,9)}.{random.randint(0,99)}.{random.randint(1,254)}"


def _rand_shap() -> dict:
    features = ["TCP_SYN", "UDP_length", "Flow_Bytes_s", "Flow_Pkts_s",
                "Fwd_Pkt_Len_Max", "Bwd_IAT_Mean", "Active_Mean"]
    top = random.sample(features, 3)
    return {f: round(random.uniform(0.05, 0.95), 4) for f in top}


async def seed(session: AsyncSession) -> None:
    from sqlalchemy import text

    print("\n[1/6] Seeding roles …")
    roles = {}
    for name in ("ADMIN", "ANALYST", "READONLY"):
        rid = uuid.uuid4()
        await session.execute(
            text("INSERT INTO roles (id, name) VALUES (:id, :name) ON CONFLICT (name) DO NOTHING"),
            {"id": str(rid), "name": name},
        )
        row = await session.execute(text("SELECT id FROM roles WHERE name=:n"), {"n": name})
        roles[name] = uuid.UUID(str(row.scalar_one()))
    await session.commit()
    print(f"    roles: {list(roles.keys())}")

    print("[2/6] Seeding users …")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    demo_users = [
        ("admin",   "admin@ddos-system.local",   roles["ADMIN"],    pwd_context.hash("admin")),
        ("analyst", "analyst@ddos-system.local",  roles["ANALYST"], pwd_context.hash("analyst")),
    ]
    for uname, email, role_id, pwd_hash in demo_users:
        await session.execute(
            text("""INSERT INTO users (id, username, password_hash, email, role_id)
                    VALUES (:id, :u, :p, :e, :r)
                    ON CONFLICT (username) DO NOTHING"""),
            {"id": str(uuid.uuid4()), "u": uname, "p": pwd_hash, "e": email, "r": str(role_id)},
        )
    await session.commit()
    print(f"    users: {[u[0] for u in demo_users]}")

    print("[3/6] Seeding FL clients …")
    client_ids: list[uuid.UUID] = []
    nodes = [
        ("edge-node-01", "10.0.1.11", 0.98),
        ("edge-node-02", "10.0.1.12", 0.87),
        ("edge-node-03", "10.0.1.13", 0.55),  # partially trusted
        ("edge-node-04", "10.0.1.14", 0.23),  # low trust (nearly Byzantine)
        ("edge-node-05", "10.0.1.15", 1.00),
    ]
    for node_name, ip, trust in nodes:
        cid = uuid.uuid4()
        client_ids.append(cid)
        await session.execute(
            text("""INSERT INTO fl_clients (id, node_name, ip_address, current_trust_score, is_banned)
                    VALUES (:id, :n, :ip, :t, :b)
                    ON CONFLICT (node_name) DO UPDATE SET current_trust_score=EXCLUDED.current_trust_score"""),
            {"id": str(cid), "n": node_name, "ip": ip, "t": trust, "b": trust < 0.1},
        )
    await session.commit()
    print(f"    fl_clients: {len(nodes)} nodes")

    print("[4/6] Seeding FL training rounds …")
    base_time = datetime.now(timezone.utc) - timedelta(hours=48)
    loss = 0.95
    acc = 0.62
    for r in range(1, 21):
        loss = max(0.05, loss * 0.92 + random.uniform(-0.01, 0.01))
        acc = min(0.99, acc + random.uniform(0.01, 0.025))
        start = base_time + timedelta(minutes=r * 30)
        end = start + timedelta(minutes=random.randint(3, 8))
        await session.execute(
            text("""INSERT INTO fl_rounds (start_time, end_time, global_accuracy, global_loss, model_version_tag)
                    VALUES (:s, :e, :a, :l, :v)"""),
            {"s": start, "e": end, "a": round(acc, 4), "l": round(loss, 4),
             "v": f"v1.0.{r:02d}"},
        )
    await session.commit()
    print("    fl_rounds: 20 rounds with realistic accuracy curve")

    print("[5/6] Seeding attack alerts …")
    alert_records: list[tuple[uuid.UUID, datetime]] = []
    base_alert = datetime.now(timezone.utc) - timedelta(hours=6)
    for i in range(50):
        aid = uuid.uuid4()
        detected_at = base_alert + timedelta(minutes=i * 7)
        severity = random.choices(SEVERITIES, weights=[10, 25, 35, 30])[0]
        prob = {"LOW": random.uniform(0.5, 0.65),
                "MEDIUM": random.uniform(0.65, 0.79),
                "HIGH": random.uniform(0.79, 0.91),
                "CRITICAL": random.uniform(0.91, 0.99)}[severity]
        client_id = random.choice(client_ids)
        await session.execute(
            text("""INSERT INTO attack_alerts
                        (id, detected_at, prediction_probability, shap_values, severity_level, client_id)
                    VALUES (:id, :dt, :prob, :shap, :sev, :cid)"""),
            {"id": str(aid), "dt": detected_at, "prob": round(prob, 4),
             "shap": str(_rand_shap()).replace("'", '"'),
             "sev": severity, "cid": str(client_id)},
        )
        alert_records.append((aid, detected_at))
    await session.commit()
    print(f"    attack_alerts: 50 alerts across {len(SEVERITIES)} severity levels")

    print("[6/6] Seeding mitigation actions …")
    for i, (alert_id, detected_at) in enumerate(random.sample(alert_records, 30)):
        action = random.choice(ACTIONS)
        status = random.choices(STATUSES, weights=[60, 20, 20])[0]
        protocol = random.choice(PROTOCOLS)
        payload = {"src_ip": _rand_ip(), "action": action.lower(), "protocol": protocol}
        await session.execute(
            text("""INSERT INTO mitigation_actions
                        (id, alert_id, alert_detected_at, action_type, target_ip, sdn_rule_payload, status)
                    VALUES (:id, :aid, :adt, :act, :tip, :payload, :st)"""),
            {"id": str(uuid.uuid4()), "aid": str(alert_id), "adt": detected_at,
             "act": action, "tip": _rand_ip(),
             "payload": str(payload).replace("'", '"'),
             "st": status},
        )
    await session.commit()
    print("    mitigation_actions: 30 actions seeded")


async def main() -> None:
    print("=" * 60)
    print(" Adaptive FL DDoS System — Database Seeder")
    print("=" * 60)
    engine = _make_engine()
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await seed(session)
        print("\n✅ Seeding complete. Start the dashboard to verify live data.")
    except Exception as exc:
        print(f"\n❌ Seeding failed: {exc}")
        print("   Ensure Docker DB is running: docker compose -f docker/docker-compose.yml up db -d")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

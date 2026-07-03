"""
scripts/init_db.py
-------------------
Initialises the PostgreSQL database by running Alembic migrations.

This script is the canonical way to create database tables for the
Adaptive FL DDoS Detection system. It runs `alembic upgrade head`
against the configured DATABASE_URL.

Usage:
    python scripts/init_db.py

Prerequisites:
    - PostgreSQL running (locally or via Docker Compose)
    - DATABASE_URL set in .env or environment
    - Virtual environment activated with all dependencies installed

Acceptance Criteria (Milestone 4):
    - `alembic upgrade head` creates all tables defined in docs/Database.md.
    - Includes TimescaleDB hypertable creation for traffic_history, attack_alerts.

Ref: docs/Database.md § 4 (Migration Strategy)
     docs/DevelopmentRoadmap.md — Milestone 4
"""

import os
import sys
import subprocess
from pathlib import Path

# ── Ensure we run from the project root ───────────────────────────────────────
PROJECT_ROOT = Path(__file__).parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> None:
    """Run Alembic migrations to initialise or upgrade the database schema."""
    print("=" * 60)
    print(" Adaptive FL DDoS System — Database Initialisation")
    print("=" * 60)

    # ── Check DATABASE_URL is configured ────────────────────────────────────
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        # Try loading from .env
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        database_url = line.split("=", 1)[1]
                        os.environ["DATABASE_URL"] = database_url
                        break

    if not database_url:
        print(
            "ERROR: DATABASE_URL not set.\n"
            "  Set it in your .env file or as an environment variable.\n"
            "  Example: postgresql://ddos_user:password@localhost:5432/ddos_db",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[OK] DATABASE_URL configured.")

    # ── Check alembic.ini exists ─────────────────────────────────────────────
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    if not alembic_ini.exists():
        print(
            "ERROR: alembic.ini not found.\n"
            "  Run: alembic init alembic  (from project root)",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Run alembic upgrade head ──────────────────────────────────────────────
    print("\nRunning: alembic upgrade head ...\n")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )

    if result.returncode == 0:
        print("\n[OK] Database schema up to date.")
        print("     All tables from docs/Database.md are created.")
    else:
        print(
            f"\nERROR: alembic upgrade failed (exit code {result.returncode}).",
            file=sys.stderr,
        )
        sys.exit(result.returncode)

    print("=" * 60)


if __name__ == "__main__":
    main()

"""
scripts/seed_db.py
-------------------
Injects mock data into the PostgreSQL database for UI testing and development.

Creates:
  - Default admin/analyst/readonly user accounts
  - Sample FL client registrations with trust scores
  - Mock FL round records
  - Sample attack alerts with synthetic SHAP values
  - Sample mitigation action records

Usage:
    python scripts/seed_db.py

Prerequisites:
    - Database initialised via `python scripts/init_db.py`
    - DATABASE_URL configured in .env
    - Virtual environment activated

Ref: docs/Database.md § 2 (Table Definitions)
     docs/DevelopmentRoadmap.md — Milestone 4
"""

import os
import sys
from pathlib import Path

# ── Project root setup ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> None:
    """Seed the database with mock data for development and dashboard testing."""
    print("=" * 60)
    print(" Adaptive FL DDoS System — Database Seeding")
    print("=" * 60)

    # TODO (Milestone 4): Import SQLAlchemy models and session
    # TODO (Milestone 4): Create default roles: ADMIN, ANALYST, READONLY
    # TODO (Milestone 4): Create default admin user (password: change-in-prod)
    # TODO (Milestone 4): Create 3 mock FL clients with trust scores 1.0, 0.8, 0.3
    # TODO (Milestone 4): Create 5 mock FL rounds with accuracy/loss metrics
    # TODO (Milestone 4): Create 10 mock attack alerts with SHAP values
    # TODO (Milestone 4): Create 5 mock mitigation actions (BLOCK_IP, RATE_LIMIT)

    print("\n[NOTICE] Database seeding deferred to Milestone 4.")
    print("         Run this script again after implementing ORM models.")
    print("=" * 60)


if __name__ == "__main__":
    main()

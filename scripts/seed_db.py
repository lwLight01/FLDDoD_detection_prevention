"""scripts/seed_db.py"""

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

    # (Summary comment)
    print("\n[NOTICE] Database seeding deferred to Milestone 4.")
    print("         Run this script again after implementing ORM models.")
    print("=" * 60)


if __name__ == "__main__":
    main()

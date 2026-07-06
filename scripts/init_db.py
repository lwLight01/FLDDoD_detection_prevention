import os
import sys
import subprocess
from pathlib import Path
PROJECT_ROOT = Path(__file__).parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / "src"))
def main() -> None:
    print("=" * 60)
    print(" Adaptive FL DDoS System — Database Initialisation")
    print("=" * 60)
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
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
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    if not alembic_ini.exists():
        print(
            "ERROR: alembic.ini not found.\n"
            "  Run: alembic init alembic  (from project root)",
            file=sys.stderr,
        )
        sys.exit(1)
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

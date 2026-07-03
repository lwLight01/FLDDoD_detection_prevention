"""
tests/integration/test_milestone4_database.py
-----------------------------------------------
Integration tests for Milestone 4: Database Schema (live DB).

Verifies that `alembic upgrade head` has successfully created all 9 tables
and 2 TimescaleDB hypertables in the running PostgreSQL instance.

Requirements:
  - Docker container `ddos_db` must be running.
    Start with: docker compose -f docker/docker-compose.yml up db -d
  - DATABASE_URL must be set in .env or environment.
    Default: postgresql://ddos_user:change_this_password@localhost:5432/ddos_db

Run with:
  pytest tests/integration/test_milestone4_database.py -v -m integration

Acceptance Criteria (Milestone 4):
  - All 9 tables from docs/Database.md exist in the database.
  - traffic_history and attack_alerts are registered as TimescaleDB hypertables.
  - All GIN and B-Tree indexes exist.
  - The alembic_version table confirms migration was applied.

Ref: docs/DevelopmentRoadmap.md — Milestone 4
     docs/Database.md § 2 & § 3
"""

import os
import pytest
from pathlib import Path

# Load .env if present so tests can run standalone
_env_file = Path(__file__).parents[2] / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ddos_user:change_this_password@localhost:5432/ddos_db",
)
# Convert asyncpg URLs to psycopg2 for sync tests
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture(scope="module")
def db_engine():
    """Create a synchronous SQLAlchemy engine for the live DB."""
    sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy required")
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(
            f"Cannot connect to database at {DATABASE_URL}. "
            f"Start it with: docker compose -f docker/docker-compose.yml up db -d\n"
            f"Error: {exc}"
        )
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_conn(db_engine):
    from sqlalchemy import text
    with db_engine.connect() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Migration State
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAlembicMigrationApplied:
    """Verify Alembic has been applied to the database."""

    def test_alembic_version_table_exists(self, db_conn):
        from sqlalchemy import text, inspect
        inspector = inspect(db_conn)
        tables = inspector.get_table_names()
        assert "alembic_version" in tables, \
            "alembic_version table must exist — run: alembic upgrade head"

    def test_migration_version_is_set(self, db_conn):
        from sqlalchemy import text
        result = db_conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        assert len(result) == 1, "Exactly one migration version must be recorded"
        assert result[0][0] == "001_initial_schema", \
            f"Expected migration '001_initial_schema', got '{result[0][0]}'"


# ---------------------------------------------------------------------------
# Table Existence
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAllTablesExist:
    """All 9 schema tables must exist in the public schema."""

    EXPECTED_TABLES = [
        "roles",
        "users",
        "fl_rounds",
        "fl_clients",
        "fl_client_updates",
        "models",
        "traffic_history",
        "attack_alerts",
        "mitigation_actions",
    ]

    @pytest.mark.parametrize("table_name", EXPECTED_TABLES)
    def test_table_exists(self, db_conn, table_name):
        from sqlalchemy import inspect
        inspector = inspect(db_conn)
        tables = inspector.get_table_names(schema="public")
        assert table_name in tables, \
            f"Table '{table_name}' must exist — run: alembic upgrade head"


# ---------------------------------------------------------------------------
# TimescaleDB HyperTables
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestTimescaleHypertables:
    """traffic_history and attack_alerts must be TimescaleDB hypertables."""

    def _get_hypertables(self, db_conn) -> list[str]:
        from sqlalchemy import text
        result = db_conn.execute(
            text("SELECT hypertable_name FROM timescaledb_information.hypertables")
        ).fetchall()
        return [row[0] for row in result]

    def test_traffic_history_is_hypertable(self, db_conn):
        hypertables = self._get_hypertables(db_conn)
        assert "traffic_history" in hypertables, \
            "traffic_history must be a TimescaleDB hypertable"

    def test_attack_alerts_is_hypertable(self, db_conn):
        hypertables = self._get_hypertables(db_conn)
        assert "attack_alerts" in hypertables, \
            "attack_alerts must be a TimescaleDB hypertable"

    def test_exactly_two_hypertables(self, db_conn):
        hypertables = self._get_hypertables(db_conn)
        assert len(hypertables) == 2, \
            f"Expected exactly 2 hypertables, got {len(hypertables)}: {hypertables}"


# ---------------------------------------------------------------------------
# Column Structure
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestTableColumns:
    """Spot-check critical columns exist with correct types."""

    def _col_names(self, db_conn, table: str) -> list[str]:
        from sqlalchemy import inspect
        inspector = inspect(db_conn)
        return [c["name"] for c in inspector.get_columns(table)]

    def test_users_has_required_columns(self, db_conn):
        cols = self._col_names(db_conn, "users")
        for expected in ["id", "username", "password_hash", "email", "role_id", "created_at"]:
            assert expected in cols, f"users table missing column: {expected}"

    def test_fl_rounds_has_required_columns(self, db_conn):
        cols = self._col_names(db_conn, "fl_rounds")
        for expected in ["id", "start_time", "end_time", "global_accuracy", "global_loss", "model_version_tag"]:
            assert expected in cols, f"fl_rounds table missing column: {expected}"

    def test_traffic_history_has_required_columns(self, db_conn):
        cols = self._col_names(db_conn, "traffic_history")
        for expected in ["id", "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "protocol"]:
            assert expected in cols, f"traffic_history table missing column: {expected}"

    def test_attack_alerts_has_shap_values_column(self, db_conn):
        cols = self._col_names(db_conn, "attack_alerts")
        assert "shap_values" in cols, "attack_alerts must have a shap_values JSONB column"

    def test_mitigation_actions_has_sdn_payload_column(self, db_conn):
        cols = self._col_names(db_conn, "mitigation_actions")
        assert "sdn_rule_payload" in cols, \
            "mitigation_actions must have a sdn_rule_payload JSONB column"


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDatabaseIndexes:
    """Verify B-Tree and GIN indexes from docs/Database.md § 3 exist."""

    def _get_index_names(self, db_conn, table: str) -> list[str]:
        from sqlalchemy import text
        result = db_conn.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = :table AND schemaname = 'public'"
            ),
            {"table": table},
        ).fetchall()
        return [row[0] for row in result]

    def test_users_username_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "users")
        assert any("username" in idx for idx in indexes), \
            "users table must have an index on username"

    def test_users_email_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "users")
        assert any("email" in idx for idx in indexes), \
            "users table must have an index on email"

    def test_fl_clients_node_name_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "fl_clients")
        assert any("node_name" in idx for idx in indexes), \
            "fl_clients table must have an index on node_name"

    def test_attack_alerts_shap_gin_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "attack_alerts")
        assert any("shap" in idx or "gin" in idx for idx in indexes), \
            "attack_alerts must have a GIN index on shap_values"

    def test_mitigation_actions_target_ip_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "mitigation_actions")
        assert any("target_ip" in idx for idx in indexes), \
            "mitigation_actions must have an index on target_ip"

    def test_models_partial_active_index_exists(self, db_conn):
        indexes = self._get_index_names(db_conn, "models")
        assert any("active" in idx for idx in indexes), \
            "models table must have a partial unique index for is_active"


# ---------------------------------------------------------------------------
# Basic Write/Read (Smoke Test)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestBasicCRUD:
    """Verify tables accept and return data correctly."""

    def test_can_insert_and_read_role(self, db_conn):
        from sqlalchemy import text
        import uuid

        role_id = str(uuid.uuid4())
        role_name = f"TEST_ROLE_{uuid.uuid4().hex[:6].upper()}"

        db_conn.execute(
            text("INSERT INTO roles (id, name) VALUES (:id, :name)"),
            {"id": role_id, "name": role_name},
        )
        db_conn.commit()

        result = db_conn.execute(
            text("SELECT name FROM roles WHERE id = :id"),
            {"id": role_id},
        ).fetchone()

        assert result is not None
        assert result[0] == role_name

        # Cleanup
        db_conn.execute(text("DELETE FROM roles WHERE id = :id"), {"id": role_id})
        db_conn.commit()

    def test_traffic_history_autoincrement_id(self, db_conn):
        """Verify BIGSERIAL auto-increment works on the hypertable."""
        from sqlalchemy import text
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc)
        db_conn.execute(
            text("""
                INSERT INTO traffic_history
                    (timestamp, src_ip, dst_ip, src_port, dst_port, protocol)
                VALUES (:ts, '10.0.0.1', '10.0.0.2', 12345, 80, 'TCP')
            """),
            {"ts": ts},
        )
        db_conn.commit()

        result = db_conn.execute(
            text("SELECT id FROM traffic_history WHERE timestamp = :ts"),
            {"ts": ts},
        ).fetchone()

        assert result is not None
        assert result[0] > 0, "BIGSERIAL id must be auto-assigned and > 0"

        # Cleanup
        db_conn.execute(
            text("DELETE FROM traffic_history WHERE timestamp = :ts"), {"ts": ts}
        )
        db_conn.commit()

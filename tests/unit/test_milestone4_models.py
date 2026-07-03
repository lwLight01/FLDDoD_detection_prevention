"""
tests/unit/test_milestone4_models.py
--------------------------------------
Unit tests for Milestone 4: Database Schema (ORM models).

Validates that all SQLAlchemy ORM models are correctly defined —
importable, have the right table names, columns, primary keys,
and relationships — WITHOUT requiring a live database connection.

Acceptance Criteria (Milestone 4):
  - All 9 ORM model classes are importable with no errors.
  - Each model has the correct __tablename__.
  - Primary keys, nullable constraints, and relationships are correct.
  - TimescaleDB HyperTable models have composite PKs.
  - Alembic migration file exists and contains all 9 table definitions.

Ref: docs/DevelopmentRoadmap.md — Milestone 4
     docs/Database.md § 2 (Table Definitions)
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# ORM Import & Table Name Tests
# ---------------------------------------------------------------------------


class TestORMModelsImportable:
    """All 9 ORM models must be importable without errors."""

    def test_base_importable(self):
        from mitigation_engine.db.models import Base

        assert Base is not None

    def test_role_model_importable(self):
        from mitigation_engine.db.models import Role

        assert Role.__tablename__ == "roles"

    def test_user_model_importable(self):
        from mitigation_engine.db.models import User

        assert User.__tablename__ == "users"

    def test_fl_round_model_importable(self):
        from mitigation_engine.db.models import FLRound

        assert FLRound.__tablename__ == "fl_rounds"

    def test_fl_client_model_importable(self):
        from mitigation_engine.db.models import FLClient

        assert FLClient.__tablename__ == "fl_clients"

    def test_fl_client_update_model_importable(self):
        from mitigation_engine.db.models import FLClientUpdate

        assert FLClientUpdate.__tablename__ == "fl_client_updates"

    def test_model_version_importable(self):
        from mitigation_engine.db.models import ModelVersion

        assert ModelVersion.__tablename__ == "models"

    def test_traffic_history_importable(self):
        from mitigation_engine.db.models import TrafficHistory

        assert TrafficHistory.__tablename__ == "traffic_history"

    def test_attack_alert_importable(self):
        from mitigation_engine.db.models import AttackAlert

        assert AttackAlert.__tablename__ == "attack_alerts"

    def test_mitigation_action_importable(self):
        from mitigation_engine.db.models import MitigationAction

        assert MitigationAction.__tablename__ == "mitigation_actions"


# ---------------------------------------------------------------------------
# Column & Primary Key Tests
# ---------------------------------------------------------------------------


class TestORMPrimaryKeys:
    """Each model must declare the correct primary key columns."""

    def _pk_cols(self, model_class) -> list[str]:
        return [col.name for col in model_class.__table__.primary_key.columns]

    def test_roles_pk_is_id(self):
        from mitigation_engine.db.models import Role

        assert self._pk_cols(Role) == ["id"]

    def test_users_pk_is_id(self):
        from mitigation_engine.db.models import User

        assert self._pk_cols(User) == ["id"]

    def test_fl_rounds_pk_is_id(self):
        from mitigation_engine.db.models import FLRound

        assert self._pk_cols(FLRound) == ["id"]

    def test_fl_clients_pk_is_id(self):
        from mitigation_engine.db.models import FLClient

        assert self._pk_cols(FLClient) == ["id"]

    def test_fl_client_updates_pk_is_id(self):
        from mitigation_engine.db.models import FLClientUpdate

        assert self._pk_cols(FLClientUpdate) == ["id"]

    def test_model_version_pk_is_id(self):
        from mitigation_engine.db.models import ModelVersion

        assert self._pk_cols(ModelVersion) == ["id"]

    def test_traffic_history_has_composite_pk(self):
        """TimescaleDB requires (id, timestamp) composite PK."""
        from mitigation_engine.db.models import TrafficHistory

        pks = self._pk_cols(TrafficHistory)
        assert "id" in pks
        assert "timestamp" in pks
        assert len(pks) == 2, "traffic_history must have exactly 2 PK columns"

    def test_attack_alerts_has_composite_pk(self):
        """TimescaleDB requires (id, detected_at) composite PK."""
        from mitigation_engine.db.models import AttackAlert

        pks = self._pk_cols(AttackAlert)
        assert "id" in pks
        assert "detected_at" in pks
        assert len(pks) == 2, "attack_alerts must have exactly 2 PK columns"

    def test_mitigation_actions_pk_is_id(self):
        from mitigation_engine.db.models import MitigationAction

        assert self._pk_cols(MitigationAction) == ["id"]


class TestORMColumnConstraints:
    """Verify key nullable and type constraints on ORM models."""

    def _col(self, model_class, col_name):
        return model_class.__table__.c[col_name]

    def test_user_username_not_nullable(self):
        from mitigation_engine.db.models import User

        assert not self._col(User, "username").nullable

    def test_user_email_not_nullable(self):
        from mitigation_engine.db.models import User

        assert not self._col(User, "email").nullable

    def test_user_role_id_is_nullable(self):
        from mitigation_engine.db.models import User

        assert self._col(User, "role_id").nullable

    def test_fl_client_trust_score_has_default(self):
        from mitigation_engine.db.models import FLClient

        col = self._col(FLClient, "current_trust_score")
        assert col.server_default is not None or col.default is not None

    def test_traffic_history_id_is_bigint(self):
        from sqlalchemy import BigInteger

        from mitigation_engine.db.models import TrafficHistory

        col = self._col(TrafficHistory, "id")
        assert isinstance(col.type, BigInteger)

    def test_attack_alert_shap_values_not_nullable(self):
        from mitigation_engine.db.models import AttackAlert

        assert not self._col(AttackAlert, "shap_values").nullable

    def test_mitigation_action_status_not_nullable(self):
        from mitigation_engine.db.models import MitigationAction

        assert not self._col(MitigationAction, "status").nullable


# ---------------------------------------------------------------------------
# Relationship Tests
# ---------------------------------------------------------------------------


class TestORMRelationships:
    """Verify ORM relationships are correctly declared."""

    def test_role_has_users_relationship(self):
        from mitigation_engine.db.models import Role

        assert hasattr(Role, "users")

    def test_user_has_role_relationship(self):
        from mitigation_engine.db.models import User

        assert hasattr(User, "role")

    def test_fl_round_has_client_updates_relationship(self):
        from mitigation_engine.db.models import FLRound

        assert hasattr(FLRound, "client_updates")

    def test_fl_client_has_updates_relationship(self):
        from mitigation_engine.db.models import FLClient

        assert hasattr(FLClient, "updates")

    def test_fl_client_has_alerts_relationship(self):
        from mitigation_engine.db.models import FLClient

        assert hasattr(FLClient, "alerts")

    def test_attack_alert_has_mitigation_action_relationship(self):
        from mitigation_engine.db.models import AttackAlert

        assert hasattr(AttackAlert, "mitigation_action")

    def test_mitigation_action_has_alert_relationship(self):
        from mitigation_engine.db.models import MitigationAction

        assert hasattr(MitigationAction, "alert")


# ---------------------------------------------------------------------------
# Alembic Migration File Tests
# ---------------------------------------------------------------------------


class TestAlembicMigration:
    """Verify the initial migration script is correct and complete."""

    def _migration_content(self) -> str:
        versions_dir = PROJECT_ROOT / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*initial_schema*.py"))
        assert len(migration_files) == 1, "Exactly one initial schema migration file must exist"
        return migration_files[0].read_text(encoding="utf-8")

    def test_migration_file_exists(self):
        versions_dir = PROJECT_ROOT / "alembic" / "versions"
        assert any(
            versions_dir.glob("*initial_schema*.py")
        ), "Initial schema migration file must exist in alembic/versions/"

    def test_migration_creates_all_9_tables(self):
        content = self._migration_content()
        expected_tables = [
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
        for table in expected_tables:
            assert table in content, f"Migration must reference table '{table}'"

    def test_migration_enables_timescaledb_extension(self):
        content = self._migration_content()
        assert "timescaledb" in content.lower(), "Migration must enable the timescaledb extension"

    def test_migration_enables_uuid_ossp_extension(self):
        content = self._migration_content()
        assert "uuid-ossp" in content, "Migration must enable the uuid-ossp extension"

    def test_migration_creates_hypertable_for_traffic_history(self):
        content = self._migration_content()
        assert (
            "create_hypertable" in content and "traffic_history" in content
        ), "Migration must convert traffic_history to a TimescaleDB hypertable"

    def test_migration_creates_hypertable_for_attack_alerts(self):
        content = self._migration_content()
        assert (
            "create_hypertable" in content and "attack_alerts" in content
        ), "Migration must convert attack_alerts to a TimescaleDB hypertable"

    def test_migration_has_downgrade_function(self):
        content = self._migration_content()
        assert "def downgrade" in content, "Migration must implement a downgrade() function"

    def test_migration_has_upgrade_function(self):
        content = self._migration_content()
        assert "def upgrade" in content, "Migration must implement an upgrade() function"

    def test_alembic_ini_exists(self):
        assert (PROJECT_ROOT / "alembic.ini").exists()

    def test_alembic_env_py_exists(self):
        assert (PROJECT_ROOT / "alembic" / "env.py").exists()

"""
alembic/versions/20240101_0000_initial_schema.py
--------------------------------------------------
Initial database schema migration.

Creates all 9 tables defined in docs/Database.md:
  - roles, users (identity/RBAC)
  - fl_rounds, fl_clients, fl_client_updates (FL state)
  - models (model version registry)
  - traffic_history (TimescaleDB HyperTable, partitioned on timestamp)
  - attack_alerts (TimescaleDB HyperTable, partitioned on detected_at)
  - mitigation_actions (SDN operations log)

TimescaleDB hypertables require the timescaledb extension, which is
pre-installed in the `timescale/timescaledb:latest-pg16` Docker image.

Ref: docs/Database.md § 2 (Table Definitions & Constraints)
     docs/DevelopmentRoadmap.md — Milestone 4
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── Enable required PostgreSQL extensions ──────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    # TimescaleDB must be pre-installed in the PostgreSQL image.
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # ── roles ──────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", name="fk_users_role_id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── fl_rounds ──────────────────────────────────────────────────────────────
    op.create_table(
        "fl_rounds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("global_accuracy", sa.Float(), nullable=True),
        sa.Column("global_loss", sa.Float(), nullable=True),
        sa.Column("model_version_tag", sa.String(100), nullable=False),
    )

    # ── fl_clients ─────────────────────────────────────────────────────────────
    op.create_table(
        "fl_clients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=False),
        sa.Column("node_name", sa.String(100), nullable=False),
        sa.Column(
            "current_trust_score",
            sa.Float(),
            server_default=sa.text("1.0"),
            nullable=False,
        ),
        sa.Column(
            "is_banned",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.UniqueConstraint("node_name", name="uq_fl_clients_node_name"),
    )
    op.create_index("ix_fl_clients_node_name", "fl_clients", ["node_name"])

    # ── fl_client_updates ──────────────────────────────────────────────────────
    op.create_table(
        "fl_client_updates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "round_id",
            sa.Integer(),
            sa.ForeignKey("fl_rounds.id", ondelete="CASCADE", name="fk_fl_client_updates_round_id"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fl_clients.id", name="fk_fl_client_updates_client_id"),
            nullable=False,
        ),
        sa.Column(
            "submitted_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("cosine_similarity", sa.Float(), nullable=False),
        sa.Column("assigned_trust_weight", sa.Float(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
    )

    # ── models ─────────────────────────────────────────────────────────────────
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version_tag", sa.String(100), nullable=False),
        sa.Column(
            "deployed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("weights_file_path", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.UniqueConstraint("version_tag", name="uq_models_version_tag"),
    )
    # Partial unique index: only one model can be active at a time
    op.execute(
        "CREATE UNIQUE INDEX uq_models_active ON models (is_active) WHERE is_active = TRUE"
    )

    # ── traffic_history (TimescaleDB HyperTable) ───────────────────────────────
    # BIGSERIAL for auto-incrementing id; composite PK (id, timestamp) required
    # by TimescaleDB so the partition key (timestamp) is part of the PK.
    op.execute("""
        CREATE TABLE traffic_history (
            id          BIGSERIAL       NOT NULL,
            timestamp   TIMESTAMPTZ     NOT NULL,
            src_ip      INET            NOT NULL,
            dst_ip      INET            NOT NULL,
            src_port    INTEGER         NOT NULL,
            dst_port    INTEGER         NOT NULL,
            protocol    VARCHAR(10)     NOT NULL,
            flow_duration FLOAT,
            total_fwd_packets BIGINT,
            total_bwd_packets BIGINT,
            PRIMARY KEY (id, timestamp)
        )
    """)
    op.execute("SELECT create_hypertable('traffic_history', 'timestamp')")

    # ── attack_alerts (TimescaleDB HyperTable) ─────────────────────────────────
    # Composite PK (id, detected_at) required by TimescaleDB.
    op.execute("""
        CREATE TABLE attack_alerts (
            id                      UUID            NOT NULL DEFAULT uuid_generate_v4(),
            detected_at             TIMESTAMPTZ     NOT NULL,
            flow_id                 BIGINT,
            flow_timestamp          TIMESTAMPTZ,
            client_id               UUID            REFERENCES fl_clients(id),
            prediction_probability  FLOAT           NOT NULL,
            shap_values             JSONB           NOT NULL,
            severity_level          VARCHAR(20)     NOT NULL,
            PRIMARY KEY (id, detected_at)
        )
    """)
    op.execute("SELECT create_hypertable('attack_alerts', 'detected_at')")
    # GIN index for fast JSONB queries on SHAP values
    op.execute(
        "CREATE INDEX ix_attack_alerts_shap_gin ON attack_alerts USING GIN (shap_values)"
    )

    # ── mitigation_actions ─────────────────────────────────────────────────────
    # Composite FK (alert_id, alert_detected_at) -> attack_alerts (id, detected_at)
    op.execute("""
        CREATE TABLE mitigation_actions (
            id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
            alert_id            UUID            NOT NULL,
            alert_detected_at   TIMESTAMPTZ     NOT NULL,
            executed_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            action_type         VARCHAR(50)     NOT NULL,
            target_ip           INET            NOT NULL,
            sdn_rule_payload    JSONB           NOT NULL,
            status              VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
            CONSTRAINT fk_mitigation_alert
                FOREIGN KEY (alert_id, alert_detected_at)
                REFERENCES attack_alerts(id, detected_at)
        )
    """)
    op.execute(
        "CREATE INDEX ix_mitigation_actions_target_ip ON mitigation_actions (target_ip)"
    )
    op.execute(
        "CREATE INDEX ix_mitigation_actions_sdn_gin "
        "ON mitigation_actions USING GIN (sdn_rule_payload)"
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP TABLE IF EXISTS mitigation_actions")
    op.execute("DROP TABLE IF EXISTS attack_alerts")
    op.execute("DROP TABLE IF EXISTS traffic_history")
    op.drop_table("models")
    op.drop_table("fl_client_updates")
    op.drop_table("fl_clients")
    op.drop_table("fl_rounds")
    op.drop_table("users")
    op.drop_table("roles")

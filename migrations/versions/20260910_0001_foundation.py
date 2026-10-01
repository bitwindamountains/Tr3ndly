"""Create source ingestion and decision foundation.

Revision ID: 20260910_0001
Revises:
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_configs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("access_method", sa.String(80), nullable=False),
        sa.Column("terms_url", sa.String(2048), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_configs"),
        sa.UniqueConstraint("slug", name="uq_source_configs_slug"),
    )
    op.create_index("ix_source_configs_slug", "source_configs", ["slug"])

    op.create_table(
        "source_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("running", "succeeded", "failed", name="sourcerunstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor", sa.String(512), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source_configs.id"],
            name="fk_source_runs_source_id_source_configs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_runs"),
    )

    op.create_table(
        "raw_signals",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("source_run_id", sa.String(36), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=True),
        sa.Column("canonical_url", sa.String(2048), nullable=True),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("permitted_summary", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["source_configs.id"], name="fk_raw_signals_source_id_source_configs"
        ),
        sa.ForeignKeyConstraint(
            ["source_run_id"], ["source_runs.id"], name="fk_raw_signals_source_run_id_source_runs"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_raw_signals"),
        sa.UniqueConstraint("content_hash", name="uq_raw_signals_content_hash"),
    )
    op.create_index("ix_raw_signals_content_hash", "raw_signals", ["content_hash"])
    op.create_index("ix_raw_signals_source_observed", "raw_signals", ["source_id", "observed_at"])

    op.create_table(
        "decision_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "accepted",
                "rejected",
                "deferred",
                "insufficient_evidence",
                name="decisiontype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("reason_code", sa.String(120), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("score_version", sa.String(80), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_decision_events"),
    )
    op.create_index("ix_decision_events_opportunity_id", "decision_events", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_decision_events_opportunity_id", table_name="decision_events")
    op.drop_table("decision_events")
    op.drop_index("ix_raw_signals_source_observed", table_name="raw_signals")
    op.drop_index("ix_raw_signals_content_hash", table_name="raw_signals")
    op.drop_table("raw_signals")
    op.drop_table("source_runs")
    op.drop_index("ix_source_configs_slug", table_name="source_configs")
    op.drop_table("source_configs")

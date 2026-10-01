"""Add event clusters, per-source signal dedupe, and replayable score components.

Revision ID: 20261002_0003
Revises: 20260910_0002
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0003"
down_revision: str | None = "20260910_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The model declares a unique index on slug; 0001 created a constraint plus a plain index.
    with op.batch_alter_table("source_configs") as batch:
        batch.drop_constraint("uq_source_configs_slug", type_="unique")
        batch.drop_index("ix_source_configs_slug")
        batch.create_index("ix_source_configs_slug", ["slug"], unique=True)

    # Exact dedupe is per source: the same forecast fetched twice must not be stored twice.
    with op.batch_alter_table("raw_signals") as batch:
        batch.create_unique_constraint(
            "uq_raw_signals_source_content_hash", ["source_id", "content_hash"]
        )

    op.create_table(
        "event_clusters",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("dedupe_key", sa.String(240), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("location", sa.String(160), nullable=False),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("consumer_needs", sa.JSON(), nullable=False),
        sa.Column(
            "sensitivity",
            sa.Enum(
                "none", "low", "medium", "high", "blocked", name="sensitivity", native_enum=False
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("timely_score", sa.Integer(), nullable=False),
        sa.Column("rule_version", sa.String(80), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "expired", name="eventstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 100", name="ck_event_clusters_confidence_range"
        ),
        sa.CheckConstraint(
            "timely_score BETWEEN 0 AND 100", name="ck_event_clusters_timely_score_range"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["source_configs.id"], name="fk_event_clusters_source_id_source_configs"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_event_clusters"),
    )
    op.create_index("ix_event_clusters_expires_at", "event_clusters", ["expires_at"])
    op.create_index("ix_event_clusters_dedupe_status", "event_clusters", ["dedupe_key", "status"])

    op.create_table(
        "event_cluster_members",
        sa.Column("cluster_id", sa.String(36), nullable=False),
        sa.Column("raw_signal_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(
            ["cluster_id"],
            ["event_clusters.id"],
            name="fk_event_cluster_members_cluster_id_event_clusters",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_signal_id"],
            ["raw_signals.id"],
            name="fk_event_cluster_members_raw_signal_id_raw_signals",
        ),
        sa.PrimaryKeyConstraint("cluster_id", "raw_signal_id", name="pk_event_cluster_members"),
    )

    with op.batch_alter_table("opportunities") as batch:
        batch.add_column(sa.Column("event_cluster_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("concept_key", sa.String(120), nullable=True))
        batch.create_foreign_key(
            "fk_opportunities_event_cluster_id_event_clusters",
            "event_clusters",
            ["event_cluster_id"],
            ["id"],
        )
        batch.create_index("ix_opportunities_event_cluster_id", ["event_cluster_id"])
        batch.create_unique_constraint(
            "uq_opportunities_event_cluster_concept", ["event_cluster_id", "concept_key"]
        )

    with op.batch_alter_table("opportunity_evidence") as batch:
        batch.add_column(sa.Column("raw_signal_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_opportunity_evidence_raw_signal_id_raw_signals",
            "raw_signals",
            ["raw_signal_id"],
            ["id"],
        )

    with op.batch_alter_table("score_snapshots") as batch:
        batch.add_column(sa.Column("timely_score", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("trend_score", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("components", sa.JSON(), nullable=True))
        batch.create_check_constraint(
            "ck_score_snapshots_timely_range", "timely_score BETWEEN 0 AND 100"
        )
        batch.create_check_constraint(
            "ck_score_snapshots_trend_range", "trend_score BETWEEN 0 AND 100"
        )


def downgrade() -> None:
    with op.batch_alter_table("score_snapshots") as batch:
        batch.drop_constraint("ck_score_snapshots_trend_range", type_="check")
        batch.drop_constraint("ck_score_snapshots_timely_range", type_="check")
        batch.drop_column("components")
        batch.drop_column("trend_score")
        batch.drop_column("timely_score")

    with op.batch_alter_table("opportunity_evidence") as batch:
        batch.drop_constraint(
            "fk_opportunity_evidence_raw_signal_id_raw_signals", type_="foreignkey"
        )
        batch.drop_column("raw_signal_id")

    with op.batch_alter_table("opportunities") as batch:
        batch.drop_constraint("uq_opportunities_event_cluster_concept", type_="unique")
        batch.drop_index("ix_opportunities_event_cluster_id")
        batch.drop_constraint(
            "fk_opportunities_event_cluster_id_event_clusters", type_="foreignkey"
        )
        batch.drop_column("concept_key")
        batch.drop_column("event_cluster_id")

    op.drop_table("event_cluster_members")
    op.drop_index("ix_event_clusters_dedupe_status", table_name="event_clusters")
    op.drop_index("ix_event_clusters_expires_at", table_name="event_clusters")
    op.drop_table("event_clusters")

    with op.batch_alter_table("raw_signals") as batch:
        batch.drop_constraint("uq_raw_signals_source_content_hash", type_="unique")

    with op.batch_alter_table("source_configs") as batch:
        batch.drop_index("ix_source_configs_slug")
        batch.create_index("ix_source_configs_slug", ["slug"])
        batch.create_unique_constraint("uq_source_configs_slug", ["slug"])

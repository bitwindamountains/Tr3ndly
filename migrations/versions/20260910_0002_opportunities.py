"""Add auditable opportunities, evidence, and score snapshots.

Revision ID: 20260910_0002
Revises: 20260910_0001
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0002"
down_revision: str | None = "20260910_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("raw_signals") as batch:
        batch.drop_constraint("uq_raw_signals_content_hash", type_="unique")

    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("product_concept", sa.String(240), nullable=False),
        sa.Column("category", sa.String(160), nullable=False),
        sa.Column(
            "reason_type",
            sa.Enum("timely", "trend", "both", name="opportunityreason", native_enum=False),
            nullable=False,
        ),
        sa.Column("why_now", sa.Text(), nullable=False),
        sa.Column("target_user", sa.String(240), nullable=False),
        sa.Column("location", sa.String(160), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "eligible",
                "accepted",
                "rejected",
                "deferred",
                "matched",
                "expired",
                name="opportunitystatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("search_queries", sa.JSON(), nullable=False),
        sa.Column("uncertainties", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opportunities"),
    )
    op.create_index("ix_opportunities_expires_at", "opportunities", ["expires_at"])

    op.create_table(
        "opportunity_evidence",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column("source_name", sa.String(160), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name="fk_opportunity_evidence_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opportunity_evidence"),
    )
    op.create_index(
        "ix_opportunity_evidence_opportunity_id",
        "opportunity_evidence",
        ["opportunity_id"],
    )

    op.create_table(
        "score_snapshots",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column("demand", sa.Integer(), nullable=False),
        sa.Column("execution", sa.Integer(), nullable=False),
        sa.Column("marketplace_fit_prior", sa.Integer(), nullable=False),
        sa.Column("uncertainty_penalty", sa.Integer(), nullable=False),
        sa.Column("discovery_priority", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("demand BETWEEN 0 AND 100", name="ck_score_snapshots_demand_range"),
        sa.CheckConstraint(
            "execution BETWEEN 0 AND 100", name="ck_score_snapshots_execution_range"
        ),
        sa.CheckConstraint(
            "marketplace_fit_prior BETWEEN 0 AND 100",
            name="ck_score_snapshots_marketplace_fit_range",
        ),
        sa.CheckConstraint(
            "uncertainty_penalty BETWEEN 0 AND 100",
            name="ck_score_snapshots_uncertainty_range",
        ),
        sa.CheckConstraint(
            "discovery_priority BETWEEN 0 AND 100",
            name="ck_score_snapshots_priority_range",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name="fk_score_snapshots_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_score_snapshots"),
    )
    op.create_index("ix_score_snapshots_opportunity_id", "score_snapshots", ["opportunity_id"])

    with op.batch_alter_table("decision_events") as batch:
        batch.create_foreign_key(
            "fk_decision_events_opportunity_id_opportunities",
            "opportunities",
            ["opportunity_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("decision_events") as batch:
        batch.drop_constraint("fk_decision_events_opportunity_id_opportunities", type_="foreignkey")
    op.drop_index("ix_score_snapshots_opportunity_id", table_name="score_snapshots")
    op.drop_table("score_snapshots")
    op.drop_index("ix_opportunity_evidence_opportunity_id", table_name="opportunity_evidence")
    op.drop_table("opportunity_evidence")
    op.drop_index("ix_opportunities_expires_at", table_name="opportunities")
    op.drop_table("opportunities")
    with op.batch_alter_table("raw_signals") as batch:
        batch.create_unique_constraint("uq_raw_signals_content_hash", ["content_hash"])

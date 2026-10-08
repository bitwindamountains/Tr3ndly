"""Add product matches, search failures, creative briefs and variants, and imported results.

Revision ID: 20261008_0004
Revises: 20261002_0003
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261008_0004"
down_revision: str | None = "20261002_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _id() -> sa.Column[str]:
    return sa.Column("id", sa.String(36), nullable=False)


def _created_at() -> sa.Column[sa.DateTime]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    with op.batch_alter_table("score_snapshots") as batch:
        batch.add_column(sa.Column("listing_economics", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("publish_priority", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "ck_score_snapshots_economics_range", "listing_economics BETWEEN 0 AND 100"
        )
        batch.create_check_constraint(
            "ck_score_snapshots_publish_range", "publish_priority BETWEEN 0 AND 100"
        )

    op.create_table(
        "product_matches",
        _id(),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column("marketplace", sa.String(40), nullable=False),
        sa.Column("product_url", sa.String(2048), nullable=False),
        sa.Column("affiliate_url", sa.String(2048), nullable=False),
        sa.Column("listing_title", sa.String(500), nullable=False),
        sa.Column("seller_name", sa.String(240), nullable=True),
        sa.Column("seller_type", sa.String(40), nullable=True),
        sa.Column("price_centavos", sa.Integer(), nullable=False),
        sa.Column("commission_rate_bps", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("sold_count", sa.Integer(), nullable=True),
        sa.Column("in_stock", sa.Boolean(), nullable=False),
        sa.Column("shipping_note", sa.Text(), nullable=True),
        sa.Column("verified_facts", sa.JSON(), nullable=False),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("image_usage_note", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "candidate", "confirmed", "stale", name="productmatchstatus", native_enum=False
            ),
            nullable=False,
        ),
        sa.Column("eligibility_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.CheckConstraint("price_centavos > 0", name="ck_product_matches_price_positive"),
        sa.CheckConstraint(
            "commission_rate_bps BETWEEN 0 AND 10000", name="ck_product_matches_commission_range"
        ),
        sa.CheckConstraint("rating BETWEEN 0 AND 50", name="ck_product_matches_rating_range"),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name="fk_product_matches_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_product_matches"),
    )
    op.create_index("ix_product_matches_opportunity_id", "product_matches", ["opportunity_id"])

    op.create_table(
        "listing_search_failures",
        _id(),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column("marketplace", sa.String(40), nullable=False),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name="fk_listing_search_failures_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_listing_search_failures"),
    )
    op.create_index(
        "ix_listing_search_failures_opportunity_id", "listing_search_failures", ["opportunity_id"]
    )

    op.create_table(
        "creative_briefs",
        _id(),
        sa.Column("product_match_id", sa.String(36), nullable=False),
        sa.Column("platform", sa.String(40), nullable=False),
        sa.Column("audience", sa.String(240), nullable=False),
        sa.Column("angle", sa.Text(), nullable=False),
        sa.Column("verified_facts", sa.JSON(), nullable=False),
        sa.Column("forbidden_claims", sa.JSON(), nullable=False),
        sa.Column("disclosure", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("experiment_label", sa.String(120), nullable=True),
        sa.Column("version", sa.String(40), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["product_match_id"],
            ["product_matches.id"],
            name="fk_creative_briefs_product_match_id_product_matches",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_creative_briefs"),
    )
    op.create_index("ix_creative_briefs_product_match_id", "creative_briefs", ["product_match_id"])

    op.create_table(
        "creative_variants",
        _id(),
        sa.Column("brief_id", sa.String(36), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("hook_type", sa.String(40), nullable=False),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("generator", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=True),
        sa.Column("generation", sa.JSON(), nullable=True),
        sa.Column("policy_issues", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "needs_review",
                "approved",
                "rejected",
                "exported",
                name="creativestatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("tracking_code", sa.String(40), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["brief_id"],
            ["creative_briefs.id"],
            name="fk_creative_variants_brief_id_creative_briefs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["creative_variants.id"],
            name="fk_creative_variants_parent_id_creative_variants",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_creative_variants"),
        sa.UniqueConstraint("tracking_code", name="uq_creative_variants_tracking_code"),
    )
    op.create_index("ix_creative_variants_brief_id", "creative_variants", ["brief_id"])

    op.create_table(
        "creative_reviews",
        _id(),
        sa.Column("variant_id", sa.String(36), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("approved", "rejected", name="reviewdecision", native_enum=False),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["creative_variants.id"],
            name="fk_creative_reviews_variant_id_creative_variants",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_creative_reviews"),
    )
    op.create_index("ix_creative_reviews_variant_id", "creative_reviews", ["variant_id"])

    op.create_table(
        "metric_observations",
        _id(),
        sa.Column("tracking_code", sa.String(80), nullable=False),
        sa.Column("variant_id", sa.String(36), nullable=True),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=True),
        sa.Column("orders", sa.Integer(), nullable=True),
        sa.Column("gmv_centavos", sa.Integer(), nullable=True),
        sa.Column("commission_centavos", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("import_batch", sa.String(36), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["creative_variants.id"],
            name="fk_metric_observations_variant_id_creative_variants",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metric_observations"),
    )
    op.create_index(
        "ix_metric_observations_code_day", "metric_observations", ["tracking_code", "observed_on"]
    )
    op.create_index("ix_metric_observations_variant_id", "metric_observations", ["variant_id"])


def downgrade() -> None:
    op.drop_index("ix_metric_observations_variant_id", table_name="metric_observations")
    op.drop_index("ix_metric_observations_code_day", table_name="metric_observations")
    op.drop_table("metric_observations")
    op.drop_index("ix_creative_reviews_variant_id", table_name="creative_reviews")
    op.drop_table("creative_reviews")
    op.drop_index("ix_creative_variants_brief_id", table_name="creative_variants")
    op.drop_table("creative_variants")
    op.drop_index("ix_creative_briefs_product_match_id", table_name="creative_briefs")
    op.drop_table("creative_briefs")
    op.drop_index("ix_listing_search_failures_opportunity_id", table_name="listing_search_failures")
    op.drop_table("listing_search_failures")
    op.drop_index("ix_product_matches_opportunity_id", table_name="product_matches")
    op.drop_table("product_matches")

    with op.batch_alter_table("score_snapshots") as batch:
        batch.drop_constraint("ck_score_snapshots_publish_range", type_="check")
        batch.drop_constraint("ck_score_snapshots_economics_range", type_="check")
        batch.drop_column("publish_priority")
        batch.drop_column("listing_economics")

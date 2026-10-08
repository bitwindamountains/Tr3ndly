import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tr3ndly.db.base import Base
from tr3ndly.db.types import UTCDateTime, utcnow


def new_id() -> str:
    return str(uuid.uuid4())


def created_at_column() -> Mapped[datetime]:
    # Python-side default keeps microsecond precision; SQLite's CURRENT_TIMESTAMP is per second.
    return mapped_column(UTCDateTime(), default=utcnow, server_default=func.now())


class SourceRunStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DecisionType(enum.StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class OpportunityStatus(enum.StrEnum):
    ELIGIBLE = "eligible"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    MATCHED = "matched"
    EXPIRED = "expired"


class OpportunityReason(enum.StrEnum):
    TIMELY = "timely"
    TREND = "trend"
    BOTH = "both"


class EventStatus(enum.StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"


class ProductMatchStatus(enum.StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    # Replaced by a newer confirmed listing for the same opportunity.
    STALE = "stale"


class CreativeStatus(enum.StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPORTED = "exported"


class ReviewDecision(enum.StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class Sensitivity(enum.StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


def enum_values(enum_type: type[enum.Enum]) -> list[str]:
    return [str(member.value) for member in enum_type]


def enum_column(enum_type: type[enum.Enum]) -> Enum:
    return Enum(enum_type, native_enum=False, values_callable=enum_values)


class SourceConfig(Base):
    __tablename__ = "source_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    access_method: Mapped[str] = mapped_column(String(80))
    terms_url: Mapped[str | None] = mapped_column(String(2048))
    enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = created_at_column()

    runs: Mapped[list["SourceRun"]] = relationship(back_populates="source")


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id", ondelete="CASCADE"))
    status: Mapped[SourceRunStatus] = mapped_column(
        enum_column(SourceRunStatus), default=SourceRunStatus.RUNNING
    )
    started_at: Mapped[datetime] = created_at_column()
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    cursor: Mapped[str | None] = mapped_column(String(512))
    error: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    source: Mapped[SourceConfig] = relationship(back_populates="runs")
    signals: Mapped[list["RawSignal"]] = relationship(back_populates="source_run")


class RawSignal(Base):
    __tablename__ = "raw_signals"
    __table_args__ = (
        Index("ix_raw_signals_source_observed", "source_id", "observed_at"),
        UniqueConstraint("source_id", "content_hash", name="uq_raw_signals_source_content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id"))
    source_run_id: Mapped[str] = mapped_column(ForeignKey("source_runs.id"))
    external_id: Mapped[str | None] = mapped_column(String(512))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(1000))
    permitted_summary: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime())
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = created_at_column()

    source_run: Mapped[SourceRun] = relationship(back_populates="signals")


class EventCluster(Base):
    """A detected real-world condition, such as heat in Metro Manila, that may create needs."""

    __tablename__ = "event_clusters"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 100", name="confidence_range"),
        CheckConstraint("timely_score BETWEEN 0 AND 100", name="timely_score_range"),
        Index("ix_event_clusters_dedupe_status", "dedupe_key", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id"))
    dedupe_key: Mapped[str] = mapped_column(String(240))
    event_type: Mapped[str] = mapped_column(String(80))
    location: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(1000))
    summary: Mapped[str] = mapped_column(Text)
    consumer_needs: Mapped[list[str]] = mapped_column(JSON, default=list)
    sensitivity: Mapped[Sensitivity] = mapped_column(enum_column(Sensitivity))
    confidence: Mapped[int] = mapped_column(Integer)
    timely_score: Mapped[int] = mapped_column(Integer)
    rule_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[EventStatus] = mapped_column(
        enum_column(EventStatus), default=EventStatus.ACTIVE
    )
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime())
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(UTCDateTime())
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime())

    members: Mapped[list["EventClusterMember"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="event_cluster")


class EventClusterMember(Base):
    __tablename__ = "event_cluster_members"

    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("event_clusters.id", ondelete="CASCADE"), primary_key=True
    )
    raw_signal_id: Mapped[str] = mapped_column(ForeignKey("raw_signals.id"), primary_key=True)

    cluster: Mapped[EventCluster] = relationship(back_populates="members")


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint(
            "event_cluster_id", "concept_key", name="uq_opportunities_event_cluster_concept"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_concept: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(160))
    reason_type: Mapped[OpportunityReason] = mapped_column(enum_column(OpportunityReason))
    why_now: Mapped[str] = mapped_column(Text)
    target_user: Mapped[str] = mapped_column(String(240))
    location: Mapped[str] = mapped_column(String(160))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        enum_column(OpportunityStatus), default=OpportunityStatus.ELIGIBLE
    )
    search_queries: Mapped[list[str]] = mapped_column(JSON, default=list)
    uncertainties: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    event_cluster_id: Mapped[str | None] = mapped_column(
        ForeignKey("event_clusters.id"), index=True
    )
    concept_key: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = created_at_column()

    event_cluster: Mapped[EventCluster | None] = relationship(back_populates="opportunities")
    evidence: Mapped[list["OpportunityEvidence"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    scores: Mapped[list["ScoreSnapshot"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionEvent"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    product_matches: Mapped[list["ProductMatch"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunityEvidence(Base):
    __tablename__ = "opportunity_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    raw_signal_id: Mapped[str | None] = mapped_column(ForeignKey("raw_signals.id"))
    source_name: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime())
    summary: Mapped[str] = mapped_column(Text)

    opportunity: Mapped[Opportunity] = relationship(back_populates="evidence")
    raw_signal: Mapped[RawSignal | None] = relationship()


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"
    __table_args__ = (
        CheckConstraint("demand BETWEEN 0 AND 100", name="demand_range"),
        CheckConstraint("execution BETWEEN 0 AND 100", name="execution_range"),
        CheckConstraint("marketplace_fit_prior BETWEEN 0 AND 100", name="marketplace_fit_range"),
        CheckConstraint("uncertainty_penalty BETWEEN 0 AND 100", name="uncertainty_range"),
        CheckConstraint("discovery_priority BETWEEN 0 AND 100", name="priority_range"),
        CheckConstraint("timely_score BETWEEN 0 AND 100", name="timely_range"),
        CheckConstraint("trend_score BETWEEN 0 AND 100", name="trend_range"),
        CheckConstraint("listing_economics BETWEEN 0 AND 100", name="economics_range"),
        CheckConstraint("publish_priority BETWEEN 0 AND 100", name="publish_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    demand: Mapped[int] = mapped_column(Integer)
    execution: Mapped[int] = mapped_column(Integer)
    marketplace_fit_prior: Mapped[int] = mapped_column(Integer)
    uncertainty_penalty: Mapped[int] = mapped_column(Integer)
    discovery_priority: Mapped[int] = mapped_column(Integer)
    timely_score: Mapped[int | None] = mapped_column(Integer)
    trend_score: Mapped[int | None] = mapped_column(Integer)
    # Set once a listing is confirmed; publish_priority then ranks the opportunity.
    listing_economics: Mapped[int | None] = mapped_column(Integer)
    publish_priority: Mapped[int | None] = mapped_column(Integer)
    # Input dimensions, kept so the formula can be replayed on historical data.
    components: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = created_at_column()

    opportunity: Mapped[Opportunity] = relationship(back_populates="scores")


class DecisionEvent(Base):
    __tablename__ = "decision_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[DecisionType] = mapped_column(enum_column(DecisionType))
    reason_code: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    score_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = created_at_column()

    opportunity: Mapped[Opportunity] = relationship(back_populates="decisions")


class ProductMatch(Base):
    """A real affiliate listing an operator found for an opportunity.

    Money is stored as integer centavos and rates as basis points so values stay exact on every
    database. Listing facts are not edited: a correction is a new candidate.
    """

    __tablename__ = "product_matches"
    __table_args__ = (
        CheckConstraint("price_centavos > 0", name="price_positive"),
        CheckConstraint("commission_rate_bps BETWEEN 0 AND 10000", name="commission_range"),
        CheckConstraint("rating BETWEEN 0 AND 50", name="rating_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    marketplace: Mapped[str] = mapped_column(String(40))
    product_url: Mapped[str] = mapped_column(String(2048))
    affiliate_url: Mapped[str] = mapped_column(String(2048))
    listing_title: Mapped[str] = mapped_column(String(500))
    seller_name: Mapped[str | None] = mapped_column(String(240))
    seller_type: Mapped[str | None] = mapped_column(String(40))
    price_centavos: Mapped[int] = mapped_column(Integer)
    commission_rate_bps: Mapped[int] = mapped_column(Integer)
    # Tenths of a star, 0-50, so 4.8 is stored as 48.
    rating: Mapped[int | None] = mapped_column(Integer)
    review_count: Mapped[int | None] = mapped_column(Integer)
    sold_count: Mapped[int | None] = mapped_column(Integer)
    in_stock: Mapped[bool] = mapped_column(Boolean)
    shipping_note: Mapped[str | None] = mapped_column(Text)
    verified_facts: Mapped[list[str]] = mapped_column(JSON, default=list)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    image_usage_note: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProductMatchStatus] = mapped_column(
        enum_column(ProductMatchStatus), default=ProductMatchStatus.CANDIDATE
    )
    # When the operator last confirmed the listing is live and affiliate-eligible.
    eligibility_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = created_at_column()

    opportunity: Mapped[Opportunity] = relationship(back_populates="product_matches")
    briefs: Mapped[list["CreativeBrief"]] = relationship(back_populates="product_match")


class ListingSearchFailure(Base):
    """A marketplace search that found no usable listing. Feeds marketplace-fit priors."""

    __tablename__ = "listing_search_failures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    marketplace: Mapped[str] = mapped_column(String(40))
    query: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str] = mapped_column(String(80))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()


class CreativeBrief(Base):
    """An immutable brief that every copy variant derives from."""

    __tablename__ = "creative_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_match_id: Mapped[str] = mapped_column(
        ForeignKey("product_matches.id", ondelete="CASCADE"), index=True
    )
    platform: Mapped[str] = mapped_column(String(40))
    audience: Mapped[str] = mapped_column(String(240))
    angle: Mapped[str] = mapped_column(Text)
    verified_facts: Mapped[list[str]] = mapped_column(JSON, default=list)
    forbidden_claims: Mapped[list[str]] = mapped_column(JSON, default=list)
    disclosure: Mapped[str] = mapped_column(Text)
    hypothesis: Mapped[str | None] = mapped_column(Text)
    experiment_label: Mapped[str | None] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = created_at_column()

    product_match: Mapped[ProductMatch] = relationship(back_populates="briefs")
    variants: Mapped[list["CreativeVariant"]] = relationship(
        back_populates="brief", cascade="all, delete-orphan"
    )


class CreativeVariant(Base):
    """One copy package. An operator edit creates a new variant whose parent is the edited one."""

    __tablename__ = "creative_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    brief_id: Mapped[str] = mapped_column(
        ForeignKey("creative_briefs.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("creative_variants.id"))
    hook_type: Mapped[str] = mapped_column(String(40))
    hook: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    cta: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    generator: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    # Model, request id, and token usage for AI-generated variants.
    generation: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    policy_issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    status: Mapped[CreativeStatus] = mapped_column(
        enum_column(CreativeStatus), default=CreativeStatus.NEEDS_REVIEW
    )
    # Goes into the affiliate link's sub ID so sales trace back to this variant.
    tracking_code: Mapped[str | None] = mapped_column(String(40), unique=True)
    exported_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = created_at_column()

    brief: Mapped[CreativeBrief] = relationship(back_populates="variants")
    reviews: Mapped[list["CreativeReview"]] = relationship(
        back_populates="variant", cascade="all, delete-orphan"
    )


class CreativeReview(Base):
    __tablename__ = "creative_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    variant_id: Mapped[str] = mapped_column(
        ForeignKey("creative_variants.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[ReviewDecision] = mapped_column(enum_column(ReviewDecision))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()

    variant: Mapped[CreativeVariant] = relationship(back_populates="reviews")


class MetricObservation(Base):
    """Imported results for one tracking code on one day. Append-only; the newest row wins."""

    __tablename__ = "metric_observations"
    __table_args__ = (Index("ix_metric_observations_code_day", "tracking_code", "observed_on"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tracking_code: Mapped[str] = mapped_column(String(80))
    # Null when Tr3ndly did not issue the code: a baseline, unassisted post.
    variant_id: Mapped[str | None] = mapped_column(ForeignKey("creative_variants.id"), index=True)
    observed_on: Mapped[date] = mapped_column(Date)
    views: Mapped[int | None] = mapped_column(Integer)
    clicks: Mapped[int | None] = mapped_column(Integer)
    orders: Mapped[int | None] = mapped_column(Integer)
    gmv_centavos: Mapped[int | None] = mapped_column(Integer)
    commission_centavos: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(40))
    import_batch: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = created_at_column()

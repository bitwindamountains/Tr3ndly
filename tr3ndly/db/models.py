import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tr3ndly.db.base import Base


def new_id() -> str:
    return str(uuid.uuid4())


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


def enum_values(enum_type: type[enum.Enum]) -> list[str]:
    return [str(member.value) for member in enum_type]


class SourceConfig(Base):
    __tablename__ = "source_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    access_method: Mapped[str] = mapped_column(String(80))
    terms_url: Mapped[str | None] = mapped_column(String(2048))
    enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    runs: Mapped[list["SourceRun"]] = relationship(back_populates="source")


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id", ondelete="CASCADE"))
    status: Mapped[SourceRunStatus] = mapped_column(
        Enum(SourceRunStatus, native_enum=False, values_callable=enum_values),
        default=SourceRunStatus.RUNNING,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[str | None] = mapped_column(String(512))
    error: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    source: Mapped[SourceConfig] = relationship(back_populates="runs")
    signals: Mapped[list["RawSignal"]] = relationship(back_populates="source_run")


class RawSignal(Base):
    __tablename__ = "raw_signals"
    __table_args__ = (Index("ix_raw_signals_source_observed", "source_id", "observed_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id"))
    source_run_id: Mapped[str] = mapped_column(ForeignKey("source_runs.id"))
    external_id: Mapped[str | None] = mapped_column(String(512))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(1000))
    permitted_summary: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_run: Mapped[SourceRun] = relationship(back_populates="signals")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_concept: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(160))
    reason_type: Mapped[OpportunityReason] = mapped_column(
        Enum(OpportunityReason, native_enum=False, values_callable=enum_values)
    )
    why_now: Mapped[str] = mapped_column(Text)
    target_user: Mapped[str] = mapped_column(String(240))
    location: Mapped[str] = mapped_column(String(160))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, native_enum=False, values_callable=enum_values),
        default=OpportunityStatus.ELIGIBLE,
    )
    search_queries: Mapped[list[str]] = mapped_column(JSON, default=list)
    uncertainties: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped[list["OpportunityEvidence"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    scores: Mapped[list["ScoreSnapshot"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionEvent"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunityEvidence(Base):
    __tablename__ = "opportunity_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    source_name: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str] = mapped_column(Text)

    opportunity: Mapped[Opportunity] = relationship(back_populates="evidence")


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"
    __table_args__ = (
        CheckConstraint("demand BETWEEN 0 AND 100", name="demand_range"),
        CheckConstraint("execution BETWEEN 0 AND 100", name="execution_range"),
        CheckConstraint("marketplace_fit_prior BETWEEN 0 AND 100", name="marketplace_fit_range"),
        CheckConstraint("uncertainty_penalty BETWEEN 0 AND 100", name="uncertainty_range"),
        CheckConstraint("discovery_priority BETWEEN 0 AND 100", name="priority_range"),
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
    version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    opportunity: Mapped[Opportunity] = relationship(back_populates="scores")


class DecisionEvent(Base):
    __tablename__ = "decision_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, native_enum=False, values_callable=enum_values)
    )
    reason_code: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    score_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    opportunity: Mapped[Opportunity] = relationship(back_populates="decisions")

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SourceHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DEMO = "demo"


class ReasonType(StrEnum):
    TIMELY = "timely"
    TREND = "trend"
    BOTH = "both"


class Evidence(BaseModel):
    source_name: str
    source_url: HttpUrl | None = None
    observed_at: datetime
    summary: str


class ScoreBreakdown(BaseModel):
    demand: int = Field(ge=0, le=100)
    execution: int = Field(ge=0, le=100)
    marketplace_fit_prior: int = Field(ge=0, le=100)
    uncertainty_penalty: int = Field(ge=0, le=100)
    discovery_priority: int = Field(ge=0, le=100)
    version: str


class OpportunitySummary(BaseModel):
    id: str
    product_concept: str
    category: str
    reason_type: ReasonType
    why_now: str
    target_user: str
    location: str
    expires_at: datetime
    score: ScoreBreakdown
    search_queries: list[str]
    uncertainties: list[str]
    evidence: list[Evidence]


class DecisionCreate(BaseModel):
    decision: Literal["accepted", "rejected", "deferred", "insufficient_evidence"]
    reason_code: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=2000)


class DecisionResponse(BaseModel):
    id: str
    opportunity_id: str
    decision: str
    reason_code: str
    note: str | None
    score_version: str
    created_at: datetime


class OpportunityDetail(OpportunitySummary):
    status: str
    decisions: list[DecisionResponse]


class TimelySignal(BaseModel):
    id: str
    headline: str
    event_type: str
    location: str
    summary: str
    confidence: int = Field(ge=0, le=100)
    consumer_needs: list[str]
    expires_at: datetime


class TodayResponse(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mode: Literal["demo", "live"] = "demo"
    source_health: SourceHealth = SourceHealth.DEMO
    signals: list[TimelySignal]
    opportunities: list[OpportunitySummary]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str
    version: str

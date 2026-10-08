from datetime import UTC, datetime
from decimal import Decimal
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


class SourceState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    NEVER_RUN = "never_run"
    DISABLED = "disabled"


class ScoreBreakdown(BaseModel):
    demand: int = Field(ge=0, le=100)
    execution: int = Field(ge=0, le=100)
    marketplace_fit_prior: int = Field(ge=0, le=100)
    uncertainty_penalty: int = Field(ge=0, le=100)
    discovery_priority: int = Field(ge=0, le=100)
    timely_score: int | None = Field(default=None, ge=0, le=100)
    trend_score: int | None = Field(default=None, ge=0, le=100)
    # Present once a listing is confirmed; publish_priority then decides the ranking.
    listing_economics: int | None = Field(default=None, ge=0, le=100)
    publish_priority: int | None = Field(default=None, ge=0, le=100)
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


Marketplace = Literal["shopee", "lazada", "tiktok_shop", "other"]
SellerType = Literal["mall", "preferred", "standard"]


class ProductMatchCreate(BaseModel):
    """A listing the operator found. Price in PHP, commission as a percentage, rating 0-5."""

    marketplace: Marketplace
    product_url: HttpUrl
    affiliate_url: HttpUrl
    listing_title: str = Field(min_length=3, max_length=500)
    seller_name: str | None = Field(default=None, max_length=240)
    seller_type: SellerType | None = None
    price_php: Decimal = Field(gt=0, le=10_000_000, decimal_places=2)
    commission_rate_pct: Decimal = Field(ge=0, le=100, decimal_places=2)
    rating: Decimal | None = Field(default=None, ge=0, le=5, decimal_places=1)
    review_count: int | None = Field(default=None, ge=0)
    sold_count: int | None = Field(default=None, ge=0)
    in_stock: bool = True
    shipping_note: str | None = Field(default=None, max_length=1000)
    # Facts copied from the listing. Copy may only state these.
    verified_facts: list[str] = Field(default_factory=list, max_length=12)
    image_url: HttpUrl | None = None
    image_usage_note: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)


class ProductMatchConfirm(BaseModel):
    # The operator checked that the listing is live and eligible for their affiliate account.
    eligibility_confirmed: Literal[True]


class ProductMatchView(BaseModel):
    id: str
    opportunity_id: str
    marketplace: str
    product_url: str
    affiliate_url: str
    listing_title: str
    seller_name: str | None
    seller_type: str | None
    price_php: float
    commission_rate_pct: float
    expected_commission_php: float
    rating: float | None
    review_count: int | None
    sold_count: int | None
    in_stock: bool
    shipping_note: str | None
    verified_facts: list[str]
    image_url: str | None
    image_usage_note: str | None
    notes: str | None
    status: str
    listing_economics: int = Field(ge=0, le=100)
    economics_components: dict[str, int]
    eligibility_checked_at: datetime | None
    confirmed_at: datetime | None
    created_at: datetime


SearchFailureReason = Literal[
    "no_results",
    "not_affiliate_eligible",
    "low_commission",
    "poor_quality",
    "out_of_stock",
    "other",
]


class SearchFailureCreate(BaseModel):
    marketplace: Marketplace
    query: str = Field(min_length=2, max_length=500)
    reason: SearchFailureReason
    note: str | None = Field(default=None, max_length=2000)


class SearchFailureView(BaseModel):
    id: str
    marketplace: str
    query: str
    reason: str
    note: str | None
    created_at: datetime


class OpportunityDetail(OpportunitySummary):
    status: str
    # Whether a new operator decision would be accepted right now.
    decidable: bool
    # Whether listings can be added or confirmed right now (accepted or matched, still open).
    matchable: bool
    decisions: list[DecisionResponse]
    product_matches: list[ProductMatchView] = Field(default_factory=list)
    search_failures: list[SearchFailureView] = Field(default_factory=list)


Platform = Literal["tiktok", "facebook", "instagram", "youtube_shorts"]


class CreativeBriefCreate(BaseModel):
    platform: Platform
    # Defaults come from the opportunity when these are left empty.
    angle: str | None = Field(default=None, max_length=500)
    audience: str | None = Field(default=None, max_length=240)
    hypothesis: str | None = Field(default=None, max_length=1000)
    experiment_label: str | None = Field(default=None, max_length=120)


class PolicyIssue(BaseModel):
    code: str
    field: str
    match: str
    message: str
    blocking: bool


class CreativeVariantView(BaseModel):
    id: str
    brief_id: str
    parent_id: str | None
    hook_type: str
    hook: str
    caption: str
    cta: str
    hashtags: list[str]
    generator: str
    prompt_version: str | None
    policy_issues: list[PolicyIssue]
    status: str
    tracking_code: str | None
    exported_at: datetime | None
    created_at: datetime


class CreativeBriefView(BaseModel):
    id: str
    product_match_id: str
    platform: str
    audience: str
    angle: str
    verified_facts: list[str]
    forbidden_claims: list[str]
    disclosure: str
    hypothesis: str | None
    experiment_label: str | None
    version: str
    created_at: datetime
    variants: list[CreativeVariantView]


class CopyEdits(BaseModel):
    hook: str = Field(min_length=3, max_length=300)
    caption: str = Field(min_length=3, max_length=2200)
    cta: str = Field(min_length=2, max_length=200)
    hashtags: list[str] = Field(default_factory=list, max_length=10)


class CreativeReviewCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=2000)
    # Saving edits creates a new variant; the decision then applies to it.
    edits: CopyEdits | None = None


class ExportPackage(BaseModel):
    variant_id: str
    tracking_code: str
    platform: str
    post_text: str
    disclosure: str
    affiliate_url: str
    product_url: str
    image_url: str | None
    image_usage_note: str | None
    checklist: list[str]
    exported_at: datetime


class StudioView(BaseModel):
    opportunity: OpportunitySummary
    product_match: ProductMatchView
    # How generation will run: "claude:<model>" or "template".
    generator: str
    briefs: list[CreativeBriefView]


class ResultsImport(BaseModel):
    csv: str = Field(min_length=1, max_length=1_000_000)


class ResultsImportResult(BaseModel):
    rows: int
    imported: int
    unchanged: int
    # Codes Tr3ndly did not issue. They are kept as baseline (unassisted) posts.
    baseline_codes: list[str]
    errors: list[str]


class ResultTotals(BaseModel):
    posts: int
    views: int
    clicks: int
    orders: int
    gmv_php: float
    commission_php: float
    commission_per_post_php: float | None
    commission_per_1000_views_php: float | None
    click_through_rate: float | None
    conversion_rate: float | None


class ResultGroup(BaseModel):
    key: str
    totals: ResultTotals


class ResultsOverview(BaseModel):
    assisted: ResultTotals
    baseline: ResultTotals
    by_category: list[ResultGroup]
    by_event_type: list[ResultGroup]
    by_hook_type: list[ResultGroup]
    warnings: list[str]


class TimelySignal(BaseModel):
    id: str
    headline: str
    event_type: str
    location: str
    summary: str
    confidence: int = Field(ge=0, le=100)
    consumer_needs: list[str]
    timely_score: int = Field(ge=0, le=100)
    sensitivity: str
    expires_at: datetime


class SourceStatus(BaseModel):
    slug: str
    display_name: str
    state: SourceState
    poll_interval_minutes: int
    attribution: str
    last_run_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None


class SourceRunView(BaseModel):
    id: str
    source: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    error: str | None
    stats: dict[str, int]


class TodayResponse(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mode: Literal["demo", "live"] = "demo"
    source_health: SourceHealth = SourceHealth.DEMO
    sources: list[SourceStatus] = Field(default_factory=list)
    # Locations with open opportunities, for filter controls; unaffected by the active filter.
    locations: list[str] = Field(default_factory=list)
    signals: list[TimelySignal]
    opportunities: list[OpportunitySummary]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str
    version: str

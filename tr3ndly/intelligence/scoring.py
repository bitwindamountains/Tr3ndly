"""Versioned scoring formulas from the master build plan, section 9.

Weights are provisional. Change them only with a new SCORE_VERSION and a recorded evaluation.
Component inputs are stored with every snapshot so a formula can be replayed later.
"""

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from tr3ndly.db.models import Sensitivity
from tr3ndly.intelligence.catalog import ProductConcept

SCORE_VERSION = "discovery-v2"
# Used instead of SCORE_VERSION once a confirmed listing adds economics to the score.
PUBLISH_SCORE_VERSION = "publish-v1"
# Neutral until results show which kinds of tests teach the most.
LEARNING_VALUE = 50

SENSITIVITY_PENALTY: dict[Sensitivity, int] = {
    Sensitivity.NONE: 0,
    Sensitivity.LOW: 0,
    Sensitivity.MEDIUM: 15,
    Sensitivity.HIGH: 50,
    Sensitivity.BLOCKED: 100,
}


def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(round(max(low, min(high, value))))


@dataclass(frozen=True)
class TimelyDimensions:
    freshness: int
    geography: int
    reach: int
    need_strength: int
    actionability: int
    source_confidence: int
    sensitivity_penalty: int

    def score(self) -> int:
        return clamp(
            0.15 * self.freshness
            + 0.15 * self.geography
            + 0.10 * self.reach
            + 0.25 * self.need_strength
            + 0.20 * self.actionability
            + 0.15 * self.source_confidence
            - self.sensitivity_penalty
        )

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def demand_score(timely: int | None, trend: int | None) -> int:
    """A product does not need to be both timely and trending; agreement earns a small bonus."""
    high = max(timely or 0, trend or 0)
    low = min(timely or 0, trend or 0)
    return clamp(high + 0.15 * low)


def uncertainty_penalty(lead_days: int, sensitivity: Sensitivity, matched: bool = False) -> int:
    # Until a listing is matched, whether a good one exists is itself uncertain.
    penalty = (0 if matched else 5) + 5 * max(0, lead_days)
    if sensitivity in (Sensitivity.MEDIUM, Sensitivity.HIGH):
        penalty += 5
    return clamp(penalty)


@dataclass(frozen=True)
class ListingFacts:
    """The listing fields the economics score reads. Money in centavos, rate in basis points."""

    price_centavos: int
    commission_rate_bps: int
    rating_tenths: int | None
    review_count: int | None
    sold_count: int | None
    seller_type: str | None


def expected_commission_centavos(price_centavos: int, commission_rate_bps: int) -> int:
    return price_centavos * commission_rate_bps // 10_000


# Conversion prior by price band (PHP): impulse-friendly prices convert best on social posts.
PRICE_BANDS: tuple[tuple[int, int], ...] = (
    (100, 60),
    (1_000, 90),
    (3_000, 75),
    (10_000, 55),
)
EXPENSIVE_PRICE_PRIOR = 35
SELLER_SCORES = {"mall": 90, "preferred": 75, "standard": 55}
UNKNOWN = 50


def listing_economics(listing: ListingFacts) -> tuple[int, dict[str, int]]:
    """Plan section 9.3: commission amount, price band, seller, rating evidence, and sales.

    Returns the score and its components. Commission amount, not rate, is what counts.
    """
    commission_php = (
        expected_commission_centavos(listing.price_centavos, listing.commission_rate_bps) / 100
    )
    # 50 at PHP 20 per sale, +40 for every tenfold increase.
    commission = clamp(50 + 40 * math.log10(commission_php / 20)) if commission_php > 0 else 0

    price_php = listing.price_centavos / 100
    price_band = next(
        (prior for limit, prior in PRICE_BANDS if price_php < limit), EXPENSIVE_PRICE_PRIOR
    )
    seller = SELLER_SCORES.get(listing.seller_type or "", UNKNOWN)

    rating = UNKNOWN
    if listing.rating_tenths is not None:
        # 3.5 stars scores 20, 5.0 scores 100; few reviews pull the score toward neutral.
        stars = clamp(20 + 80 * (listing.rating_tenths / 10 - 3.5) / 1.5)
        weight = min(1.0, (listing.review_count or 0) / 200)
        rating = clamp(UNKNOWN + (stars - UNKNOWN) * weight)

    sales = UNKNOWN
    if listing.sold_count is not None:
        # About 30 with no sales, 90 at 1,000 sold.
        sales = clamp(30 + 20 * math.log10(listing.sold_count + 1))

    components = {
        "commission": commission,
        "price_band": price_band,
        "seller": seller,
        "rating": rating,
        "sales": sales,
    }
    score = clamp(
        0.35 * commission + 0.15 * price_band + 0.15 * seller + 0.20 * rating + 0.15 * sales
    )
    return score, components


@dataclass(frozen=True)
class OpportunityScore:
    timely: int | None
    trend: int | None
    demand: int
    execution: int
    marketplace_fit_prior: int
    uncertainty: int
    discovery_priority: int
    listing_economics: int | None = None
    publish_priority: int | None = None
    economics_components: dict[str, Any] = field(default_factory=dict)
    version: str = SCORE_VERSION


def score_concept(
    timely: TimelyDimensions,
    concept: ProductConcept,
    lead_days: int,
    sensitivity: Sensitivity,
    listing: ListingFacts | None = None,
) -> OpportunityScore:
    """Score a timely-only concept; with a confirmed listing, also its publish priority."""
    timely_score = timely.score()
    return score_opportunity(
        demand=demand_score(timely_score, None),
        timely=timely_score,
        trend=None,
        execution=concept.execution,
        marketplace_fit_prior=concept.marketplace_fit_prior,
        lead_days=lead_days,
        sensitivity=sensitivity,
        listing=listing,
    )


def score_opportunity(
    *,
    demand: int,
    timely: int | None,
    trend: int | None,
    execution: int,
    marketplace_fit_prior: int,
    lead_days: int,
    sensitivity: Sensitivity,
    listing: ListingFacts | None = None,
) -> OpportunityScore:
    uncertainty = uncertainty_penalty(lead_days, sensitivity, matched=listing is not None)
    discovery = discovery_priority(demand, execution, marketplace_fit_prior, uncertainty)
    if listing is None:
        return OpportunityScore(
            timely=timely,
            trend=trend,
            demand=demand,
            execution=execution,
            marketplace_fit_prior=marketplace_fit_prior,
            uncertainty=uncertainty,
            discovery_priority=discovery,
        )
    economics, components = listing_economics(listing)
    return OpportunityScore(
        timely=timely,
        trend=trend,
        demand=demand,
        execution=execution,
        marketplace_fit_prior=marketplace_fit_prior,
        uncertainty=uncertainty,
        discovery_priority=discovery,
        listing_economics=economics,
        publish_priority=publish_priority(demand, execution, economics, uncertainty),
        economics_components=components,
        version=PUBLISH_SCORE_VERSION,
    )


def publish_priority(
    demand: int,
    execution: int,
    economics: int,
    uncertainty: int,
    learning_value: int = LEARNING_VALUE,
    effort: int = 0,
) -> int:
    """Plan section 9.5, after a listing is matched."""
    return clamp(
        0.40 * demand
        + 0.25 * execution
        + 0.30 * economics
        + 0.05 * learning_value
        - uncertainty
        - effort
    )


def discovery_priority(
    demand: int,
    execution: int,
    marketplace_fit_prior: int,
    uncertainty: int,
    saturation: int = 0,
) -> int:
    return clamp(
        0.55 * demand + 0.30 * execution + 0.15 * marketplace_fit_prior - uncertainty - saturation
    )

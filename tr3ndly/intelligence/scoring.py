"""Versioned scoring formulas from the master build plan, section 9.

Weights are provisional. Change them only with a new SCORE_VERSION and a recorded evaluation.
Component inputs are stored with every snapshot so a formula can be replayed later.
"""

from dataclasses import asdict, dataclass

from tr3ndly.db.models import Sensitivity
from tr3ndly.intelligence.catalog import ProductConcept

SCORE_VERSION = "discovery-v1"

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


def uncertainty_penalty(lead_days: int, sensitivity: Sensitivity) -> int:
    # No listing is matched before the operator searches, so there is always some uncertainty.
    penalty = 5 + 5 * max(0, lead_days)
    if sensitivity in (Sensitivity.MEDIUM, Sensitivity.HIGH):
        penalty += 5
    return clamp(penalty)


@dataclass(frozen=True)
class OpportunityScore:
    timely: int
    trend: int | None
    demand: int
    execution: int
    marketplace_fit_prior: int
    uncertainty: int
    discovery_priority: int
    version: str = SCORE_VERSION


def score_concept(
    timely: TimelyDimensions,
    concept: ProductConcept,
    lead_days: int,
    sensitivity: Sensitivity,
) -> OpportunityScore:
    """Discovery priority for a timely-only concept before any listing is matched."""
    timely_score = timely.score()
    demand = demand_score(timely_score, None)
    uncertainty = uncertainty_penalty(lead_days, sensitivity)
    return OpportunityScore(
        timely=timely_score,
        trend=None,
        demand=demand,
        execution=concept.execution,
        marketplace_fit_prior=concept.marketplace_fit_prior,
        uncertainty=uncertainty,
        discovery_priority=discovery_priority(
            demand, concept.execution, concept.marketplace_fit_prior, uncertainty
        ),
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

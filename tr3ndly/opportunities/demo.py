from datetime import UTC, datetime, timedelta

from tr3ndly.db.models import (
    Opportunity,
    OpportunityEvidence,
    OpportunityReason,
    OpportunityStatus,
    ScoreSnapshot,
)
from tr3ndly.opportunities.scores import NO_LISTING_UNCERTAINTY

DEMO_OPPORTUNITY_ID = "demo_opp_fan"


def build_demo_opportunity(now: datetime | None = None) -> Opportunity:
    now = now or datetime.now(UTC)
    opportunity = Opportunity(
        id=DEMO_OPPORTUNITY_ID,
        product_concept="Portable rechargeable fan",
        category="Household convenience",
        reason_type=OpportunityReason.TIMELY,
        why_now="Warm daytime conditions may increase interest in portable personal cooling.",
        target_user="Commuters, students, and households",
        location="Metro Manila",
        expires_at=now + timedelta(days=365),
        status=OpportunityStatus.ELIGIBLE,
        search_queries=[
            "portable rechargeable fan",
            "mini fan USB rechargeable",
            "handheld fan long battery",
        ],
        uncertainties=[
            NO_LISTING_UNCERTAINTY,
            "This is seeded demo evidence and not a live weather recommendation.",
        ],
        is_demo=True,
    )
    opportunity.evidence.append(
        OpportunityEvidence(
            source_name="Demo weather source",
            observed_at=now,
            summary=(
                "Seeded evidence demonstrates how a source observation is retained "
                "with an opportunity."
            ),
        )
    )
    opportunity.scores.append(
        ScoreSnapshot(
            demand=76,
            execution=84,
            marketplace_fit_prior=80,
            uncertainty_penalty=8,
            discovery_priority=70,
            version="discovery-v0.1",
        )
    )
    return opportunity

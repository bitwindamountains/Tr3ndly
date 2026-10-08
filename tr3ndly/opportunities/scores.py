"""Append-only score snapshots, shared by the pipeline and listing confirmation."""

from typing import Any

from tr3ndly.db.models import Opportunity, ProductMatch, ProductMatchStatus, ScoreSnapshot
from tr3ndly.intelligence.scoring import ListingFacts, OpportunityScore

NO_LISTING_UNCERTAINTY = "No affiliate listing has been matched yet."


def confirmed_match(opportunity: Opportunity) -> ProductMatch | None:
    """Requires product_matches to be loaded."""
    confirmed = [
        match
        for match in opportunity.product_matches
        if match.status == ProductMatchStatus.CONFIRMED
    ]
    return max(confirmed, key=lambda match: match.confirmed_at or match.created_at, default=None)


def listing_facts(match: ProductMatch) -> ListingFacts:
    return ListingFacts(
        price_centavos=match.price_centavos,
        commission_rate_bps=match.commission_rate_bps,
        rating_tenths=match.rating,
        review_count=match.review_count,
        sold_count=match.sold_count,
        seller_type=match.seller_type,
    )


def record_score(
    opportunity: Opportunity,
    score: OpportunityScore,
    components: dict[str, Any],
    match: ProductMatch | None = None,
) -> bool:
    """Append a snapshot unless the score is unchanged. Requires scores to be loaded."""
    latest = max(opportunity.scores, key=lambda item: (item.created_at, item.id), default=None)
    if latest is not None and _snapshot_values(latest) == _score_values(score):
        return False
    if match is not None:
        components = {
            **components,
            "listing": {"product_match_id": match.id, **score.economics_components},
        }
    opportunity.scores.append(
        ScoreSnapshot(
            demand=score.demand,
            execution=score.execution,
            marketplace_fit_prior=score.marketplace_fit_prior,
            uncertainty_penalty=score.uncertainty,
            discovery_priority=score.discovery_priority,
            timely_score=score.timely,
            trend_score=score.trend,
            listing_economics=score.listing_economics,
            publish_priority=score.publish_priority,
            components=components,
            version=score.version,
        )
    )
    return True


def _score_values(score: OpportunityScore) -> tuple[object, ...]:
    return (
        score.version,
        score.demand,
        score.execution,
        score.marketplace_fit_prior,
        score.uncertainty,
        score.discovery_priority,
        score.timely,
        score.trend,
        score.listing_economics,
        score.publish_priority,
    )


def _snapshot_values(snapshot: ScoreSnapshot) -> tuple[object, ...]:
    return (
        snapshot.version,
        snapshot.demand,
        snapshot.execution,
        snapshot.marketplace_fit_prior,
        snapshot.uncertainty_penalty,
        snapshot.discovery_priority,
        snapshot.timely_score,
        snapshot.trend_score,
        snapshot.listing_economics,
        snapshot.publish_priority,
    )

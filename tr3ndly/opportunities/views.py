"""Mapping from ORM rows to API read models."""

from tr3ndly.db.models import (
    DecisionEvent,
    ListingSearchFailure,
    Opportunity,
    ProductMatch,
    ScoreSnapshot,
)
from tr3ndly.intelligence.scoring import expected_commission_centavos, listing_economics
from tr3ndly.opportunities.scores import listing_facts
from tr3ndly.schemas import (
    DecisionResponse,
    Evidence,
    OpportunitySummary,
    ProductMatchView,
    ScoreBreakdown,
    SearchFailureView,
)


def latest_score(opportunity: Opportunity) -> ScoreSnapshot:
    return max(opportunity.scores, key=lambda item: (item.created_at, item.id))


def rank_value(opportunity: Opportunity) -> int:
    """Publish priority once a listing is confirmed, discovery priority before."""
    score = latest_score(opportunity)
    if score.publish_priority is not None:
        return score.publish_priority
    return score.discovery_priority


def to_summary(opportunity: Opportunity) -> OpportunitySummary:
    """Requires evidence (with raw_signal) and scores to be loaded."""
    score = latest_score(opportunity)
    # Evidence rows are append-only; show only the newest observation of each source item.
    newest: dict[str, Evidence] = {}
    for item in sorted(opportunity.evidence, key=lambda row: row.observed_at):
        key = (
            item.raw_signal.external_id
            if item.raw_signal and item.raw_signal.external_id
            else item.id
        )
        newest[key] = Evidence(
            source_name=item.source_name,
            source_url=item.source_url,
            observed_at=item.observed_at,
            summary=item.summary,
        )
    return OpportunitySummary(
        id=opportunity.id,
        product_concept=opportunity.product_concept,
        category=opportunity.category,
        reason_type=opportunity.reason_type.value,
        why_now=opportunity.why_now,
        target_user=opportunity.target_user,
        location=opportunity.location,
        expires_at=opportunity.expires_at,
        score=ScoreBreakdown(
            demand=score.demand,
            execution=score.execution,
            marketplace_fit_prior=score.marketplace_fit_prior,
            uncertainty_penalty=score.uncertainty_penalty,
            discovery_priority=score.discovery_priority,
            timely_score=score.timely_score,
            trend_score=score.trend_score,
            listing_economics=score.listing_economics,
            publish_priority=score.publish_priority,
            version=score.version,
        ),
        search_queries=opportunity.search_queries,
        uncertainties=opportunity.uncertainties,
        evidence=list(newest.values()),
    )


def to_match(match: ProductMatch) -> ProductMatchView:
    economics, components = listing_economics(listing_facts(match))
    return ProductMatchView(
        id=match.id,
        opportunity_id=match.opportunity_id,
        marketplace=match.marketplace,
        product_url=match.product_url,
        affiliate_url=match.affiliate_url,
        listing_title=match.listing_title,
        seller_name=match.seller_name,
        seller_type=match.seller_type,
        price_php=match.price_centavos / 100,
        commission_rate_pct=match.commission_rate_bps / 100,
        expected_commission_php=expected_commission_centavos(
            match.price_centavos, match.commission_rate_bps
        )
        / 100,
        rating=match.rating / 10 if match.rating is not None else None,
        review_count=match.review_count,
        sold_count=match.sold_count,
        in_stock=match.in_stock,
        shipping_note=match.shipping_note,
        verified_facts=match.verified_facts,
        image_url=match.image_url,
        image_usage_note=match.image_usage_note,
        notes=match.notes,
        status=match.status.value,
        listing_economics=economics,
        economics_components=components,
        eligibility_checked_at=match.eligibility_checked_at,
        confirmed_at=match.confirmed_at,
        created_at=match.created_at,
    )


def to_search_failure(failure: ListingSearchFailure) -> SearchFailureView:
    return SearchFailureView(
        id=failure.id,
        marketplace=failure.marketplace,
        query=failure.query,
        reason=failure.reason,
        note=failure.note,
        created_at=failure.created_at,
    )


def to_decision(event: DecisionEvent) -> DecisionResponse:
    return DecisionResponse(
        id=event.id,
        opportunity_id=event.opportunity_id,
        decision=event.decision.value,
        reason_code=event.reason_code,
        note=event.note,
        score_version=event.score_version,
        created_at=event.created_at,
    )

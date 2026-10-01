"""Mapping from ORM rows to API read models."""

from tr3ndly.db.models import DecisionEvent, Opportunity, ScoreSnapshot
from tr3ndly.schemas import DecisionResponse, Evidence, OpportunitySummary, ScoreBreakdown


def latest_score(opportunity: Opportunity) -> ScoreSnapshot:
    return max(opportunity.scores, key=lambda item: (item.created_at, item.id))


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
            version=score.version,
        ),
        search_queries=opportunity.search_queries,
        uncertainties=opportunity.uncertainties,
        evidence=list(newest.values()),
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

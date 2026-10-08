"""Write side for product matches and failed searches (plan section 12).

An operator adds the real listing they found, then confirms it is live and affiliate-eligible.
Confirming moves the opportunity to `matched` and rescores it with listing economics.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.db.models import (
    ListingSearchFailure,
    Opportunity,
    OpportunityStatus,
    ProductMatch,
    ProductMatchStatus,
    Sensitivity,
)
from tr3ndly.db.types import utcnow
from tr3ndly.errors import Conflict, NotFound
from tr3ndly.intelligence.scoring import score_opportunity
from tr3ndly.opportunities.scores import NO_LISTING_UNCERTAINTY, listing_facts, record_score
from tr3ndly.opportunities.views import latest_score, to_match, to_search_failure
from tr3ndly.schemas import (
    ProductMatchCreate,
    ProductMatchView,
    SearchFailureCreate,
    SearchFailureView,
)

# Listings are added only after the operator accepts the opportunity.
MATCHABLE = (OpportunityStatus.ACCEPTED, OpportunityStatus.MATCHED)


def is_matchable(opportunity: Opportunity, now: datetime) -> bool:
    return opportunity.status in MATCHABLE and opportunity.expires_at > now


def _require_matchable(opportunity: Opportunity, now: datetime) -> None:
    if opportunity.expires_at <= now:
        raise Conflict("The opportunity window has closed")
    if opportunity.status not in MATCHABLE:
        raise Conflict("Accept the opportunity before adding or confirming a listing")


def _clean_facts(facts: list[str]) -> list[str]:
    cleaned: list[str] = []
    for fact in facts:
        text = " ".join(fact.split())[:300]
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


async def add_product_match(
    session: AsyncSession,
    opportunity_id: str,
    payload: ProductMatchCreate,
    now: datetime | None = None,
) -> ProductMatchView:
    now = now or utcnow()
    opportunity = await session.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise NotFound("Opportunity not found")
    _require_matchable(opportunity, now)

    match = ProductMatch(
        opportunity_id=opportunity.id,
        marketplace=payload.marketplace,
        product_url=str(payload.product_url),
        affiliate_url=str(payload.affiliate_url),
        listing_title=payload.listing_title.strip(),
        seller_name=payload.seller_name,
        seller_type=payload.seller_type,
        price_centavos=int(payload.price_php * 100),
        commission_rate_bps=int(payload.commission_rate_pct * 100),
        rating=int(payload.rating * 10) if payload.rating is not None else None,
        review_count=payload.review_count,
        sold_count=payload.sold_count,
        in_stock=payload.in_stock,
        shipping_note=payload.shipping_note,
        verified_facts=_clean_facts(payload.verified_facts),
        image_url=str(payload.image_url) if payload.image_url else None,
        image_usage_note=payload.image_usage_note,
        notes=payload.notes,
        status=ProductMatchStatus.CANDIDATE,
    )
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return to_match(match)


async def confirm_product_match(
    session: AsyncSession, match_id: str, now: datetime | None = None
) -> ProductMatchView:
    """Confirm (or re-check) a listing: it becomes the opportunity's one confirmed listing."""
    now = now or utcnow()
    match = await session.scalar(
        select(ProductMatch)
        .where(ProductMatch.id == match_id)
        .options(
            selectinload(ProductMatch.opportunity).selectinload(Opportunity.scores),
            selectinload(ProductMatch.opportunity).selectinload(Opportunity.product_matches),
        )
    )
    if match is None:
        raise NotFound("Product match not found")
    opportunity = match.opportunity
    if match.status == ProductMatchStatus.STALE:
        raise Conflict("This listing was replaced by another one; add it again to use it")
    _require_matchable(opportunity, now)
    # Listing gates (plan section 8): a high score cannot override these.
    if not match.in_stock:
        raise Conflict("An out-of-stock listing cannot be confirmed")
    if match.commission_rate_bps <= 0:
        raise Conflict("This listing pays no commission")
    if not opportunity.scores:
        raise Conflict("Opportunity has no score snapshot to rescore")

    for other in opportunity.product_matches:
        if other.id != match.id and other.status == ProductMatchStatus.CONFIRMED:
            other.status = ProductMatchStatus.STALE
    match.status = ProductMatchStatus.CONFIRMED
    match.confirmed_at = match.confirmed_at or now
    match.eligibility_checked_at = now
    opportunity.status = OpportunityStatus.MATCHED
    opportunity.uncertainties = [
        item for item in opportunity.uncertainties if item != NO_LISTING_UNCERTAINTY
    ]

    # Rescore from the latest snapshot's inputs, the same way the pipeline will next run.
    latest = latest_score(opportunity)
    components = dict(latest.components or {})
    components.pop("listing", None)
    score = score_opportunity(
        demand=latest.demand,
        timely=latest.timely_score,
        trend=latest.trend_score,
        execution=latest.execution,
        marketplace_fit_prior=latest.marketplace_fit_prior,
        lead_days=int(components.get("lead_days", 0)),
        sensitivity=Sensitivity(components.get("sensitivity", Sensitivity.LOW.value)),
        listing=listing_facts(match),
    )
    record_score(opportunity, score, components, match)
    await session.commit()
    await session.refresh(match)
    return to_match(match)


async def log_search_failure(
    session: AsyncSession, opportunity_id: str, payload: SearchFailureCreate
) -> SearchFailureView:
    if await session.get(Opportunity, opportunity_id) is None:
        raise NotFound("Opportunity not found")
    failure = ListingSearchFailure(
        opportunity_id=opportunity_id,
        marketplace=payload.marketplace,
        query=payload.query.strip(),
        reason=payload.reason,
        note=payload.note,
    )
    session.add(failure)
    await session.commit()
    await session.refresh(failure)
    return to_search_failure(failure)

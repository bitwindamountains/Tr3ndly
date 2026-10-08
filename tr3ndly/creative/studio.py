"""Write and read side for briefs, copy variants, review, and export.

State rules:
- A brief needs a confirmed listing with at least one verified fact.
- Generated and edited copy is checked by `policy.check_copy`; blocking issues prevent approval.
- Edits never overwrite a variant: they create a new one whose parent is the edited one.
- Export needs an approved variant and a listing re-confirmed within LISTING_RECHECK_HOURS. It
  assigns a tracking code for the affiliate link's sub ID and always appends the disclosure.
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.config import Settings
from tr3ndly.creative.copywriter import BriefInput, Copywriter, copywriter_name
from tr3ndly.creative.policy import check_copy, has_blocking, normalize_hashtags
from tr3ndly.db.models import (
    CreativeBrief,
    CreativeReview,
    CreativeStatus,
    CreativeVariant,
    Opportunity,
    OpportunityEvidence,
    ProductMatch,
    ProductMatchStatus,
    ReviewDecision,
)
from tr3ndly.db.types import utcnow
from tr3ndly.errors import Conflict, NotFound
from tr3ndly.intelligence.catalog import CONCEPTS_BY_KEY
from tr3ndly.opportunities.views import to_match, to_summary
from tr3ndly.schemas import (
    CreativeBriefCreate,
    CreativeBriefView,
    CreativeReviewCreate,
    CreativeVariantView,
    ExportPackage,
    PolicyIssue,
    StudioView,
)

BRIEF_VERSION = "brief-v1"
# Always forbidden, on top of the product concept's own list.
STANDARD_FORBIDDEN_CLAIMS = (
    "prices, discounts, or vouchers",
    "superlatives such as best or #1",
    "urgency or scarcity",
    "health, safety, or guarantee claims",
    "fear or disaster framing",
    "personal use of the product",
)
OCCASION_BY_EVENT = {
    "HEAT": "the hot days ahead",
    "HEAVY_RAIN": "the rainy days ahead",
    "SALE_DAY": "the next sale day",
    "PAYDAY": "payday",
    "GIFTING": "gift season",
    "BACK_TO_SCHOOL": "back to school",
}


async def _load_match(session: AsyncSession, match_id: str) -> ProductMatch:
    match = await session.scalar(
        select(ProductMatch)
        .where(ProductMatch.id == match_id)
        .options(selectinload(ProductMatch.opportunity).selectinload(Opportunity.event_cluster))
    )
    if match is None:
        raise NotFound("Product match not found")
    return match


async def create_brief(
    session: AsyncSession, match_id: str, payload: CreativeBriefCreate, settings: Settings
) -> CreativeBriefView:
    match = await _load_match(session, match_id)
    if match.status != ProductMatchStatus.CONFIRMED:
        raise Conflict("Confirm the listing before writing a brief")
    if not match.verified_facts:
        raise Conflict(
            "This listing has no verified facts. Add it again with facts copied from the listing."
        )
    opportunity = match.opportunity
    concept = CONCEPTS_BY_KEY.get(opportunity.concept_key or "")
    event_type = opportunity.event_cluster.event_type if opportunity.event_cluster else ""
    occasion = OCCASION_BY_EVENT.get(event_type, "this week")
    brief = CreativeBrief(
        product_match_id=match.id,
        platform=payload.platform,
        audience=(payload.audience or opportunity.target_user).strip(),
        angle=(
            payload.angle or f"A practical {opportunity.product_concept.lower()} for {occasion}."
        ).strip(),
        verified_facts=list(match.verified_facts),
        forbidden_claims=[
            *(concept.claims_to_avoid if concept else ()),
            *STANDARD_FORBIDDEN_CLAIMS,
        ],
        disclosure=settings.affiliate_disclosure,
        hypothesis=payload.hypothesis,
        experiment_label=payload.experiment_label,
        version=BRIEF_VERSION,
        variants=[],
    )
    session.add(brief)
    await session.commit()
    return to_brief(brief)


async def generate_variants(
    session: AsyncSession, brief_id: str, copywriter: Copywriter
) -> list[CreativeVariantView]:
    brief = await session.scalar(
        select(CreativeBrief)
        .where(CreativeBrief.id == brief_id)
        .options(selectinload(CreativeBrief.product_match).selectinload(ProductMatch.opportunity))
    )
    if brief is None:
        raise NotFound("Creative brief not found")
    match = brief.product_match
    if match.status != ProductMatchStatus.CONFIRMED:
        raise Conflict("The listing was replaced. Write a brief for the current listing.")

    batch = await copywriter.write(
        BriefInput(
            product_name=match.opportunity.product_concept,
            category=match.opportunity.category,
            platform=brief.platform,
            audience=brief.audience,
            angle=brief.angle,
            verified_facts=tuple(brief.verified_facts),
            forbidden_claims=tuple(brief.forbidden_claims),
        )
    )
    variants: list[CreativeVariant] = []
    for draft in batch.drafts:
        hashtags = normalize_hashtags(draft.hashtags)
        variant = CreativeVariant(
            brief_id=brief.id,
            hook_type=draft.hook_type,
            hook=draft.hook.strip(),
            caption=draft.caption.strip(),
            cta=draft.cta.strip(),
            hashtags=hashtags,
            generator=batch.generator,
            prompt_version=batch.prompt_version,
            generation=batch.generation,
            policy_issues=check_copy(
                hook=draft.hook,
                caption=draft.caption,
                cta=draft.cta,
                hashtags=hashtags,
                verified_facts=brief.verified_facts,
            ),
            status=CreativeStatus.NEEDS_REVIEW,
        )
        session.add(variant)
        variants.append(variant)
    await session.commit()
    return [to_variant(variant) for variant in variants]


async def review_variant(
    session: AsyncSession, variant_id: str, payload: CreativeReviewCreate
) -> CreativeVariantView:
    variant = await session.scalar(
        select(CreativeVariant)
        .where(CreativeVariant.id == variant_id)
        .options(selectinload(CreativeVariant.brief))
    )
    if variant is None:
        raise NotFound("Creative variant not found")
    if variant.status not in (CreativeStatus.NEEDS_REVIEW, CreativeStatus.APPROVED):
        raise Conflict(f"A {variant.status.value} variant cannot be reviewed; edit a copy instead")

    target = variant
    if payload.edits is not None:
        hashtags = normalize_hashtags(payload.edits.hashtags)
        target = CreativeVariant(
            brief_id=variant.brief_id,
            parent_id=variant.id,
            hook_type=variant.hook_type,
            hook=payload.edits.hook.strip(),
            caption=payload.edits.caption.strip(),
            cta=payload.edits.cta.strip(),
            hashtags=hashtags,
            generator="operator",
            prompt_version=None,
            policy_issues=check_copy(
                hook=payload.edits.hook,
                caption=payload.edits.caption,
                cta=payload.edits.cta,
                hashtags=hashtags,
                verified_facts=variant.brief.verified_facts,
            ),
            status=CreativeStatus.NEEDS_REVIEW,
        )
        session.add(target)

    decision = ReviewDecision(payload.decision)
    if decision == ReviewDecision.APPROVED and has_blocking(target.policy_issues):
        # Keep the edit so the operator can keep working on it.
        await session.commit()
        blocking = sum(1 for issue in target.policy_issues if issue.get("blocking"))
        raise Conflict(f"Fix {blocking} flagged claim(s) before approving")

    target.status = (
        CreativeStatus.APPROVED if decision == ReviewDecision.APPROVED else CreativeStatus.REJECTED
    )
    await session.flush()
    session.add(CreativeReview(variant_id=target.id, decision=decision, note=payload.note))
    await session.commit()
    return to_variant(target)


async def export_variant(
    session: AsyncSession, variant_id: str, settings: Settings, now: datetime | None = None
) -> ExportPackage:
    now = now or utcnow()
    variant = await _load_variant_for_export(session, variant_id)
    if variant.status not in (CreativeStatus.APPROVED, CreativeStatus.EXPORTED):
        raise Conflict("Approve the variant before exporting it")
    match = variant.brief.product_match
    if match.status != ProductMatchStatus.CONFIRMED:
        raise Conflict("The listing was replaced. Write copy for the current listing.")
    window = timedelta(hours=settings.listing_recheck_hours)
    if match.eligibility_checked_at is None or now - match.eligibility_checked_at > window:
        raise Conflict(
            f"The listing was last checked over {settings.listing_recheck_hours} hours ago. "
            "Open it, check it is live, and confirm it again."
        )
    if variant.tracking_code is None:
        variant.tracking_code = new_tracking_code()
    variant.status = CreativeStatus.EXPORTED
    variant.exported_at = variant.exported_at or now
    await session.commit()
    return to_export(variant)


async def get_export(session: AsyncSession, variant_id: str) -> ExportPackage:
    variant = await _load_variant_for_export(session, variant_id)
    if variant.status != CreativeStatus.EXPORTED:
        raise NotFound("This variant has not been exported")
    return to_export(variant)


async def studio(session: AsyncSession, match_id: str, settings: Settings) -> StudioView:
    match = await session.scalar(
        select(ProductMatch)
        .where(ProductMatch.id == match_id)
        .options(
            selectinload(ProductMatch.opportunity)
            .selectinload(Opportunity.evidence)
            .selectinload(OpportunityEvidence.raw_signal),
            selectinload(ProductMatch.opportunity).selectinload(Opportunity.scores),
            selectinload(ProductMatch.briefs).selectinload(CreativeBrief.variants),
        )
    )
    if match is None:
        raise NotFound("Product match not found")
    briefs = sorted(match.briefs, key=lambda brief: brief.created_at, reverse=True)
    return StudioView(
        opportunity=to_summary(match.opportunity),
        product_match=to_match(match),
        generator=copywriter_name(settings),
        briefs=[to_brief(brief) for brief in briefs],
    )


def new_tracking_code() -> str:
    # Short and alphanumeric, so it fits marketplace sub-ID fields.
    return f"t3{secrets.token_hex(4)}"


async def _load_variant_for_export(session: AsyncSession, variant_id: str) -> CreativeVariant:
    variant = await session.scalar(
        select(CreativeVariant)
        .where(CreativeVariant.id == variant_id)
        .options(selectinload(CreativeVariant.brief).selectinload(CreativeBrief.product_match))
    )
    if variant is None:
        raise NotFound("Creative variant not found")
    return variant


def post_text(variant: CreativeVariant, disclosure: str) -> str:
    parts = [variant.hook, variant.caption, variant.cta, disclosure]
    if variant.hashtags:
        parts.append(" ".join(variant.hashtags))
    return "\n\n".join(part for part in parts if part)


def to_export(variant: CreativeVariant) -> ExportPackage:
    brief = variant.brief
    match = brief.product_match
    assert variant.tracking_code is not None and variant.exported_at is not None
    checklist = [
        f'Create your affiliate link with sub ID "{variant.tracking_code}" so sales from this '
        "post trace back to it.",
        "Turn on the platform's branded or commercial content disclosure setting.",
        "Use the listing's own photos or real footage of the product; do not change how it looks.",
        "Open the listing just before posting to check it is still live. Do not state a price.",
        "Keep the disclosure line in the caption.",
    ]
    if brief.experiment_label:
        checklist.append(f'Label this post "{brief.experiment_label}" in your results.')
    return ExportPackage(
        variant_id=variant.id,
        tracking_code=variant.tracking_code,
        platform=brief.platform,
        post_text=post_text(variant, brief.disclosure),
        disclosure=brief.disclosure,
        affiliate_url=match.affiliate_url,
        product_url=match.product_url,
        image_url=match.image_url,
        image_usage_note=match.image_usage_note,
        checklist=checklist,
        exported_at=variant.exported_at,
    )


def to_variant(variant: CreativeVariant) -> CreativeVariantView:
    return CreativeVariantView(
        id=variant.id,
        brief_id=variant.brief_id,
        parent_id=variant.parent_id,
        hook_type=variant.hook_type,
        hook=variant.hook,
        caption=variant.caption,
        cta=variant.cta,
        hashtags=variant.hashtags,
        generator=variant.generator,
        prompt_version=variant.prompt_version,
        policy_issues=[PolicyIssue(**issue) for issue in variant.policy_issues],
        status=variant.status.value,
        tracking_code=variant.tracking_code,
        exported_at=variant.exported_at,
        created_at=variant.created_at,
    )


def to_brief(brief: CreativeBrief) -> CreativeBriefView:
    variants = sorted(brief.variants, key=lambda item: item.created_at, reverse=True)
    return CreativeBriefView(
        id=brief.id,
        product_match_id=brief.product_match_id,
        platform=brief.platform,
        audience=brief.audience,
        angle=brief.angle,
        verified_facts=brief.verified_facts,
        forbidden_claims=brief.forbidden_claims,
        disclosure=brief.disclosure,
        hypothesis=brief.hypothesis,
        experiment_label=brief.experiment_label,
        version=brief.version,
        created_at=brief.created_at,
        variants=[to_variant(variant) for variant in variants],
    )

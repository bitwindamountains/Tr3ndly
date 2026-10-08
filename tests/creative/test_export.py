from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tr3ndly.config import Settings
from tr3ndly.creative.copywriter import TemplateCopywriter
from tr3ndly.creative.studio import create_brief, export_variant, generate_variants, review_variant
from tr3ndly.db.models import OpportunityStatus
from tr3ndly.db.types import utcnow
from tr3ndly.errors import Conflict
from tr3ndly.opportunities.demo import build_demo_opportunity
from tr3ndly.opportunities.listings import add_product_match, confirm_product_match
from tr3ndly.schemas import CreativeBriefCreate, CreativeReviewCreate, ProductMatchCreate


async def test_export_requires_a_recently_rechecked_listing(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    settings = Settings(listing_recheck_hours=72)
    checked = utcnow()
    async with sessions() as session:
        opportunity = build_demo_opportunity(checked)
        opportunity.status = OpportunityStatus.ACCEPTED
        session.add(opportunity)
        await session.commit()
        match = await add_product_match(
            session,
            opportunity.id,
            ProductMatchCreate(
                marketplace="lazada",
                product_url="https://www.lazada.com.ph/products/fan-i1.html",
                affiliate_url="https://c.lazada.com.ph/t/abc",
                listing_title="Handheld fan",
                price_php=Decimal("299.50"),
                commission_rate_pct=Decimal("6"),
                verified_facts=["USB-C charging"],
            ),
        )
        await confirm_product_match(session, match.id, now=checked)
        brief = await create_brief(
            session, match.id, CreativeBriefCreate(platform="instagram"), settings
        )
        variant = (await generate_variants(session, brief.id, TemplateCopywriter()))[0]
        await review_variant(session, variant.id, CreativeReviewCreate(decision="approved"))

        with pytest.raises(Conflict, match="72 hours"):
            await export_variant(session, variant.id, settings, now=checked + timedelta(hours=73))

        # Re-confirming the listing refreshes the check, and export then succeeds.
        later = checked + timedelta(hours=73)
        await confirm_product_match(session, match.id, now=later)
        package = await export_variant(session, variant.id, settings, now=later)
    assert package.tracking_code.startswith("t3")
    assert package.post_text.count(settings.affiliate_disclosure) == 1

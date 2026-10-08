"""Results: CSV import of affiliate reports and the assisted-versus-baseline overview.

Rows are keyed by tracking code (the affiliate link's sub ID) and day. Observations are
append-only: a re-import with changed numbers adds a row, and the newest row for a code and day
wins. Codes Tr3ndly did not issue are baseline (unassisted) posts.
"""

import csv
import io
import re
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tr3ndly.db.models import (
    CreativeBrief,
    CreativeStatus,
    CreativeVariant,
    MetricObservation,
    Opportunity,
    ProductMatch,
)
from tr3ndly.errors import InvalidInput
from tr3ndly.schemas import ResultGroup, ResultsImportResult, ResultsOverview, ResultTotals

MAX_ROWS = 5000
# Below this many assisted posts, differences are mostly noise (plan section 15).
MIN_POSTS_FOR_COMPARISON = 30
METRICS = ("views", "clicks", "orders", "gmv_centavos", "commission_centavos")

# Column names accepted for each field, after lower-casing and turning spaces into underscores.
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "tracking_code": ("tracking_code", "sub_id", "subid", "sub_id1", "sub_id_1"),
    "date": ("date", "day", "observed_on", "report_date", "order_date"),
    "views": ("views", "video_views", "impressions"),
    "clicks": ("clicks", "link_clicks", "affiliate_clicks"),
    "orders": ("orders", "order_count", "conversions"),
    "gmv": ("gmv", "sales", "gross_sales", "order_amount"),
    "commission": ("commission", "estimated_commission", "total_commission", "commission_php"),
}


async def import_results(
    session: AsyncSession, csv_text: str, source: str = "csv"
) -> ResultsImportResult:
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("﻿")))
    columns = _map_columns(reader.fieldnames or [])
    if "tracking_code" not in columns or "date" not in columns:
        raise InvalidInput("The CSV needs a tracking code (or sub ID) column and a date column")

    parsed: list[dict[str, object]] = []
    errors: list[str] = []
    for line, row in enumerate(reader, start=2):
        if line - 1 > MAX_ROWS:
            raise InvalidInput(
                f"The CSV has more than {MAX_ROWS} rows; split it into smaller files"
            )
        try:
            parsed.append(_parse_row(row, columns))
        except ValueError as error:
            errors.append(f"Line {line}: {error}")

    codes = {str(item["tracking_code"]) for item in parsed}
    variants = {
        variant.tracking_code: variant.id
        for variant in await session.scalars(
            select(CreativeVariant).where(CreativeVariant.tracking_code.in_(codes))
        )
    }
    latest: dict[tuple[str, date], MetricObservation] = {}
    for observation in await session.scalars(
        select(MetricObservation)
        .where(MetricObservation.tracking_code.in_(codes))
        .order_by(MetricObservation.created_at)
    ):
        latest[(observation.tracking_code, observation.observed_on)] = observation

    batch = str(uuid.uuid4())
    imported = unchanged = 0
    for item in parsed:
        code = str(item["tracking_code"])
        day = item["observed_on"]
        assert isinstance(day, date)
        previous = latest.get((code, day))
        if previous is not None and all(
            getattr(previous, metric) == item[metric] for metric in METRICS
        ):
            unchanged += 1
            continue
        observation = MetricObservation(
            tracking_code=code,
            variant_id=variants.get(code),
            observed_on=day,
            source=source,
            import_batch=batch,
            **{metric: item[metric] for metric in METRICS},
        )
        session.add(observation)
        latest[(code, day)] = observation
        imported += 1
    await session.commit()
    return ResultsImportResult(
        rows=len(parsed) + len(errors),
        imported=imported,
        unchanged=unchanged,
        baseline_codes=sorted(codes - set(variants))[:50],
        errors=errors[:50],
    )


@dataclass
class _Sums:
    views: int = 0
    clicks: int = 0
    orders: int = 0
    gmv_centavos: int = 0
    commission_centavos: int = 0

    def add(self, observation: MetricObservation) -> None:
        for metric in METRICS:
            setattr(self, metric, getattr(self, metric) + (getattr(observation, metric) or 0))


async def results_overview(session: AsyncSession) -> ResultsOverview:
    newest: dict[tuple[str, date], MetricObservation] = {}
    for observation in await session.scalars(
        select(MetricObservation).order_by(MetricObservation.created_at)
    ):
        newest[(observation.tracking_code, observation.observed_on)] = observation
    per_code: dict[str, _Sums] = defaultdict(_Sums)
    for (code, _), observation in newest.items():
        per_code[code].add(observation)

    variants = {
        variant.tracking_code: variant
        for variant in await session.scalars(
            select(CreativeVariant)
            .where(CreativeVariant.tracking_code.is_not(None))
            .options(
                selectinload(CreativeVariant.brief)
                .selectinload(CreativeBrief.product_match)
                .selectinload(ProductMatch.opportunity)
                .selectinload(Opportunity.event_cluster)
            )
        )
    }
    assisted = {code: sums for code, sums in per_code.items() if code in variants}
    baseline = {code: sums for code, sums in per_code.items() if code not in variants}

    def grouped(key_of: Callable[[CreativeVariant], str]) -> list[ResultGroup]:
        groups: dict[str, dict[str, _Sums]] = defaultdict(dict)
        for code, sums in assisted.items():
            groups[key_of(variants[code])][code] = sums
        return sorted(
            (ResultGroup(key=key, totals=_totals(members)) for key, members in groups.items()),
            key=lambda group: group.totals.commission_php,
            reverse=True,
        )

    warnings: list[str] = []
    exported_without_results = [
        code
        for code, variant in variants.items()
        if variant.status == CreativeStatus.EXPORTED and code not in per_code
    ]
    if exported_without_results:
        warnings.append(
            f"{len(exported_without_results)} exported post(s) have no imported results yet."
        )
    if not baseline:
        warnings.append(
            "No baseline (unassisted) posts imported yet, so there is nothing to compare against."
        )
    if 0 < len(assisted) < MIN_POSTS_FOR_COMPARISON:
        warnings.append(
            f"Only {len(assisted)} assisted post(s) so far. Treat differences as noise until "
            f"there are at least {MIN_POSTS_FOR_COMPARISON}."
        )

    return ResultsOverview(
        assisted=_totals(assisted),
        baseline=_totals(baseline),
        by_category=grouped(lambda variant: variant.brief.product_match.opportunity.category),
        by_event_type=grouped(_event_type),
        by_hook_type=grouped(lambda variant: variant.hook_type),
        warnings=warnings,
    )


def _event_type(variant: CreativeVariant) -> str:
    cluster = variant.brief.product_match.opportunity.event_cluster
    return cluster.event_type if cluster else "unknown"


def _totals(per_code: dict[str, _Sums]) -> ResultTotals:
    total = _Sums()
    for sums in per_code.values():
        for metric in METRICS:
            setattr(total, metric, getattr(total, metric) + getattr(sums, metric))
    posts = len(per_code)
    commission = total.commission_centavos / 100
    return ResultTotals(
        posts=posts,
        views=total.views,
        clicks=total.clicks,
        orders=total.orders,
        gmv_php=total.gmv_centavos / 100,
        commission_php=commission,
        commission_per_post_php=round(commission / posts, 2) if posts else None,
        commission_per_1000_views_php=(
            round(commission * 1000 / total.views, 2) if total.views else None
        ),
        click_through_rate=round(total.clicks / total.views, 4) if total.views else None,
        conversion_rate=round(total.orders / total.clicks, 4) if total.clicks else None,
    )


def _map_columns(fieldnames: list[str]) -> dict[str, str]:
    normalized = {re.sub(r"[\s\-]+", "_", name.strip().lower()): name for name in fieldnames}
    columns: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                columns[field] = normalized[alias]
                break
    return columns


def _parse_row(row: dict[str, str | None], columns: dict[str, str]) -> dict[str, object]:
    def cell(field: str) -> str:
        return (row.get(columns[field]) or "").strip() if field in columns else ""

    code = cell("tracking_code")
    if not code:
        raise ValueError("missing tracking code")
    if len(code) > 80:
        raise ValueError("tracking code is longer than 80 characters")
    return {
        "tracking_code": code,
        "observed_on": _parse_date(cell("date")),
        "views": _parse_int(cell("views"), "views"),
        "clicks": _parse_int(cell("clicks"), "clicks"),
        "orders": _parse_int(cell("orders"), "orders"),
        "gmv_centavos": _parse_money(cell("gmv"), "GMV"),
        "commission_centavos": _parse_money(cell("commission"), "commission"),
    }


def _parse_date(text: str) -> date:
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"unreadable date {text!r}; use YYYY-MM-DD or MM/DD/YYYY")


def _parse_int(text: str, name: str) -> int | None:
    if not text:
        return None
    try:
        value = int(text.replace(",", ""))
    except ValueError:
        raise ValueError(f"{name} is not a whole number: {text!r}") from None
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def _parse_money(text: str, name: str) -> int | None:
    cleaned = re.sub(r"(?i)php|₱|,|\s", "", text)
    if not cleaned:
        return None
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"{name} is not an amount: {text!r}") from None
    if amount < 0:
        raise ValueError(f"{name} cannot be negative")
    return int((amount * 100).to_integral_value())

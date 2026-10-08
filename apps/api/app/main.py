from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.auth import require_operator
from apps.api.app.database import get_session
from tr3ndly import __version__
from tr3ndly.config import Settings, get_settings
from tr3ndly.creative import studio
from tr3ndly.creative.copywriter import Copywriter, build_copywriter
from tr3ndly.db.models import OpportunityReason
from tr3ndly.db.session import dispose_engine
from tr3ndly.db.types import utcnow
from tr3ndly.errors import Conflict, InvalidInput, NotFound, UpstreamError
from tr3ndly.log import configure_logging
from tr3ndly.operations import recent_runs, source_statuses
from tr3ndly.opportunities import listings
from tr3ndly.opportunities.decisions import (
    DecisionNotAllowed,
    OpportunityNotFound,
    record_decision,
)
from tr3ndly.opportunities.queries import OpportunityQueries
from tr3ndly.results import import_results, results_overview
from tr3ndly.schemas import (
    CreativeBriefCreate,
    CreativeBriefView,
    CreativeReviewCreate,
    CreativeVariantView,
    DecisionCreate,
    DecisionResponse,
    ExportPackage,
    HealthResponse,
    OpportunityDetail,
    ProductMatchConfirm,
    ProductMatchCreate,
    ProductMatchView,
    ResultsImport,
    ResultsImportResult,
    ResultsOverview,
    SearchFailureCreate,
    SearchFailureView,
    SourceRunView,
    SourceStatus,
    StudioView,
    TodayResponse,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_copywriter(config: AppSettings) -> Copywriter:
    return build_copywriter(config)


CopywriterDep = Annotated[Copywriter, Depends(get_copywriter)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_started", environment=settings.environment)
    yield
    await dispose_engine()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Evidence-to-opportunity API for Tr3ndly.",
    lifespan=lifespan,
)
# Only the Next.js server calls the API, so there is no CORS. Everything except /health
# requires the operator token when one is configured.
protected = APIRouter(dependencies=[Depends(require_operator)])

ERROR_STATUS: dict[type[Exception], int] = {
    NotFound: status.HTTP_404_NOT_FOUND,
    Conflict: status.HTTP_409_CONFLICT,
    InvalidInput: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UpstreamError: status.HTTP_502_BAD_GATEWAY,
}


async def domain_error(_: Request, error: Exception) -> JSONResponse:
    if isinstance(error, UpstreamError):
        logger.warning("upstream_error", error=str(error), cause=repr(error.__cause__))
    return JSONResponse(status_code=ERROR_STATUS[type(error)], content={"detail": str(error)})


for error_type in ERROR_STATUS:
    app.add_exception_handler(error_type, domain_error)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        version=app.version,
    )


@protected.get("/today", response_model=TodayResponse, tags=["opportunities"])
async def today(
    session: DatabaseSession,
    config: AppSettings,
    location: Annotated[str | None, Query(max_length=160)] = None,
    reason_type: OpportunityReason | None = None,
) -> TodayResponse:
    """Return the ranked opportunity queue, timely signals, and source health."""
    return await OpportunityQueries(session, config).today(
        location=location, reason_type=reason_type
    )


@protected.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetail,
    tags=["opportunities"],
)
async def opportunity_detail(
    opportunity_id: str,
    session: DatabaseSession,
    config: AppSettings,
) -> OpportunityDetail:
    opportunity = await OpportunityQueries(session, config).detail(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@protected.post(
    "/opportunities/{opportunity_id}/decision",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["opportunities"],
)
async def create_decision(
    opportunity_id: str,
    payload: DecisionCreate,
    session: DatabaseSession,
) -> DecisionResponse:
    try:
        return await record_decision(session, opportunity_id, payload)
    except OpportunityNotFound:
        raise HTTPException(status_code=404, detail="Opportunity not found") from None
    except DecisionNotAllowed as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@protected.post(
    "/opportunities/{opportunity_id}/product-match",
    response_model=ProductMatchView,
    status_code=status.HTTP_201_CREATED,
    tags=["listings"],
)
async def add_product_match(
    opportunity_id: str, payload: ProductMatchCreate, session: DatabaseSession
) -> ProductMatchView:
    return await listings.add_product_match(session, opportunity_id, payload)


@protected.post(
    "/product-matches/{match_id}/confirm", response_model=ProductMatchView, tags=["listings"]
)
async def confirm_product_match(
    match_id: str, _: ProductMatchConfirm, session: DatabaseSession
) -> ProductMatchView:
    return await listings.confirm_product_match(session, match_id)


@protected.post(
    "/opportunities/{opportunity_id}/search-failures",
    response_model=SearchFailureView,
    status_code=status.HTTP_201_CREATED,
    tags=["listings"],
)
async def log_search_failure(
    opportunity_id: str, payload: SearchFailureCreate, session: DatabaseSession
) -> SearchFailureView:
    return await listings.log_search_failure(session, opportunity_id, payload)


@protected.get("/product-matches/{match_id}/studio", response_model=StudioView, tags=["creative"])
async def get_studio(match_id: str, session: DatabaseSession, config: AppSettings) -> StudioView:
    return await studio.studio(session, match_id, config)


@protected.post(
    "/product-matches/{match_id}/creative-brief",
    response_model=CreativeBriefView,
    status_code=status.HTTP_201_CREATED,
    tags=["creative"],
)
async def create_creative_brief(
    match_id: str, payload: CreativeBriefCreate, session: DatabaseSession, config: AppSettings
) -> CreativeBriefView:
    return await studio.create_brief(session, match_id, payload, config)


@protected.post(
    "/creative-briefs/{brief_id}/generate",
    response_model=list[CreativeVariantView],
    status_code=status.HTTP_201_CREATED,
    tags=["creative"],
)
async def generate_creatives(
    brief_id: str, session: DatabaseSession, copywriter: CopywriterDep
) -> list[CreativeVariantView]:
    return await studio.generate_variants(session, brief_id, copywriter)


@protected.post(
    "/creatives/{variant_id}/review", response_model=CreativeVariantView, tags=["creative"]
)
async def review_creative(
    variant_id: str, payload: CreativeReviewCreate, session: DatabaseSession
) -> CreativeVariantView:
    return await studio.review_variant(session, variant_id, payload)


@protected.post("/creatives/{variant_id}/export", response_model=ExportPackage, tags=["creative"])
async def export_creative(
    variant_id: str, session: DatabaseSession, config: AppSettings
) -> ExportPackage:
    return await studio.export_variant(session, variant_id, config)


@protected.get("/creatives/{variant_id}/export", response_model=ExportPackage, tags=["creative"])
async def get_creative_export(variant_id: str, session: DatabaseSession) -> ExportPackage:
    return await studio.get_export(session, variant_id)


@protected.post("/results/import", response_model=ResultsImportResult, tags=["results"])
async def import_results_csv(
    payload: ResultsImport, session: DatabaseSession
) -> ResultsImportResult:
    return await import_results(session, payload.csv)


@protected.get("/results/overview", response_model=ResultsOverview, tags=["results"])
async def get_results_overview(session: DatabaseSession) -> ResultsOverview:
    return await results_overview(session)


@protected.get("/operations/sources", response_model=list[SourceStatus], tags=["operations"])
async def operations_sources(session: DatabaseSession, config: AppSettings) -> list[SourceStatus]:
    return await source_statuses(session, config, utcnow())


@protected.get("/operations/runs", response_model=list[SourceRunView], tags=["operations"])
async def operations_runs(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SourceRunView]:
    return await recent_runs(session, limit)


app.include_router(protected)

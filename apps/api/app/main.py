from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_session
from tr3ndly import __version__
from tr3ndly.config import Settings, get_settings
from tr3ndly.db.session import dispose_engine
from tr3ndly.db.types import utcnow
from tr3ndly.log import configure_logging
from tr3ndly.operations import recent_runs, source_statuses
from tr3ndly.opportunities.repository import (
    DecisionNotAllowed,
    OpportunityNotFound,
    OpportunityRepository,
)
from tr3ndly.schemas import (
    DecisionCreate,
    DecisionResponse,
    HealthResponse,
    OpportunityDetail,
    SourceRunView,
    SourceStatus,
    TodayResponse,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        version=app.version,
    )


@app.get("/today", response_model=TodayResponse, tags=["opportunities"])
async def today(session: DatabaseSession, config: AppSettings) -> TodayResponse:
    """Return the ranked opportunity queue, timely signals, and source health."""
    return await OpportunityRepository(session, config).get_today()


@app.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetail,
    tags=["opportunities"],
)
async def opportunity_detail(
    opportunity_id: str,
    session: DatabaseSession,
    config: AppSettings,
) -> OpportunityDetail:
    opportunity = await OpportunityRepository(session, config).get_detail(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@app.post(
    "/opportunities/{opportunity_id}/decision",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["opportunities"],
)
async def create_decision(
    opportunity_id: str,
    payload: DecisionCreate,
    session: DatabaseSession,
    config: AppSettings,
) -> DecisionResponse:
    try:
        return await OpportunityRepository(session, config).record_decision(opportunity_id, payload)
    except OpportunityNotFound:
        raise HTTPException(status_code=404, detail="Opportunity not found") from None
    except DecisionNotAllowed as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@app.get("/operations/sources", response_model=list[SourceStatus], tags=["operations"])
async def operations_sources(session: DatabaseSession, config: AppSettings) -> list[SourceStatus]:
    return await source_statuses(session, config, utcnow())


@app.get("/operations/runs", response_model=list[SourceRunView], tags=["operations"])
async def operations_runs(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SourceRunView]:
    return await recent_runs(session, limit)

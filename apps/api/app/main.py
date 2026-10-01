from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import get_settings
from apps.api.app.database import dispose_engine, get_session
from apps.api.app.logging import configure_logging
from apps.api.app.schemas import (
    DecisionCreate,
    DecisionResponse,
    HealthResponse,
    OpportunityDetail,
    TodayResponse,
)
from tr3ndly.opportunities.repository import OpportunityRepository

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_started", environment=settings.environment)
    yield
    await dispose_engine()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
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
async def today(session: DatabaseSession) -> TodayResponse:
    """Return active opportunities from the persistence layer."""
    return await OpportunityRepository(session).get_today()


@app.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetail,
    tags=["opportunities"],
)
async def opportunity_detail(
    opportunity_id: str,
    session: DatabaseSession,
) -> OpportunityDetail:
    opportunity = await OpportunityRepository(session).get_detail(opportunity_id)
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
) -> DecisionResponse:
    decision = await OpportunityRepository(session).record_decision(opportunity_id, payload)
    if decision is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return decision

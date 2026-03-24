"""Learning Management Service — FastAPI application."""

import logging
import traceback

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import verify_api_key
from app.database import engine
from app.etl import sync as etl_sync
from app.models.interaction import InteractionLog
from app.routers import analytics, interactions, items, learners, pipeline
from app.settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="A learning management service API.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    """Run ETL sync on startup if database is empty."""
    try:
        async with AsyncSession(engine) as session:
            # Check if we have any interactions
            count = (await session.exec(select(func.count(InteractionLog.id)))).one()
            if count == 0:
                logger.info("Database is empty, running ETL sync...")
                try:
                    result = await etl_sync(session)
                    logger.info(f"ETL sync completed: {result}")
                except Exception as e:
                    logger.error(f"ETL sync failed: {e}")
            else:
                logger.info(f"Database has {count} interactions, skipping ETL sync")
    except Exception as e:
        logger.error(f"Startup ETL check failed: {e}")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return error details in the response for easier debugging."""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": tb[-3:],  # last 3 lines of traceback
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    items.router,
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(verify_api_key)],
)

if settings.enable_interactions:
    app.include_router(
        interactions.router,
        prefix="/interactions",
        tags=["interactions"],
        dependencies=[Depends(verify_api_key)],
    )

if settings.enable_learners:
    app.include_router(
        learners.router,
        prefix="/learners",
        tags=["learners"],
        dependencies=[Depends(verify_api_key)],
    )

app.include_router(
    pipeline.router,
    prefix="/pipeline",
    tags=["pipeline"],
    dependencies=[Depends(verify_api_key)],
)

app.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(verify_api_key)],
)

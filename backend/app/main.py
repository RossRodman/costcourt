"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.debate.sessions import DebateManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.debates.aclose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Pass `settings` explicitly in tests to avoid env leakage."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="CostCourt API",
        description="CostCourt: AI-powered construction estimate review.",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.debates = DebateManager()
    app.include_router(api_router)
    return app

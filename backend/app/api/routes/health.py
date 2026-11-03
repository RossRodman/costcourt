from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.api.deps import SettingsDep

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    llm_configured: bool


@router.get("/health")
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        env=settings.env.value,
        llm_configured=settings.has_api_key,
    )

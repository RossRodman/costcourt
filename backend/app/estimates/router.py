from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.estimates.catalog import EstimateNotFoundError, SampleCatalog, get_sample_catalog
from app.estimates.models import Estimate, EstimateSummary

router = APIRouter(prefix="/estimates", tags=["estimates"])

CatalogDep = Annotated[SampleCatalog, Depends(get_sample_catalog)]


@router.get("/samples")
async def list_samples(catalog: CatalogDep) -> list[EstimateSummary]:
    """Built-in example estimates to try a debate on."""
    return catalog.list()


@router.get("/samples/{estimate_id}", responses={404: {"description": "Unknown sample id"}})
async def get_sample(estimate_id: str, catalog: CatalogDep) -> Estimate:
    try:
        return catalog.get(estimate_id)
    except EstimateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/preview")
async def preview(estimate: Estimate) -> Estimate:
    """Validate an uploaded estimate and return it with computed totals."""
    return estimate

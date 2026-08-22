"""API routes for analytics and metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.history import MetricsHistoryTracker
from backend.app.analytics.metrics import compute_city_metrics, compute_population_breakdown
from backend.app.core.database import get_db
from backend.app.schemas.analytics import CityMetrics, PopulationBreakdown

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/metrics", response_model=CityMetrics)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    return await compute_city_metrics(db)


@router.get("/population", response_model=PopulationBreakdown)
async def get_population_breakdown(db: AsyncSession = Depends(get_db)):
    return await compute_population_breakdown(db)


@router.get("/history")
async def get_metrics_history(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    tracker = MetricsHistoryTracker(db)
    return await tracker.get_history(limit)

"""API routes for traffic and transportation."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.traffic import TripRecord, TransitRoute
from backend.app.traffic.traffic_engine import TrafficEngine

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/stats")
async def traffic_stats(db: AsyncSession = Depends(get_db)):
    engine = TrafficEngine(db)
    return await engine.get_traffic_stats()


@router.get("/congestion")
async def congestion_map(db: AsyncSession = Depends(get_db)):
    engine = TrafficEngine(db)
    return await engine.get_congestion_map()


@router.get("/trips")
async def recent_trips(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TripRecord).order_by(desc(TripRecord.started_at)).limit(limit)
    )
    trips = list(result.scalars().all())
    return [
        {
            "id": str(t.id),
            "citizen_id": str(t.citizen_id),
            "vehicle_type": t.vehicle_type.value,
            "distance_m": round(t.distance_m, 1),
            "duration_min": round(t.duration_minutes, 1),
            "cost": t.cost,
            "congestion": round(t.congestion_experienced, 3),
            "started_at": t.started_at.isoformat() if t.started_at else None,
        }
        for t in trips
    ]


@router.get("/routes")
async def transit_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TransitRoute).where(TransitRoute.is_active == True)  # noqa: E712
    )
    routes = list(result.scalars().all())
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "type": r.route_type.value,
            "stops": r.stops,
            "frequency_min": r.frequency_minutes,
            "fare": r.fare,
            "capacity": r.capacity_per_vehicle,
        }
        for r in routes
    ]

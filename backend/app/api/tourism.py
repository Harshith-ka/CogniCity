"""Phase 6 API: Tourism endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.tourism import Hotel, TouristAttraction, TouristVisitor

router = APIRouter(prefix="/api/tourism", tags=["tourism"])


@router.get("/stats")
async def tourism_stats(db: AsyncSession = Depends(get_db)):
    hotels = await db.execute(select(sqlfunc.count()).select_from(Hotel))
    total_rooms = await db.execute(select(sqlfunc.sum(Hotel.total_rooms)).select_from(Hotel))
    occupied_rooms = await db.execute(select(sqlfunc.sum(Hotel.occupied_rooms)).select_from(Hotel))
    active_tourists = await db.execute(
        select(sqlfunc.count()).select_from(TouristVisitor).where(TouristVisitor.is_active.is_(True))
    )
    total_guests = await db.execute(select(sqlfunc.sum(Hotel.total_guests)).select_from(Hotel))
    attractions = await db.execute(select(sqlfunc.count()).select_from(TouristAttraction))
    daily_revenue = await db.execute(select(sqlfunc.sum(Hotel.daily_revenue)).select_from(Hotel))

    t_rooms = total_rooms.scalar() or 1
    o_rooms = occupied_rooms.scalar() or 0

    return {
        "total_hotels": hotels.scalar() or 0,
        "total_rooms": t_rooms,
        "occupied_rooms": o_rooms,
        "occupancy_rate": round(o_rooms / max(1, t_rooms), 3),
        "active_tourists": active_tourists.scalar() or 0,
        "total_guests_served": total_guests.scalar() or 0,
        "total_attractions": attractions.scalar() or 0,
        "daily_revenue": round(daily_revenue.scalar() or 0, 2),
    }


@router.get("/hotels")
async def list_hotels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hotel).order_by(Hotel.hotel_class.desc()))
    return [{
        "id": str(h.id),
        "name": h.name,
        "class": h.hotel_class,
        "total_rooms": h.total_rooms,
        "occupied_rooms": h.occupied_rooms,
        "occupancy_pct": round(h.occupied_rooms / max(1, h.total_rooms), 3),
        "price_per_night": h.price_per_night,
        "rating": h.rating,
        "amenities": h.amenities,
        "daily_revenue": round(h.daily_revenue, 2),
        "total_guests": h.total_guests,
    } for h in result.scalars().all()]


@router.get("/attractions")
async def list_attractions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TouristAttraction).order_by(TouristAttraction.popularity.desc()))
    return [{
        "id": str(a.id),
        "name": a.name,
        "type": a.attraction_type,
        "popularity": a.popularity,
        "ticket_price": a.ticket_price,
        "daily_visitors": a.daily_visitors,
        "total_visitors": a.total_visitors,
        "rating": a.rating,
        "capacity": a.capacity,
    } for a in result.scalars().all()]


@router.get("/visitors")
async def list_visitors(limit: int = 30, active_only: bool = True, db: AsyncSession = Depends(get_db)):
    query = select(TouristVisitor).order_by(TouristVisitor.arrived_at.desc())
    if active_only:
        query = query.where(TouristVisitor.is_active.is_(True))
    result = await db.execute(query.limit(limit))
    return [{
        "id": str(v.id),
        "origin": v.origin_country,
        "budget": v.budget,
        "spent": round(v.spent, 2),
        "satisfaction": round(v.satisfaction, 3),
        "ticks_remaining": v.ticks_remaining,
        "is_active": v.is_active,
    } for v in result.scalars().all()]

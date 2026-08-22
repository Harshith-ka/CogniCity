"""Phase 6 API: Culture & Entertainment endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.culture import Venue, CityFestival

router = APIRouter(prefix="/api/culture", tags=["culture"])


@router.get("/stats")
async def culture_stats(db: AsyncSession = Depends(get_db)):
    venues = await db.execute(select(sqlfunc.count()).select_from(Venue))
    open_venues = await db.execute(select(sqlfunc.count()).select_from(Venue).where(Venue.is_open.is_(True)))
    total_visitors = await db.execute(select(sqlfunc.sum(Venue.total_visitors)).select_from(Venue))
    total_revenue = await db.execute(select(sqlfunc.sum(Venue.daily_revenue)).select_from(Venue))
    active_festivals = await db.execute(
        select(sqlfunc.count()).select_from(CityFestival).where(CityFestival.is_active.is_(True))
    )
    total_festivals = await db.execute(select(sqlfunc.count()).select_from(CityFestival))

    return {
        "total_venues": venues.scalar() or 0,
        "open_venues": open_venues.scalar() or 0,
        "total_visitors": total_visitors.scalar() or 0,
        "daily_revenue": round(total_revenue.scalar() or 0, 2),
        "active_festivals": active_festivals.scalar() or 0,
        "total_festivals": total_festivals.scalar() or 0,
    }


@router.get("/venues")
async def list_venues(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Venue).order_by(Venue.popularity.desc()).limit(limit)
    )
    return [{
        "id": str(v.id),
        "name": v.name,
        "type": v.venue_type,
        "capacity": v.capacity,
        "popularity": v.popularity,
        "quality": v.quality,
        "ticket_price": v.ticket_price,
        "daily_revenue": v.daily_revenue,
        "total_visitors": v.total_visitors,
        "is_open": v.is_open,
    } for v in result.scalars().all()]


@router.get("/festivals")
async def list_festivals(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CityFestival).order_by(CityFestival.is_active.desc()).limit(limit)
    )
    return [{
        "id": str(f.id),
        "name": f.name,
        "type": f.event_type,
        "attendees": f.attendees,
        "max_attendees": f.max_attendees,
        "happiness_boost": f.happiness_boost,
        "is_active": f.is_active,
        "ticks_remaining": f.ticks_remaining,
        "duration_ticks": f.duration_ticks,
    } for f in result.scalars().all()]

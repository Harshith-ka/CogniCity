"""API routes for city structure — districts, locations, buildings."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.core.database import get_db
from backend.app.models.city import District, Location, Building

router = APIRouter(prefix="/city", tags=["city"])


@router.get("/districts")
async def list_districts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(District))
    districts = list(result.scalars().all())
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "population": d.population,
            "center_x": d.center_x,
            "center_y": d.center_y,
            "radius": d.radius,
            "safety_index": d.safety_index,
            "wealth_index": d.wealth_index,
            "pollution_index": d.pollution_index,
        }
        for d in districts
    ]


@router.get("/locations")
async def list_locations(
    district_name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Location)
    if district_name:
        query = query.join(District).where(District.name == district_name)

    result = await db.execute(query)
    locations = list(result.scalars().all())
    return [
        {
            "id": str(loc.id),
            "name": loc.name,
            "type": loc.location_type.value,
            "x": loc.x,
            "y": loc.y,
            "capacity": loc.capacity,
            "current_occupancy": loc.current_occupancy,
        }
        for loc in locations
    ]


@router.get("/buildings")
async def list_buildings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Building).options(
            joinedload(Building.location).joinedload(Location.district)
        )
    )
    buildings = list(result.unique().scalars().all())
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "type": b.building_type.value,
            "floors": b.floors,
            "condition": b.condition,
            "value": b.value,
            "x": b.location.x if b.location else 0.0,
            "y": b.location.y if b.location else 0.0,
            "location_type": b.location.location_type.value if b.location else None,
            "district_name": b.location.district.name if b.location and b.location.district else None,
        }
        for b in buildings
    ]


@router.get("/map")
async def city_map(db: AsyncSession = Depends(get_db)):
    """High-level city layout for visualization."""
    districts_result = await db.execute(select(District))
    districts = list(districts_result.scalars().all())

    locations_result = await db.execute(select(Location))
    locations = list(locations_result.scalars().all())

    return {
        "districts": [
            {
                "name": d.name,
                "center": [d.center_x, d.center_y],
                "radius": d.radius,
                "safety": d.safety_index,
                "wealth": d.wealth_index,
            }
            for d in districts
        ],
        "locations": [
            {
                "name": loc.name,
                "type": loc.location_type.value,
                "position": [loc.x, loc.y],
            }
            for loc in locations
        ],
    }

"""API routes for city structure — districts, locations, buildings."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.core.database import get_db
from backend.app.models.city import District, Location, Building
from backend.app.models.citizen import Citizen
from backend.app.models.infrastructure import UtilityGrid

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


class ExpandCityRequest(BaseModel):
    additional_population: int = 400


@router.post("/expand")
async def expand_city_endpoint(req: ExpandCityRequest, db: AsyncSession = Depends(get_db)):
    """Grow the city's map with new districts (not just denser existing ones) and
    populate everything — new and old districts alike — with new residents. Purely
    additive: existing citizens, relationships, and history are untouched."""
    from backend.app.engine.city_generator import expand_city, grow_city
    from backend.app.communication.relationship_engine import RelationshipEngine

    expand_stats = await expand_city(db)
    grow_result = await grow_city(db, additional_population=req.additional_population)
    new_citizens = grow_result.pop("new_citizens")

    rel_engine = RelationshipEngine(db)
    relationships_created = await rel_engine.seed_relationships(new_citizens)
    await db.commit()

    return {
        "status": "expanded",
        "new_districts": expand_stats["new_districts"],
        "new_buildings": expand_stats["buildings"] + grow_result["buildings"],
        "new_locations": expand_stats["locations"] + grow_result["locations"],
        "new_businesses": grow_result["businesses"],
        "new_citizens": len(new_citizens),
        "relationships_created": relationships_created,
    }


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


@router.get("/buildings/{building_id}/details")
async def get_building_details(building_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Full inspector detail for one building: who works/lives there right now, and
    any real issues — derived from the same condition/occupancy/utility data the rest
    of the sim already tracks, not invented separately for display purposes."""
    result = await db.execute(
        select(Building)
        .options(joinedload(Building.location).joinedload(Location.district))
        .where(Building.id == building_id)
    )
    building = result.unique().scalar_one_or_none()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    loc = building.location
    district = loc.district if loc else None

    employees, residents = [], []
    if loc:
        emp_result = await db.execute(
            select(Citizen).where(Citizen.workplace_id == loc.id, Citizen.is_alive.is_(True))
        )
        employees = [
            {"id": str(c.id), "name": c.name, "occupation": c.occupation, "happiness": round(c.happiness, 2)}
            for c in emp_result.scalars().all()
        ]
        res_result = await db.execute(
            select(Citizen).where(Citizen.home_location_id == loc.id, Citizen.is_alive.is_(True))
        )
        residents = [
            {"id": str(c.id), "name": c.name, "occupation": c.occupation}
            for c in res_result.scalars().all()
        ]

    issues = []
    if building.condition < 0.5:
        issues.append(f"Structural condition is poor ({round(building.condition * 100)}%) — needs maintenance")
    if loc and loc.capacity and loc.current_occupancy > loc.capacity:
        issues.append(f"Overcrowded — {loc.current_occupancy}/{loc.capacity} capacity")
    if building.building_type.value in ("office", "shop", "restaurant") and not employees:
        issues.append("No employees currently working here")

    if district:
        grid_result = await db.execute(select(UtilityGrid).where(UtilityGrid.district_id == district.id))
        for grid in grid_result.scalars().all():
            if not grid.is_operational:
                issues.append(f"{grid.utility_type.title()} outage affecting {district.name}")
            elif grid.health < 0.4:
                issues.append(f"{grid.utility_type.title()} grid reliability is low in {district.name}")

    return {
        "id": str(building.id),
        "name": building.name,
        "type": building.building_type.value,
        "floors": building.floors,
        "condition": building.condition,
        "value": building.value,
        "rent_cost": building.rent_cost,
        "district_name": district.name if district else None,
        "capacity": loc.capacity if loc else None,
        "current_occupancy": loc.current_occupancy if loc else None,
        "employees": employees,
        "employee_count": len(employees),
        "residents": residents,
        "resident_count": len(residents),
        "issues": issues,
    }


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

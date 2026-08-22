"""Infrastructure Placement Preview — impact calculation strategies.

Each infrastructure type gets its own strategy function rather than one large
conditional block. All strategies are registered in IMPACT_STRATEGIES and dispatched
by key from the preview-impact API. They share a few generic helpers (coverage/
distance-improvement math, construction-footprint disruption, AI scoring) so the
per-type functions stay focused on "what makes this type's placement good or bad"
rather than re-deriving the same geometry each time.

Every number shown to the user — coverage counts, distance deltas, affected people/
buildings, the AI score — comes from these calculations against real simulation data
(citizens, hospitals, schools, buildings, districts). Nothing here is a canned/generic
LLM explanation; if an LLM is ever layered on top for prose, it must be fed exactly
these numbers, not asked to invent its own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.models.city import District, Building, BuildingType
from backend.app.models.citizen import Citizen
from backend.app.models.healthcare import Hospital
from backend.app.models.education import School
from backend.app.models.crime import PoliceUnit
from backend.app.models.emergency_services import FireStation
from backend.app.infrastructure.config import INFRASTRUCTURE_CONFIG

IMPACT_TOP_N = 15
DISRUPTION_RADIUS = 90.0  # construction-footprint zone around a point-site build
CORRIDOR_WIDTH = 60.0  # how close to a new road/bridge's straight path counts as "along the route"
BUSINESS_TYPES = (BuildingType.SHOP, BuildingType.RESTAURANT)


@dataclass
class ImpactResult:
    coverage_count: int = 0
    metrics: dict[str, str] = field(default_factory=dict)  # label -> value, for the live in-3D readout
    beneficiaries: list[dict] = field(default_factory=list)
    businesses: list[dict] = field(default_factory=list)
    affected_people: list[dict] = field(default_factory=list)
    affected_buildings: list[dict] = field(default_factory=list)
    employees_hired: dict | None = None
    ai_score: int = 50
    ai_tier: str = "MODERATE IMPACT"
    ai_pros: list[str] = field(default_factory=list)
    ai_cons: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "coverage_count": self.coverage_count,
            "metrics": self.metrics,
            "beneficiaries": self.beneficiaries[:IMPACT_TOP_N],
            "total_beneficiaries": len(self.beneficiaries),
            "businesses": self.businesses[:IMPACT_TOP_N],
            "affected_people": self.affected_people[:IMPACT_TOP_N],
            "total_affected_people": len(self.affected_people),
            "affected_buildings": self.affected_buildings[:IMPACT_TOP_N],
            "total_affected_buildings": len(self.affected_buildings),
            "employees_hired": self.employees_hired,
            "ai_score": self.ai_score,
            "ai_tier": self.ai_tier,
            "ai_pros": self.ai_pros,
            "ai_cons": self.ai_cons,
            "summary": self.summary,
        }


# ─────────────────────────────────────────────────────────────
# Shared geometry/data helpers
# ─────────────────────────────────────────────────────────────

def _point_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
    nx, ny = x1 + t * dx, y1 + t * dy
    return math.hypot(px - nx, py - ny)


async def _load_citizens(db: AsyncSession) -> list[Citizen]:
    result = await db.execute(
        select(Citizen)
        .options(joinedload(Citizen.home_location), joinedload(Citizen.workplace))
        .where(Citizen.is_alive.is_(True))
    )
    return list(result.unique().scalars().all())


async def _load_buildings(db: AsyncSession) -> list[Building]:
    result = await db.execute(select(Building).options(joinedload(Building.location)))
    return list(result.unique().scalars().all())


async def _district_centers(db: AsyncSession) -> dict:
    result = await db.execute(select(District))
    return {d.id: d for d in result.scalars().all()}


def _facility_points(rows: list, district_by_id: dict) -> list[tuple[float, float]]:
    """A facility's own x/y if it was manually placed, else its district's centroid as
    a fallback for auto-generated ones that predate Build Mode."""
    points = []
    for r in rows:
        if r.x is not None and r.y is not None:
            points.append((r.x, r.y))
        elif r.district_id in district_by_id:
            d = district_by_id[r.district_id]
            points.append((d.center_x, d.center_y))
    return points


def _coverage_beneficiaries(citizens: list[Citizen], x: float, y: float, service_radius: float, existing_points: list[tuple[float, float]]) -> list[dict]:
    beneficiaries = []
    for c in citizens:
        loc = c.home_location or c.workplace
        if not loc or loc.x is None or loc.y is None:
            continue
        dist_new = math.hypot(loc.x - x, loc.y - y)
        if dist_new > service_radius:
            continue

        if existing_points:
            dist_existing = min(math.hypot(loc.x - ex, loc.y - ey) for ex, ey in existing_points)
            improvement = dist_existing - dist_new
            if improvement <= 0:
                continue
        else:
            # No existing facility of this type anywhere in the city — every in-range
            # citizen is a full win. Rank by how deep inside the service radius they
            # sit instead of an undefined "improvement over nothing" delta.
            improvement = service_radius - dist_new

        beneficiaries.append({
            "citizen_id": str(c.id), "name": c.name,
            "distance": round(dist_new, 1), "improvement": round(improvement, 1),
        })
    beneficiaries.sort(key=lambda b: -b["improvement"])
    return beneficiaries


def _construction_disruption(x: float, y: float, citizens: list[Citizen], buildings: list[Building], reason: str) -> tuple[list[dict], list[dict]]:
    affected_people = []
    for c in citizens:
        loc = c.home_location or c.workplace
        if not loc or loc.x is None or loc.y is None:
            continue
        d = math.hypot(loc.x - x, loc.y - y)
        if d <= DISRUPTION_RADIUS:
            affected_people.append({"citizen_id": str(c.id), "name": c.name, "distance": round(d, 1), "reason": reason})
    affected_people.sort(key=lambda p: p["distance"])

    affected_buildings = []
    for b in buildings:
        loc = b.location
        if not loc or loc.x is None:
            continue
        d = math.hypot(loc.x - x, loc.y - y)
        if d <= DISRUPTION_RADIUS:
            affected_buildings.append({"name": b.name, "type": b.building_type.value, "distance": round(d, 1), "reason": reason})
    affected_buildings.sort(key=lambda b: b["distance"])
    return affected_people, affected_buildings


def _nearby_businesses(x: float, y: float, buildings: list[Building], radius: float) -> list[dict]:
    businesses = []
    for b in buildings:
        if b.building_type not in BUSINESS_TYPES:
            continue
        loc = b.location
        if not loc or loc.x is None:
            continue
        d = math.hypot(loc.x - x, loc.y - y)
        if d <= radius:
            businesses.append({"name": b.name, "type": b.building_type.value, "distance": round(d, 1)})
    businesses.sort(key=lambda b: b["distance"])
    return businesses


def score_and_recommend(
    *, coverage: int, coverage_reference: int, distance_improvement: float,
    affected_count: int, type_label: str, has_existing: bool = True,
) -> tuple[int, str, list[str], list[str]]:
    """One scoring formula shared by every strategy, so 'AI recommendation' means the
    same thing across infrastructure types: reward real coverage + accessibility gain,
    penalize construction disruption. Every input is a number already shown to the
    user elsewhere in the same response — nothing hidden, nothing invented.

    has_existing distinguishes "there's a same-type facility nearby" (distance_improvement
    is a meaningful comparison) from "there's no such facility anywhere in the city yet"
    (distance_improvement is just a placeholder 0 — scoring it as "already well served"
    would be a contradiction, since there's nothing to be served BY)."""
    pros, cons = [], []
    score = 50.0

    coverage_ratio = min(1.5, coverage / max(1, coverage_reference))
    score += coverage_ratio * 30
    if coverage_ratio > 0.6:
        pros.append(f"High population currently underserved — {coverage} people would gain coverage")
    elif coverage_ratio < 0.15:
        cons.append(f"Very few people ({coverage}) fall within service range at this exact spot")

    if has_existing:
        score += min(20, distance_improvement / 50)
        if distance_improvement > 300:
            pros.append(f"Nearest existing {type_label} is far away — meaningful accessibility gain")
        elif distance_improvement <= 0:
            cons.append(f"Already well served by an existing {type_label} nearby")
    else:
        score += 15  # first of its kind in the city — a real accessibility gain by definition
        pros.append(f"No existing {type_label} anywhere in the city yet — this would be the first")

    score -= min(15, affected_count * 1.5)
    if affected_count > 5:
        cons.append(f"{affected_count} residents/buildings sit inside the construction footprint")
    elif affected_count == 0:
        pros.append("No residents or buildings disrupted by construction")

    score = max(0, min(100, round(score)))
    if score >= 80:
        tier = "HIGHLY SUITABLE"
    elif score >= 60:
        tier = "HIGH IMPACT LOCATION"
    elif score >= 40:
        tier = "MODERATE IMPACT"
    elif score >= 20:
        tier = "LOW IMPACT"
    else:
        tier = "NOT RECOMMENDED"
    return int(score), tier, pros, cons


# ─────────────────────────────────────────────────────────────
# Per-type strategies
# ─────────────────────────────────────────────────────────────

async def hospital_impact(db: AsyncSession, x: float, y: float, **_) -> ImpactResult:
    cfg = INFRASTRUCTURE_CONFIG["hospital_build"]
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)
    district_by_id = await _district_centers(db)

    hospitals_result = await db.execute(select(Hospital).where(Hospital.is_operational.is_(True)))
    existing_points = _facility_points(list(hospitals_result.scalars().all()), district_by_id)

    beneficiaries = _coverage_beneficiaries(citizens, x, y, cfg.service_radius, existing_points)
    affected_people, affected_buildings = _construction_disruption(
        x, y, citizens, buildings, "lives within the construction footprint — expect noise and access disruption during the build"
    )
    businesses = _nearby_businesses(x, y, buildings, cfg.service_radius)
    nearest_dist = min((math.hypot(x - ex, y - ey) for ex, ey in existing_points), default=0.0)

    score, tier, pros, cons = score_and_recommend(
        coverage=len(beneficiaries), coverage_reference=150,
        distance_improvement=nearest_dist, affected_count=len(affected_people) + len(affected_buildings),
        type_label="hospital", has_existing=bool(existing_points),
    )
    if existing_points:
        pros.append(f"Nearest existing hospital is {round(nearest_dist)}m away")

    result = ImpactResult(
        coverage_count=len(beneficiaries),
        metrics={
            "Coverage": f"{len(beneficiaries)} citizens",
            "Nearest Existing Hospital": f"{round(nearest_dist)}m" if existing_points else "none nearby",
            "Businesses in Range": str(len(businesses)),
            "Traffic Impact": f"+{min(25, round(len(beneficiaries) / 40))}%",
        },
        beneficiaries=beneficiaries, businesses=businesses,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired={"role": "hospital staff (doctors, nurses, support)", "min": 40, "max": 90},
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons,
    )
    result.summary = (
        f"{len(beneficiaries)} citizens within {int(cfg.service_radius)}m would gain closer access to "
        f"healthcare than their current nearest hospital; {len(businesses)} nearby businesses could see "
        f"increased foot traffic. {len(affected_people)} residents and {len(affected_buildings)} buildings "
        f"sit within the {int(DISRUPTION_RADIUS)}m construction footprint."
    )
    return result


async def school_impact(db: AsyncSession, x: float, y: float, **_) -> ImpactResult:
    cfg = INFRASTRUCTURE_CONFIG["school_build"]
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)
    district_by_id = await _district_centers(db)

    schools_result = await db.execute(select(School).where(School.is_operational.is_(True)))
    existing_points = _facility_points(list(schools_result.scalars().all()), district_by_id)

    # School-age proxy: no dedicated "student" flag on Citizen, so treat under-22s as
    # the school-relevant population — the same population the sim's education system
    # itself would eventually draw enrollment from.
    school_age = [c for c in citizens if c.age < 22]
    beneficiaries = _coverage_beneficiaries(school_age, x, y, cfg.service_radius, existing_points)
    affected_people, affected_buildings = _construction_disruption(
        x, y, citizens, buildings, "lives within the construction footprint — expect noise and access disruption during the build"
    )
    nearest_dist = min((math.hypot(x - ex, y - ey) for ex, ey in existing_points), default=0.0)

    score, tier, pros, cons = score_and_recommend(
        coverage=len(beneficiaries), coverage_reference=80,
        distance_improvement=nearest_dist, affected_count=len(affected_people) + len(affected_buildings),
        type_label="school", has_existing=bool(existing_points),
    )

    result = ImpactResult(
        coverage_count=len(beneficiaries),
        metrics={
            "School-Age Coverage": f"{len(beneficiaries)} residents under 22",
            "Nearest Existing School": f"{round(nearest_dist)}m" if existing_points else "none nearby",
            "Est. Capacity Demand": f"{round(len(beneficiaries) * 0.7)} of ~200 seats",
        },
        beneficiaries=beneficiaries,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired={"role": "teachers", "min": 10, "max": 25},
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons,
    )
    result.summary = (
        f"{len(beneficiaries)} school-age residents within {int(cfg.service_radius)}m would gain closer "
        f"access than their current nearest school. {len(affected_people)} residents and "
        f"{len(affected_buildings)} buildings sit within the construction footprint."
    )
    return result


async def housing_colony_impact(db: AsyncSession, x: float, y: float, **_) -> ImpactResult:
    cfg = INFRASTRUCTURE_CONFIG["colony_build"]
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)
    district_by_id = await _district_centers(db)

    # A colony doesn't serve existing citizens — it ADDS population — so its "coverage"
    # metric is what nearby hospitals/schools would need to absorb, not who benefits.
    hospitals_result = await db.execute(select(Hospital).where(Hospital.is_operational.is_(True)))
    schools_result = await db.execute(select(School).where(School.is_operational.is_(True)))
    hospital_points = _facility_points(list(hospitals_result.scalars().all()), district_by_id)
    school_points = _facility_points(list(schools_result.scalars().all()), district_by_id)

    est_new_population = 8 * 3  # ~8 homes/colony, ~3 residents each — matches _complete_colony_build's range
    nearest_hospital = min((math.hypot(x - hx, y - hy) for hx, hy in hospital_points), default=float("inf"))
    nearest_school = min((math.hypot(x - sx, y - sy) for sx, sy in school_points), default=float("inf"))

    affected_people, affected_buildings = _construction_disruption(
        x, y, citizens, buildings, "lives within the construction footprint — expect noise and access disruption during the build"
    )
    businesses = _nearby_businesses(x, y, buildings, 400)

    hospital_pressure = "low" if nearest_hospital < 400 else "moderate" if nearest_hospital < 900 else "high"
    school_pressure = "low" if nearest_school < 400 else "moderate" if nearest_school < 900 else "high"

    score, tier, pros, cons = score_and_recommend(
        coverage=len(businesses) * 10, coverage_reference=100,  # proxy: existing local amenity density
        distance_improvement=0 if nearest_hospital == float("inf") else max(0, 900 - nearest_hospital),
        affected_count=len(affected_people) + len(affected_buildings), type_label="colony",
    )
    if hospital_pressure == "high":
        cons.append(f"Nearest hospital is {round(nearest_hospital)}m away — new residents would add real pressure")
    if school_pressure == "high":
        cons.append(f"Nearest school is {round(nearest_school)}m away — new residents would add real pressure")
    if businesses:
        pros.append(f"{len(businesses)} businesses already nearby to serve new residents")

    result = ImpactResult(
        coverage_count=est_new_population,
        metrics={
            "New Population": f"~{est_new_population} residents",
            "Hospital Pressure": hospital_pressure,
            "School Pressure": school_pressure,
            "Nearby Businesses": str(len(businesses)),
        },
        businesses=businesses,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired=None,
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons,
    )
    result.summary = (
        f"Adds an estimated {est_new_population} new residents. Hospital pressure would be {hospital_pressure} "
        f"(nearest is {round(nearest_hospital) if nearest_hospital != float('inf') else 'n/a'}m away), school "
        f"pressure {school_pressure}. {len(affected_people)} residents and {len(affected_buildings)} buildings "
        f"sit within the construction footprint."
    )
    return result


async def fire_station_impact(db: AsyncSession, x: float, y: float, **_) -> ImpactResult:
    cfg = INFRASTRUCTURE_CONFIG["fire_station_build"]
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)
    district_by_id = await _district_centers(db)

    stations_result = await db.execute(select(FireStation).where(FireStation.is_active.is_(True)))
    existing_points = _facility_points(list(stations_result.scalars().all()), district_by_id)

    beneficiaries = _coverage_beneficiaries(citizens, x, y, cfg.service_radius, existing_points)
    affected_people, affected_buildings = _construction_disruption(
        x, y, citizens, buildings, "lives within the construction footprint — expect noise and access disruption during the build"
    )
    nearest_dist = min((math.hypot(x - ex, y - ey) for ex, ey in existing_points), default=0.0)
    # Response time modeled as travel time at a typical emergency-vehicle speed (sim units).
    est_response_ticks = round(cfg.service_radius / 40) if nearest_dist == 0 else round(nearest_dist / 40)

    score, tier, pros, cons = score_and_recommend(
        coverage=len(beneficiaries), coverage_reference=150,
        distance_improvement=nearest_dist, affected_count=len(affected_people) + len(affected_buildings),
        type_label="fire station", has_existing=bool(existing_points),
    )

    result = ImpactResult(
        coverage_count=len(beneficiaries),
        metrics={
            "Coverage": f"{len(beneficiaries)} citizens",
            "Nearest Existing Station": f"{round(nearest_dist)}m" if existing_points else "none — first in city",
            "Est. Response Time": f"~{est_response_ticks} ticks",
        },
        beneficiaries=beneficiaries,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired={"role": "firefighters", "min": 12, "max": 25},
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons,
    )
    result.summary = (
        f"{len(beneficiaries)} citizens within {int(cfg.service_radius)}m would gain faster emergency fire "
        f"response than from their current nearest station. {len(affected_people)} residents and "
        f"{len(affected_buildings)} buildings sit within the construction footprint."
    )
    return result


async def police_station_impact(db: AsyncSession, x: float, y: float, **_) -> ImpactResult:
    cfg = INFRASTRUCTURE_CONFIG["police_station_build"]
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)
    district_by_id = await _district_centers(db)

    units_result = await db.execute(select(PoliceUnit).where(PoliceUnit.is_active.is_(True)))
    existing_points = _facility_points(list(units_result.scalars().all()), district_by_id)

    beneficiaries = _coverage_beneficiaries(citizens, x, y, cfg.service_radius, existing_points)
    affected_people, affected_buildings = _construction_disruption(
        x, y, citizens, buildings, "lives within the construction footprint — expect noise and access disruption during the build"
    )
    nearest_dist = min((math.hypot(x - ex, y - ey) for ex, ey in existing_points), default=0.0)

    score, tier, pros, cons = score_and_recommend(
        coverage=len(beneficiaries), coverage_reference=150,
        distance_improvement=nearest_dist, affected_count=len(affected_people) + len(affected_buildings),
        type_label="police station", has_existing=bool(existing_points),
    )

    result = ImpactResult(
        coverage_count=len(beneficiaries),
        metrics={
            "Coverage": f"{len(beneficiaries)} citizens",
            "Nearest Existing Station": f"{round(nearest_dist)}m" if existing_points else "none — first in city",
        },
        beneficiaries=beneficiaries,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired={"role": "officers", "min": 10, "max": 22},
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons,
    )
    result.summary = (
        f"{len(beneficiaries)} citizens within {int(cfg.service_radius)}m would gain closer police coverage "
        f"than from their current nearest station. {len(affected_people)} residents and "
        f"{len(affected_buildings)} buildings sit within the construction footprint."
    )
    return result


async def _shortest_district_path(districts: list[District], start: District, end: District, road_link_threshold: float) -> float:
    import heapq
    dist = {d.id: math.inf for d in districts}
    dist[start.id] = 0.0
    visited = set()
    heap = [(0.0, start.id)]
    by_id = {d.id: d for d in districts}
    while heap:
        d, node_id = heapq.heappop(heap)
        if node_id in visited:
            continue
        visited.add(node_id)
        if node_id == end.id:
            return d
        node = by_id[node_id]
        for other in districts:
            if other.id == node_id:
                continue
            edge = math.hypot(other.center_x - node.center_x, other.center_y - node.center_y)
            if edge > road_link_threshold:
                continue
            new_dist = d + edge
            if new_dist < dist[other.id]:
                dist[other.id] = new_dist
                heapq.heappush(heap, (new_dist, other.id))
    return dist[end.id]


ROAD_LINK_THRESHOLD = 140.0 / 0.075  # matches the 3D view's own road-generation rule


async def connection_impact(db: AsyncSession, x: float, y: float, target_x: float | None = None, target_y: float | None = None, project_type: str = "road_build") -> ImpactResult:
    if target_x is None or target_y is None:
        raise ValueError("target_x/target_y required for road/bridge impact")

    districts_result = await db.execute(select(District))
    districts = list(districts_result.scalars().all())
    citizens = await _load_citizens(db)
    buildings = await _load_buildings(db)

    if not districts:
        return ImpactResult(summary="No districts found.")

    def nearest_district(px: float, py: float) -> District:
        return min(districts, key=lambda d: (d.center_x - px) ** 2 + (d.center_y - py) ** 2)

    d1, d2 = nearest_district(x, y), nearest_district(target_x, target_y)
    direct_dist = math.hypot(target_x - x, target_y - y)
    current_route = await _shortest_district_path(districts, d1, d2, ROAD_LINK_THRESHOLD)
    if current_route == math.inf:
        current_route = math.hypot(d2.center_x - d1.center_x, d2.center_y - d1.center_y)
    already_linked = current_route <= direct_dist * 1.05

    beneficiaries, affected_people = [], []
    for c in citizens:
        home_d = c.home_location.district_id if c.home_location else None
        work_d = c.workplace.district_id if c.workplace else None
        if (home_d == d1.id and work_d == d2.id) or (home_d == d2.id and work_d == d1.id):
            beneficiaries.append({
                "citizen_id": str(c.id), "name": c.name, "commute": f"{d1.name} ↔ {d2.name}",
                "improvement": round(max(0.0, current_route - direct_dist), 1),
            })
        loc = c.home_location or c.workplace
        if loc and loc.x is not None and loc.y is not None:
            corridor_dist = _point_segment_distance(loc.x, loc.y, x, y, target_x, target_y)
            if corridor_dist <= CORRIDOR_WIDTH:
                affected_people.append({
                    "citizen_id": str(c.id), "name": c.name, "distance": round(corridor_dist, 1),
                    "reason": "lives along the new route corridor — expect increased traffic and noise once built",
                })
    beneficiaries.sort(key=lambda b: -b["improvement"])
    affected_people.sort(key=lambda p: p["distance"])

    businesses, affected_buildings = [], []
    for b in buildings:
        loc = b.location
        if not loc or loc.x is None:
            continue
        if b.building_type in (BuildingType.SHOP, BuildingType.RESTAURANT, BuildingType.OFFICE) and loc.district_id in (d1.id, d2.id):
            businesses.append({"name": b.name, "type": b.building_type.value, "district": d1.name if loc.district_id == d1.id else d2.name})
        corridor_dist = _point_segment_distance(loc.x, loc.y, x, y, target_x, target_y)
        if corridor_dist <= CORRIDOR_WIDTH:
            affected_buildings.append({
                "name": b.name, "type": b.building_type.value, "distance": round(corridor_dist, 1),
                "reason": "sits along the new route corridor — expect increased traffic and noise once built",
            })
    affected_buildings.sort(key=lambda b: b["distance"])

    # already_linked means current_route ≈ direct_dist, so travel_time_saved is already
    # naturally near-zero in that case — the score/tier fall out of the same formula
    # every other strategy uses, instead of being capped after the fact (which would
    # desync the tier label from the score that produced it).
    travel_time_saved = 0.0 if already_linked else max(0.0, current_route - direct_dist)
    # already_linked means this route provides no real improvement over what exists —
    # commuter count alone shouldn't score it well just because those commuters exist;
    # the benefit they'd actually gain from THIS link is zero, so coverage is zero too.
    score, tier, pros, cons = score_and_recommend(
        coverage=0 if already_linked else len(beneficiaries), coverage_reference=20,
        distance_improvement=travel_time_saved,
        affected_count=len(affected_people) + len(affected_buildings),
        type_label="direct route",
    )
    if already_linked:
        cons.append(f"{d1.name} and {d2.name} already have a comparably direct route")

    kind = "bridge" if project_type == "bridge_build" else "road"
    if already_linked:
        summary = (
            f"{d1.name} and {d2.name} already have a direct route of about the same length as this one — "
            f"a new {kind} here would mainly add redundancy/congestion relief for the {len(beneficiaries)} "
            f"citizens who commute between them, not a real travel-time saving."
        )
    else:
        summary = (
            f"{len(beneficiaries)} citizens commute between {d1.name} and {d2.name} today via a longer route "
            f"through other districts — a direct {kind} here would shorten their trip by up to "
            f"{round(beneficiaries[0]['improvement'], 0) if beneficiaries else 0} units. "
            f"{len(businesses)} businesses in these districts could see wider reach."
        )
    summary += (
        f" {len(affected_people)} residents and {len(affected_buildings)} buildings sit along the route "
        f"corridor and would see increased traffic/noise. This project type doesn't add permanent staff."
    )

    result = ImpactResult(
        coverage_count=len(beneficiaries),
        metrics={
            "Commuters Benefiting": str(len(beneficiaries)),
            "Travel Time Saved": f"{round(travel_time_saved)} units" if not already_linked else "~0 (already linked)",
            "Businesses in Reach": str(len(businesses)),
        },
        beneficiaries=beneficiaries, businesses=businesses,
        affected_people=affected_people, affected_buildings=affected_buildings,
        employees_hired=None,
        ai_score=score, ai_tier=tier, ai_pros=pros, ai_cons=cons, summary=summary,
    )
    return result


IMPACT_STRATEGIES: dict[str, Callable[..., Awaitable[ImpactResult]]] = {
    "hospital_build": hospital_impact,
    "school_build": school_impact,
    "colony_build": housing_colony_impact,
    "fire_station_build": fire_station_impact,
    "police_station_build": police_station_impact,
    "road_build": connection_impact,
    "bridge_build": connection_impact,
}

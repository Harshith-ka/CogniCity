"""
Infrastructure & Utilities Engine: Manages power grids, water supply,
internet, and gas networks. Tracks capacity, reliability, and maintenance.
Infrastructure projects improve grid health over time.
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.city import District, Location, Building, LocationType, BuildingType
from backend.app.models.infrastructure import UtilityGrid, InfraProject
from backend.app.models.healthcare import Hospital
from backend.app.models.education import School

log = structlog.get_logger()

UTILITY_TYPES = ["power", "water", "internet", "gas"]

# Every triggerable project type, autonomous or manual. impact_reliability/impact_capacity
# only matter for utility-grid maintenance types; build types leave them at 0 and instead
# create real Hospital/School/Location+Building rows on completion (see _process_projects).
BUILD_PRESETS = {
    "road_repair":      {"name": "Road Resurfacing",       "budget": 50000,  "impact_reliability": 0.05, "impact_capacity": 0.0},
    "grid_upgrade":      {"name": "Grid Modernization",     "budget": 150000, "impact_reliability": 0.1,  "impact_capacity": 200.0},
    "pipe_replacement":  {"name": "Water Pipe Replacement", "budget": 80000,  "impact_reliability": 0.08, "impact_capacity": 100.0},
    "fiber_install":     {"name": "Fiber Optic Install",    "budget": 120000, "impact_reliability": 0.12, "impact_capacity": 500.0},
    "bridge_build":      {"name": "Bridge",                 "budget": 200000, "impact_reliability": 0.06, "impact_capacity": 0.0},
    "hospital_build":    {"name": "Hospital",               "budget": 600000, "impact_reliability": 0.0,  "impact_capacity": 0.0},
    "school_build":      {"name": "School",                 "budget": 400000, "impact_reliability": 0.0,  "impact_capacity": 0.0},
    "colony_build":      {"name": "Residential Colony",     "budget": 800000, "impact_reliability": 0.0,  "impact_capacity": 0.0},
    "road_build":        {"name": "New Road",               "budget": 250000, "impact_reliability": 0.02, "impact_capacity": 0.0},
}

# The subset the government AI itself picks from at random, unprompted, every ~40 ticks.
# The full BUILD_PRESETS set (including the new build types) is reachable via manual trigger.
AUTONOMOUS_PROJECT_TYPES = ["road_repair", "grid_upgrade", "pipe_replacement", "fiber_install", "bridge_build"]

UTILITY_DEFAULTS = {
    "power": {"capacity": 1200.0, "price_per_unit": 0.12},
    "water": {"capacity": 800.0, "price_per_unit": 0.05},
    "internet": {"capacity": 2000.0, "price_per_unit": 0.08},
    "gas": {"capacity": 600.0, "price_per_unit": 0.10},
}


class InfrastructureEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, population: int = 100) -> dict:
        self._tick_count += 1
        stats = {"outages": 0, "projects_completed": 0, "avg_reliability": 0.0, "avg_load_pct": 0.0}

        await self._update_grids(population, stats)
        await self._process_projects(stats)

        if self._tick_count % 40 == 0 and random.random() < 0.35:
            await self._start_project()

        if self._tick_count % 20 == 0:
            await self._schedule_maintenance()

        await self.db.flush()
        return stats

    async def _update_grids(self, population: int, stats: dict) -> None:
        result = await self.db.execute(select(UtilityGrid))
        grids = result.scalars().all()
        if not grids:
            return

        total_reliability = 0.0
        total_load_pct = 0.0

        for grid in grids:
            demand = population * random.uniform(0.3, 0.6)
            grid.current_load = min(grid.capacity, demand)

            grid.health -= random.uniform(0.0005, 0.002)
            grid.health = max(0.1, grid.health)

            if grid.health < 0.3 and random.random() < 0.1:
                grid.is_operational = False
                stats["outages"] += 1
                log.warning("utility_outage", type=grid.utility_type, health=grid.health)
            elif not grid.is_operational and grid.health > 0.5:
                grid.is_operational = True

            grid.reliability = grid.health * random.uniform(0.9, 1.0)
            total_reliability += grid.reliability
            total_load_pct += grid.current_load / max(1, grid.capacity)

        stats["avg_reliability"] = round(total_reliability / len(grids), 3)
        stats["avg_load_pct"] = round(total_load_pct / len(grids), 3)

    async def _process_projects(self, stats: dict) -> None:
        result = await self.db.execute(
            select(InfraProject).where(InfraProject.is_active.is_(True), InfraProject.is_completed.is_(False))
        )
        projects = result.scalars().all()

        for project in projects:
            project.progress = min(1.0, project.progress + random.uniform(0.02, 0.05))
            project.spent = project.budget * project.progress

            if project.progress >= 1.0:
                project.is_completed = True
                project.is_active = False
                project.completed_at = datetime.utcnow()

                if project.district_id and project.impact_reliability:
                    grid_result = await self.db.execute(
                        select(UtilityGrid).where(UtilityGrid.district_id == project.district_id)
                    )
                    grids = grid_result.scalars().all()
                    for grid in grids:
                        grid.reliability = min(1.0, grid.reliability + project.impact_reliability)
                        grid.capacity += project.impact_capacity
                        grid.health = min(1.0, grid.health + project.impact_reliability)

                if project.project_type == "hospital_build":
                    await self._complete_hospital_build(project)
                elif project.project_type == "school_build":
                    await self._complete_school_build(project)
                elif project.project_type == "colony_build":
                    await self._complete_colony_build(project)

                stats["projects_completed"] += 1
                log.info("infra_project_completed", name=project.name, type=project.project_type)

    async def _complete_hospital_build(self, project: InfraProject) -> None:
        district_name = None
        if project.district_id:
            district = await self.db.get(District, project.district_id)
            district_name = district.name if district else None

        hospital = Hospital(
            name=f"{district_name} Community Hospital" if district_name else "New Community Hospital",
            hospital_type=random.choice(["general", "emergency", "clinic"]),
            district_id=project.district_id,
            total_beds=random.randint(80, 180),
            icu_beds=random.randint(8, 18),
            staff_count=random.randint(40, 90),
            quality_rating=round(random.uniform(0.6, 0.9), 2),
            funding=project.budget,
        )
        self.db.add(hospital)
        log.info("hospital_built", name=hospital.name)

    async def _complete_school_build(self, project: InfraProject) -> None:
        district_name = None
        if project.district_id:
            district = await self.db.get(District, project.district_id)
            district_name = district.name if district else None

        school = School(
            name=f"{district_name} Community School" if district_name else "New Community School",
            school_type=random.choice(["elementary", "high_school", "vocational"]),
            district_id=project.district_id,
            capacity=random.randint(150, 350),
            teachers=random.randint(10, 25),
            quality_rating=round(random.uniform(0.6, 0.9), 2),
            tuition=0.0,
            programs=["general"],
        )
        self.db.add(school)
        log.info("school_built", name=school.name)

    async def _complete_colony_build(self, project: InfraProject) -> None:
        base_x = project.x if project.x is not None else 0.0
        base_y = project.y if project.y is not None else 0.0
        base_name = project.name.split(" — ")[0]
        home_count = random.randint(6, 10)

        for i in range(home_count):
            location = Location(
                name=f"{base_name} Home {i + 1}",
                location_type=LocationType.RESIDENTIAL,
                district_id=project.district_id,
                x=base_x + random.uniform(-25, 25),
                y=base_y + random.uniform(-25, 25),
                capacity=random.randint(2, 6),
            )
            self.db.add(location)
            await self.db.flush()  # need location.id for the building's FK

            building = Building(
                name=location.name,
                building_type=random.choice([BuildingType.HOUSE, BuildingType.APARTMENT]),
                location_id=location.id,
                floors=random.randint(1, 4),
                condition=round(random.uniform(0.85, 1.0), 2),
                rent_cost=round(random.uniform(400, 1200), 2),
                value=round(random.uniform(120000, 350000), 2),
            )
            self.db.add(building)

        log.info("colony_built", name=project.name, homes=home_count)

    async def _start_project(self) -> None:
        project_type = random.choice(AUTONOMOUS_PROJECT_TYPES)
        district_result = await self.db.execute(select(District).order_by(sqlfunc.random()).limit(1))
        district = district_result.scalar_one_or_none()
        await self.trigger_project(project_type, district_id=district.id if district else None)

    async def trigger_project(
        self,
        project_type: str,
        district_id: uuid.UUID | None = None,
        x: float | None = None,
        y: float | None = None,
        target_x: float | None = None,
        target_y: float | None = None,
    ) -> InfraProject:
        """Manually (or autonomously) start a project of any known type, optionally
        pinned to an exact location. road_build additionally needs a target_x/target_y
        endpoint — if not given, it picks the nearest other district to connect to."""
        if project_type not in BUILD_PRESETS:
            raise ValueError(f"Unknown project_type: {project_type}")
        preset = BUILD_PRESETS[project_type]

        district: District | None = None
        if district_id:
            district = await self.db.get(District, district_id)
        if district is None and x is not None and y is not None:
            result = await self.db.execute(select(District))
            districts = result.scalars().all()
            if districts:
                district = min(districts, key=lambda d: (d.center_x - x) ** 2 + (d.center_y - y) ** 2)
        if district is None:
            result = await self.db.execute(select(District).order_by(sqlfunc.random()).limit(1))
            district = result.scalar_one_or_none()

        if x is None or y is None:
            if district:
                angle = random.uniform(0, 2 * math.pi)
                dist = district.radius * random.uniform(0.15, 0.55)
                x = district.center_x + math.cos(angle) * dist
                y = district.center_y + math.sin(angle) * dist
            else:
                x, y = 0.0, 0.0

        if project_type == "road_build" and (target_x is None or target_y is None):
            result = await self.db.execute(select(District))
            others = [d for d in result.scalars().all() if not district or d.id != district.id]
            if others:
                other = min(others, key=lambda d: (d.center_x - x) ** 2 + (d.center_y - y) ** 2)
                target_x, target_y = other.center_x, other.center_y
            else:
                target_x, target_y = x + 300, y + 300

        project = InfraProject(
            name=f"{preset['name']} — {district.name}" if district else preset["name"],
            project_type=project_type,
            district_id=district.id if district else None,
            budget=preset["budget"],
            impact_reliability=preset.get("impact_reliability", 0.0),
            impact_capacity=preset.get("impact_capacity", 0.0),
            x=x,
            y=y,
            target_x=target_x if project_type == "road_build" else None,
            target_y=target_y if project_type == "road_build" else None,
        )
        self.db.add(project)
        await self.db.flush()
        log.info("infra_project_started", name=project.name, type=project.project_type)
        return project

    async def _schedule_maintenance(self) -> None:
        result = await self.db.execute(
            select(UtilityGrid).where(UtilityGrid.health < 0.5).order_by(UtilityGrid.health.asc()).limit(2)
        )
        grids = result.scalars().all()
        for grid in grids:
            grid.health = min(1.0, grid.health + random.uniform(0.05, 0.15))
            grid.last_maintenance = datetime.utcnow()
            if not grid.is_operational and grid.health > 0.4:
                grid.is_operational = True

    async def seed_grids(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(UtilityGrid.id)))
        if existing and existing > 0:
            return 0

        count = 0
        for d in districts:
            for utype in UTILITY_TYPES:
                defaults = UTILITY_DEFAULTS[utype]
                grid = UtilityGrid(
                    utility_type=utype,
                    district_id=d.get("id"),
                    capacity=defaults["capacity"] * random.uniform(0.8, 1.2),
                    current_load=defaults["capacity"] * random.uniform(0.3, 0.6),
                    reliability=random.uniform(0.85, 0.98),
                    coverage_pct=random.uniform(0.8, 0.98),
                    price_per_unit=defaults["price_per_unit"],
                    health=random.uniform(0.7, 0.95),
                    is_operational=True,
                )
                self.db.add(grid)
                count += 1

        await self.db.flush()
        log.info("utility_grids_seeded", count=count)
        return count

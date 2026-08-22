"""
Disaster Simulation Engine: Models natural disasters with physics-inspired
spread mechanics, building damage, evacuations, casualties, and recovery.
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.city import Building, Location, District
from backend.app.models.disaster import Disaster, DisasterType, DisasterPhase, EvacuationZone

log = structlog.get_logger()

DISASTER_PROFILES = {
    DisasterType.EARTHQUAKE: {
        "base_radius": 1500,
        "duration": 80,
        "intensity_curve": "spike",
        "spread_rate": 0.0,
        "aftershock_chance": 0.3,
        "building_damage_factor": 0.4,
        "casualty_factor": 0.02,
        "economic_factor": 50000,
    },
    DisasterType.FLOOD: {
        "base_radius": 800,
        "duration": 250,
        "intensity_curve": "slow_rise",
        "spread_rate": 15.0,
        "aftershock_chance": 0.0,
        "building_damage_factor": 0.2,
        "casualty_factor": 0.005,
        "economic_factor": 30000,
    },
    DisasterType.CYCLONE: {
        "base_radius": 2000,
        "duration": 150,
        "intensity_curve": "wave",
        "spread_rate": 25.0,
        "aftershock_chance": 0.0,
        "building_damage_factor": 0.35,
        "casualty_factor": 0.01,
        "economic_factor": 70000,
    },
    DisasterType.FIRE: {
        "base_radius": 300,
        "duration": 100,
        "intensity_curve": "exponential",
        "spread_rate": 20.0,
        "aftershock_chance": 0.1,
        "building_damage_factor": 0.6,
        "casualty_factor": 0.015,
        "economic_factor": 40000,
    },
    DisasterType.TORNADO: {
        "base_radius": 500,
        "duration": 40,
        "intensity_curve": "spike",
        "spread_rate": 30.0,
        "aftershock_chance": 0.0,
        "building_damage_factor": 0.5,
        "casualty_factor": 0.025,
        "economic_factor": 35000,
    },
    DisasterType.TSUNAMI: {
        "base_radius": 1200,
        "duration": 120,
        "intensity_curve": "slow_rise",
        "spread_rate": 40.0,
        "aftershock_chance": 0.0,
        "building_damage_factor": 0.45,
        "casualty_factor": 0.03,
        "economic_factor": 80000,
    },
    DisasterType.LANDSLIDE: {
        "base_radius": 400,
        "duration": 60,
        "intensity_curve": "spike",
        "spread_rate": 5.0,
        "aftershock_chance": 0.15,
        "building_damage_factor": 0.5,
        "casualty_factor": 0.02,
        "economic_factor": 25000,
    },
}


class DisasterEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_disaster(
        self,
        disaster_type: DisasterType,
        sim_time: datetime,
        epicenter_x: float | None = None,
        epicenter_y: float | None = None,
        intensity: float = 0.7,
    ) -> Disaster:
        profile = DISASTER_PROFILES[disaster_type]

        if epicenter_x is None or epicenter_y is None:
            districts_result = await self.db.execute(select(District))
            districts = list(districts_result.scalars().all())
            if districts:
                target = random.choice(districts)
                epicenter_x = target.center_x + random.uniform(-300, 300)
                epicenter_y = target.center_y + random.uniform(-300, 300)
            else:
                epicenter_x, epicenter_y = 0.0, 0.0

        disaster_id = uuid.uuid4()
        disaster = Disaster(
            id=disaster_id,
            name=f"{disaster_type.value.title()} at ({epicenter_x:.0f}, {epicenter_y:.0f})",
            disaster_type=disaster_type,
            phase=DisasterPhase.ONSET,
            epicenter_x=epicenter_x,
            epicenter_y=epicenter_y,
            radius=profile["base_radius"],
            intensity=intensity,
            max_intensity=intensity,
            spread_rate=profile["spread_rate"],
            duration_ticks=profile["duration"],
            parameters=profile,
            started_at=sim_time,
        )
        self.db.add(disaster)

        evac_zone = EvacuationZone(
            disaster_id=disaster_id,
            name=f"Evacuation Zone - {disaster.name}",
            center_x=epicenter_x,
            center_y=epicenter_y,
            radius=profile["base_radius"] * 1.5,
            capacity=500,
        )
        self.db.add(evac_zone)

        await self.db.flush()
        log.info("disaster_triggered", type=disaster_type.value, intensity=intensity)
        return disaster

    MAX_CONCURRENT_DISASTERS = 8

    async def process_tick(self, sim_time: datetime) -> dict:
        result = await self.db.execute(
            select(Disaster).where(Disaster.is_active == True)  # noqa: E712
        )
        disasters = list(result.scalars().all())

        stats = {
            "active_disasters": len(disasters),
            "total_casualties": 0,
            "total_injuries": 0,
            "buildings_damaged": 0,
            "evacuated": 0,
        }

        # Batch-load citizens, their locations, and nearby buildings once for the whole
        # tick — reused across every active disaster — instead of one query per citizen
        # (and per building) per disaster. The latter turns into hundreds of thousands
        # of round-trips once both population and active-disaster count grow.
        citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        citizens = list(citizens_result.scalars().all())
        location_by_id = await self._load_locations_for(citizens)

        building_result = await self.db.execute(select(Building).limit(200))
        buildings = list(building_result.scalars().all())
        building_location_by_id = await self._load_locations_for(buildings, id_attr="location_id")

        active_count = len(disasters)
        for disaster in disasters:
            disaster.elapsed_ticks += 1
            tick_stats = await self._process_disaster_tick(
                disaster, sim_time, citizens, location_by_id, buildings, building_location_by_id
            )

            stats["total_casualties"] += tick_stats.get("casualties", 0)
            stats["total_injuries"] += tick_stats.get("injuries", 0)
            stats["buildings_damaged"] += tick_stats.get("buildings_damaged", 0)
            stats["evacuated"] += tick_stats.get("evacuated", 0)

            self._update_phase(disaster)
            self._update_intensity(disaster)

            if disaster.spread_rate > 0:
                disaster.radius += disaster.spread_rate * disaster.intensity

            if disaster.elapsed_ticks >= disaster.duration_ticks:
                disaster.is_active = False
                disaster.phase = DisasterPhase.RESOLVED
                disaster.ended_at = sim_time
                log.info("disaster_resolved", name=disaster.name, casualties=disaster.casualties)

            profile = disaster.parameters or {}
            if active_count < self.MAX_CONCURRENT_DISASTERS and random.random() < profile.get("aftershock_chance", 0) * 0.1:
                aftershock_intensity = disaster.max_intensity * random.uniform(0.2, 0.5)
                offset_x = disaster.epicenter_x + random.uniform(-200, 200)
                offset_y = disaster.epicenter_y + random.uniform(-200, 200)
                await self.trigger_disaster(
                    disaster.disaster_type, sim_time,
                    epicenter_x=offset_x, epicenter_y=offset_y,
                    intensity=aftershock_intensity,
                )
                active_count += 1
                log.info("aftershock", parent=disaster.name, intensity=aftershock_intensity)

        await self.db.flush()
        return stats

    async def _load_locations_for(self, entities: list, id_attr: str = "current_location_id") -> dict:
        """Batch-fetch the distinct Location rows referenced by a list of citizens or
        buildings in a single query, instead of one query per entity."""
        ids: set = set()
        for e in entities:
            if id_attr == "current_location_id":
                loc_id = getattr(e, "current_location_id", None) or getattr(e, "home_location_id", None)
            else:
                loc_id = getattr(e, id_attr, None)
            if loc_id:
                ids.add(loc_id)
        if not ids:
            return {}
        result = await self.db.execute(select(Location).where(Location.id.in_(ids)))
        return {loc.id: loc for loc in result.scalars().all()}

    async def _process_disaster_tick(
        self,
        disaster: Disaster,
        sim_time: datetime,
        citizens: list,
        location_by_id: dict,
        buildings: list,
        building_location_by_id: dict,
    ) -> dict:
        profile = disaster.parameters or {}
        tick_stats = {"casualties": 0, "injuries": 0, "buildings_damaged": 0, "evacuated": 0}

        for citizen in citizens:
            if not citizen.home_location_id:
                continue

            loc = location_by_id.get(citizen.current_location_id) or location_by_id.get(citizen.home_location_id)
            if not loc:
                continue

            dist = math.sqrt(
                (loc.x - disaster.epicenter_x) ** 2 + (loc.y - disaster.epicenter_y) ** 2
            )
            if dist > disaster.radius:
                continue

            proximity_factor = max(0.0, 1.0 - dist / disaster.radius)
            impact = disaster.intensity * proximity_factor

            citizen.stress = min(1.0, citizen.stress + impact * 0.1)
            citizen.happiness = max(0.0, citizen.happiness - impact * 0.05)
            citizen.health = max(0.0, citizen.health - impact * profile.get("casualty_factor", 0.01))

            if random.random() < impact * profile.get("casualty_factor", 0.01) * 0.5:
                citizen.health = max(0.0, citizen.health - 0.3)
                disaster.injuries += 1
                tick_stats["injuries"] += 1

            if citizen.health <= 0:
                citizen.is_alive = False
                disaster.casualties += 1
                tick_stats["casualties"] += 1

            if impact > 0.5 and disaster.phase in (DisasterPhase.ONSET, DisasterPhase.PEAK):
                disaster.evacuated += 1
                tick_stats["evacuated"] += 1

        for building in buildings:
            loc = building_location_by_id.get(building.location_id)
            if not loc:
                continue

            dist = math.sqrt(
                (loc.x - disaster.epicenter_x) ** 2 + (loc.y - disaster.epicenter_y) ** 2
            )
            if dist > disaster.radius:
                continue

            proximity = max(0.0, 1.0 - dist / disaster.radius)
            damage = disaster.intensity * proximity * profile.get("building_damage_factor", 0.3) * 0.05
            building.condition = max(0.0, building.condition - damage)

            if building.condition < 0.3 and random.random() < 0.1:
                disaster.buildings_damaged += 1
                tick_stats["buildings_damaged"] += 1
                if building.condition <= 0:
                    disaster.buildings_destroyed += 1

        disaster.economic_damage += disaster.intensity * profile.get("economic_factor", 10000) * 0.01

        return tick_stats

    def _update_phase(self, disaster: Disaster) -> None:
        progress = disaster.elapsed_ticks / max(disaster.duration_ticks, 1)
        if progress < 0.15:
            disaster.phase = DisasterPhase.ONSET
        elif progress < 0.4:
            disaster.phase = DisasterPhase.PEAK
        elif progress < 0.7:
            disaster.phase = DisasterPhase.DECLINING
        elif progress < 1.0:
            disaster.phase = DisasterPhase.RECOVERY

    def _update_intensity(self, disaster: Disaster) -> None:
        profile = disaster.parameters or {}
        curve = profile.get("intensity_curve", "spike")
        progress = disaster.elapsed_ticks / max(disaster.duration_ticks, 1)

        if curve == "spike":
            if progress < 0.1:
                disaster.intensity = disaster.max_intensity * (progress / 0.1)
            else:
                disaster.intensity = disaster.max_intensity * max(0.0, 1.0 - (progress - 0.1) / 0.9)
        elif curve == "slow_rise":
            if progress < 0.3:
                disaster.intensity = disaster.max_intensity * (progress / 0.3)
            elif progress < 0.6:
                disaster.intensity = disaster.max_intensity
            else:
                disaster.intensity = disaster.max_intensity * max(0.0, 1.0 - (progress - 0.6) / 0.4)
        elif curve == "exponential":
            if progress < 0.5:
                disaster.intensity = disaster.max_intensity * (1.0 - math.exp(-5 * progress))
            else:
                disaster.intensity = disaster.max_intensity * math.exp(-3 * (progress - 0.5))
        elif curve == "wave":
            disaster.intensity = disaster.max_intensity * abs(math.sin(progress * math.pi * 2)) * (1.0 - progress * 0.5)

    async def get_active_disasters(self) -> list[dict]:
        result = await self.db.execute(
            select(Disaster).where(Disaster.is_active == True)  # noqa: E712
        )
        disasters = list(result.scalars().all())
        return [
            {
                "id": str(d.id),
                "name": d.name,
                "type": d.disaster_type.value,
                "phase": d.phase.value,
                "intensity": round(d.intensity, 3),
                "epicenter": [d.epicenter_x, d.epicenter_y],
                "radius": round(d.radius, 1),
                "casualties": d.casualties,
                "injuries": d.injuries,
                "buildings_damaged": d.buildings_damaged,
                "evacuated": d.evacuated,
                "economic_damage": round(d.economic_damage, 2),
                "progress": round(d.elapsed_ticks / max(d.duration_ticks, 1), 3),
            }
            for d in disasters
        ]

    async def get_disaster_history(self, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(Disaster).order_by(Disaster.created_at.desc()).limit(limit)
        )
        disasters = list(result.scalars().all())
        return [
            {
                "id": str(d.id),
                "name": d.name,
                "type": d.disaster_type.value,
                "phase": d.phase.value,
                "max_intensity": d.max_intensity,
                "casualties": d.casualties,
                "injuries": d.injuries,
                "buildings_damaged": d.buildings_damaged,
                "economic_damage": round(d.economic_damage, 2),
                "is_active": d.is_active,
            }
            for d in disasters
        ]

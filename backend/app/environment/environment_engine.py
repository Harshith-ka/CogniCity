"""
Environment & Sustainability Engine: Tracks air quality, carbon emissions,
green coverage, and manages green initiatives that improve city sustainability.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.environment import EnvironmentState, GreenInitiative

log = structlog.get_logger()

INITIATIVE_PRESETS = [
    {"name": "Solar Panel Array", "initiative_type": "solar_panel", "cost": 80000, "impact_carbon": -15.0, "impact_air_quality": -3, "impact_renewable_pct": 0.04},
    {"name": "Wind Farm Project", "initiative_type": "wind_farm", "cost": 120000, "impact_carbon": -25.0, "impact_air_quality": -2, "impact_renewable_pct": 0.06},
    {"name": "City Recycling Program", "initiative_type": "recycling_program", "cost": 30000, "impact_carbon": -5.0, "impact_air_quality": -4, "impact_renewable_pct": 0.0},
    {"name": "Urban Tree Planting", "initiative_type": "tree_planting", "cost": 15000, "impact_carbon": -8.0, "impact_air_quality": -6, "impact_renewable_pct": 0.0},
    {"name": "EV Charging Network", "initiative_type": "ev_charging", "cost": 60000, "impact_carbon": -12.0, "impact_air_quality": -5, "impact_renewable_pct": 0.0},
    {"name": "Water Treatment Upgrade", "initiative_type": "water_treatment", "cost": 50000, "impact_carbon": -3.0, "impact_air_quality": -1, "impact_renewable_pct": 0.0},
]


class EnvironmentEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, population: int = 100, weather_condition: str = "clear") -> dict:
        self._tick_count += 1

        state = await self._get_or_create_state()
        self._update_environment(state, population, weather_condition)
        await self._process_initiatives(state)

        if self._tick_count % 60 == 0 and random.random() < 0.3:
            await self._launch_initiative()

        await self.db.flush()
        return {
            "air_quality": state.air_quality_index,
            "carbon_emissions": round(state.carbon_emissions_tons, 1),
            "green_coverage": round(state.green_coverage_pct, 3),
            "renewable_energy": round(state.renewable_energy_pct, 3),
            "recycling_rate": round(state.recycling_rate, 3),
        }

    async def _get_or_create_state(self) -> EnvironmentState:
        result = await self.db.execute(select(EnvironmentState).where(EnvironmentState.is_current.is_(True)).limit(1))
        state = result.scalar_one_or_none()
        if not state:
            state = EnvironmentState(is_current=True)
            self.db.add(state)
            await self.db.flush()
        return state

    def _update_environment(self, state: EnvironmentState, population: int, weather_condition: str) -> None:
        pop_factor = population / 500.0
        state.carbon_emissions_tons += pop_factor * random.uniform(0.1, 0.5)
        state.waste_tons += pop_factor * random.uniform(0.05, 0.2)

        if weather_condition in ("rain", "storm"):
            state.air_quality_index = max(10, state.air_quality_index - random.randint(1, 3))
        elif weather_condition == "heatwave":
            state.air_quality_index = min(300, state.air_quality_index + random.randint(2, 5))
        else:
            state.air_quality_index += random.randint(-1, 2)

        state.air_quality_index = max(10, min(300, state.air_quality_index))

        recycled = state.waste_tons * state.recycling_rate
        state.waste_tons = max(0, state.waste_tons - recycled)

        state.noise_level_db += random.uniform(-0.5, 0.5)
        state.noise_level_db = max(30, min(90, state.noise_level_db))

    async def _process_initiatives(self, state: EnvironmentState) -> None:
        result = await self.db.execute(
            select(GreenInitiative).where(GreenInitiative.is_active.is_(True), GreenInitiative.is_completed.is_(False))
        )
        initiatives = result.scalars().all()

        for init in initiatives:
            init.progress = min(1.0, init.progress + random.uniform(0.01, 0.03))

            if init.progress >= 1.0:
                init.is_completed = True
                init.is_active = False
                state.carbon_emissions_tons = max(0, state.carbon_emissions_tons + init.impact_carbon)
                state.air_quality_index = max(10, state.air_quality_index + init.impact_air_quality)
                state.renewable_energy_pct = min(1.0, state.renewable_energy_pct + init.impact_renewable_pct)

                if init.initiative_type == "tree_planting":
                    state.green_coverage_pct = min(0.6, state.green_coverage_pct + 0.02)
                elif init.initiative_type == "recycling_program":
                    state.recycling_rate = min(0.9, state.recycling_rate + 0.05)

                log.info("green_initiative_completed", name=init.name, type=init.initiative_type)

    async def _launch_initiative(self) -> None:
        preset = random.choice(INITIATIVE_PRESETS)
        init = GreenInitiative(
            name=preset["name"],
            initiative_type=preset["initiative_type"],
            cost=preset["cost"],
            impact_carbon=preset["impact_carbon"],
            impact_air_quality=preset["impact_air_quality"],
            impact_renewable_pct=preset["impact_renewable_pct"],
            is_active=True,
            progress=0.0,
        )
        self.db.add(init)
        log.info("green_initiative_launched", name=init.name)

    async def seed_state(self) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(EnvironmentState.id)))
        if existing and existing > 0:
            return 0

        state = EnvironmentState(
            air_quality_index=random.randint(40, 70),
            water_quality=random.uniform(0.6, 0.9),
            noise_level_db=random.uniform(45, 65),
            green_coverage_pct=random.uniform(0.15, 0.35),
            carbon_emissions_tons=random.uniform(300, 600),
            recycling_rate=random.uniform(0.2, 0.4),
            renewable_energy_pct=random.uniform(0.1, 0.3),
            waste_tons=random.uniform(50, 150),
            is_current=True,
        )
        self.db.add(state)
        await self.db.flush()
        log.info("environment_state_seeded")
        return 1

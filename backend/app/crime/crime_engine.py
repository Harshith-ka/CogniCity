"""
Crime & Public Safety Engine: Simulates crime generation, police response,
investigation, and resolution. Crime rates depend on district safety/wealth,
unemployment, time of day, and weather. Police units respond with varying
effectiveness based on staffing and workload.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.crime import CrimeRecord, PoliceUnit

log = structlog.get_logger()

CRIME_TYPES = {
    "theft":        {"severity": "minor",    "base_prob": 0.015, "damage_range": (50, 500),    "solve_rate": 0.4},
    "vandalism":    {"severity": "minor",    "base_prob": 0.010, "damage_range": (100, 1000),  "solve_rate": 0.3},
    "fraud":        {"severity": "moderate", "base_prob": 0.005, "damage_range": (500, 5000),  "solve_rate": 0.5},
    "burglary":     {"severity": "moderate", "base_prob": 0.006, "damage_range": (500, 3000),  "solve_rate": 0.35},
    "assault":      {"severity": "serious",  "base_prob": 0.004, "damage_range": (200, 2000),  "solve_rate": 0.55},
    "robbery":      {"severity": "serious",  "base_prob": 0.003, "damage_range": (300, 5000),  "solve_rate": 0.45},
    "drug_offense": {"severity": "moderate", "base_prob": 0.007, "damage_range": (0, 1000),    "solve_rate": 0.3},
}

CRIME_TEMPLATES = {
    "theft":        ["{perp} stole items from a shop in {district}",
                     "Pickpocket incident reported near {district} market"],
    "vandalism":    ["Graffiti and property damage in {district}",
                     "Park benches destroyed in {district}"],
    "fraud":        ["Financial fraud uncovered involving {perp}",
                     "Identity theft reported by resident in {district}"],
    "burglary":     ["Home break-in reported in {district}",
                     "Business burglary overnight in {district}"],
    "assault":      ["Altercation escalated to assault in {district}",
                     "{perp} involved in a violent incident"],
    "robbery":      ["Armed robbery at a convenience store in {district}",
                     "Street robbery reported in {district}"],
    "drug_offense": ["Drug possession arrest in {district}",
                     "Suspicious drug activity reported in {district}"],
}


class CrimeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_tick(
        self,
        sim_time: datetime,
        hour: int,
        citizens: list,
        districts: list[dict],
        weather_crime_modifier: float = 1.0,
    ) -> dict:
        crimes_generated = 0
        crimes_solved = 0

        night_factor = 1.5 if hour < 6 or hour > 22 else (1.2 if hour > 20 else 1.0)

        for district in districts:
            safety = district.get("safety", 0.7)
            wealth = district.get("wealth", 0.5)
            district_id = district.get("id")

            district_citizens = [
                c for c in citizens
                if str(getattr(c, "home_location_id", "")) and random.random() < 0.3
            ]

            unsafety_factor = max(0.1, 1.0 - safety)
            poverty_factor = max(0.1, 1.0 - wealth)
            district_modifier = (unsafety_factor * 0.6 + poverty_factor * 0.4)

            for crime_type, config in CRIME_TYPES.items():
                prob = (
                    config["base_prob"]
                    * district_modifier
                    * night_factor
                    * weather_crime_modifier
                )

                if random.random() < prob and len(district_citizens) >= 1:
                    perp = random.choice(district_citizens) if district_citizens else None
                    victim = None
                    if crime_type in ("assault", "robbery", "theft") and len(district_citizens) >= 2:
                        candidates = [c for c in district_citizens if c != perp]
                        if candidates:
                            victim = random.choice(candidates)

                    damage = random.uniform(*config["damage_range"])
                    desc_template = random.choice(CRIME_TEMPLATES[crime_type])
                    description = desc_template.format(
                        perp=perp.name if perp else "Unknown suspect",
                        district=district.get("name", "unknown"),
                    )

                    crime = CrimeRecord(
                        crime_type=crime_type,
                        severity=config["severity"],
                        district_id=district_id,
                        perpetrator_id=perp.id if perp else None,
                        victim_id=victim.id if victim else None,
                        economic_damage=round(damage, 2),
                        description=description,
                        sim_timestamp=sim_time,
                    )
                    self.db.add(crime)
                    crimes_generated += 1

                    if perp:
                        perp.stress = min(1.0, perp.stress + 0.05)
                    if victim:
                        victim.happiness = max(0.0, victim.happiness - 0.05)
                        victim.stress = min(1.0, victim.stress + 0.08)
                        victim.balance = max(0, victim.balance - damage * 0.3)

        crimes_solved += await self._process_investigations(sim_time)

        await self.db.flush()

        total_unsolved = await self.db.scalar(
            select(sqlfunc.count(CrimeRecord.id)).where(
                CrimeRecord.is_solved == False,  # noqa: E712
                CrimeRecord.resolved_at == None,  # noqa: E711
            )
        ) or 0

        return {
            "crimes_generated": crimes_generated,
            "crimes_solved": crimes_solved,
            "total_unsolved": total_unsolved,
        }

    async def _process_investigations(self, sim_time: datetime) -> int:
        result = await self.db.execute(
            select(CrimeRecord).where(
                CrimeRecord.is_solved == False,  # noqa: E712
                CrimeRecord.resolved_at == None,  # noqa: E711
            ).limit(20)
        )
        unsolved = list(result.scalars().all())
        solved_count = 0

        units_result = await self.db.execute(
            select(PoliceUnit).where(PoliceUnit.is_active == True)  # noqa: E712
        )
        units = list(units_result.scalars().all())
        total_effectiveness = sum(u.effectiveness * u.officers for u in units) if units else 5.0

        for crime in unsolved:
            crime.response_time_ticks += 1
            config = CRIME_TYPES.get(crime.crime_type, {})
            base_solve = config.get("solve_rate", 0.3)

            capacity_bonus = min(0.2, total_effectiveness / max(len(unsolved), 1) * 0.01)
            time_factor = min(0.15, crime.response_time_ticks * 0.005)
            solve_chance = base_solve * 0.05 + capacity_bonus + time_factor

            if random.random() < solve_chance:
                crime.is_solved = True
                crime.resolved_at = sim_time
                solved_count += 1

                for unit in units:
                    if unit.district_id == crime.district_id:
                        unit.cases_solved += 1
                        break
                else:
                    if units:
                        units[0].cases_solved += 1

            if crime.response_time_ticks > 100 and not crime.is_solved:
                crime.resolved_at = sim_time

        return solved_count

    async def seed_police_units(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(PoliceUnit.id)))
        if existing and existing > 0:
            return 0

        count = 0
        for d in districts:
            unit = PoliceUnit(
                name=f"{d['name']} Police Station",
                district_id=d.get("id"),
                officers=random.randint(8, 25),
                effectiveness=round(random.uniform(0.5, 0.9), 2),
            )
            self.db.add(unit)
            count += 1
        await self.db.flush()
        return count

    async def get_stats(self) -> dict:
        total = await self.db.scalar(select(sqlfunc.count(CrimeRecord.id))) or 0
        solved = await self.db.scalar(
            select(sqlfunc.count(CrimeRecord.id)).where(CrimeRecord.is_solved == True)  # noqa: E712
        ) or 0
        unsolved = await self.db.scalar(
            select(sqlfunc.count(CrimeRecord.id)).where(
                CrimeRecord.is_solved == False, CrimeRecord.resolved_at == None  # noqa: E711, E712
            )
        ) or 0

        by_type_result = await self.db.execute(
            select(CrimeRecord.crime_type, sqlfunc.count(CrimeRecord.id))
            .group_by(CrimeRecord.crime_type)
        )
        by_type = {row[0]: row[1] for row in by_type_result}

        total_damage = await self.db.scalar(
            select(sqlfunc.sum(CrimeRecord.economic_damage))
        ) or 0

        return {
            "total_crimes": total,
            "solved": solved,
            "unsolved": unsolved,
            "solve_rate": solved / total if total else 0,
            "by_type": by_type,
            "total_economic_damage": round(total_damage, 2),
        }

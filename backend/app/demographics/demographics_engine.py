"""
Demographics & Population Engine: Simulates births, deaths, immigration,
emigration, marriages, and tracks population snapshots over time.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.demographics import LifeEvent, PopulationSnapshot

log = structlog.get_logger()

ORIGIN_COUNTRIES = [
    "Northland", "Eastport", "South Republic",
    "Western Isles", "Central Federation", "Overseas Territory",
]

PROMOTION_TITLES = [
    "Senior Analyst", "Team Lead", "Department Head",
    "Regional Manager", "Director", "VP of Operations",
]


class DemographicsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, sim_time: datetime, tick: int, citizens: list) -> dict:
        self._tick_count += 1
        stats = {"births": 0, "deaths": 0, "immigrants": 0, "emigrants": 0, "marriages": 0, "promotions": 0}

        self._process_births(citizens, stats)
        self._process_deaths(citizens, stats)
        self._process_immigration(citizens, stats)
        self._process_emigration(citizens, stats)
        self._process_life_events(citizens, stats)

        if self._tick_count % 10 == 0:
            await self._take_snapshot(citizens, tick, stats)

        await self.db.flush()
        return stats

    def _process_births(self, citizens: list, stats: dict) -> None:
        for citizen in citizens:
            if citizen.age < 20 or citizen.age > 45:
                continue
            if random.random() < 0.0005:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="birth",
                    description=f"{citizen.name} welcomed a new child",
                )
                self.db.add(event)
                citizen.happiness = min(1.0, citizen.happiness + 0.15)
                stats["births"] += 1

    def _process_deaths(self, citizens: list, stats: dict) -> None:
        for citizen in citizens:
            death_chance = 0.0
            if citizen.age > 75:
                death_chance = 0.001 * (citizen.age - 75) / 10
            if citizen.health < 0.1:
                death_chance += 0.002

            if death_chance > 0 and random.random() < death_chance:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="death",
                    description=f"{citizen.name} passed away at age {citizen.age}",
                )
                self.db.add(event)
                citizen.is_alive = False
                citizen.health = 0.0
                stats["deaths"] += 1

    def _process_immigration(self, citizens: list, stats: dict) -> None:
        if not citizens:
            return
        if random.random() < 0.02:
            count = random.randint(1, 3)
            for _ in range(count):
                origin = random.choice(ORIGIN_COUNTRIES)
                anchor = random.choice(citizens)
                event = LifeEvent(
                    citizen_id=anchor.id,
                    event_type="immigration",
                    description=f"New immigrant arrived from {origin}",
                )
                self.db.add(event)
                stats["immigrants"] += 1

    def _process_emigration(self, citizens: list, stats: dict) -> None:
        unhappy = [c for c in citizens if c.happiness < 0.2 and c.balance < 100]
        for citizen in unhappy:
            if random.random() < 0.005:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="emigration",
                    description=f"{citizen.name} left the city seeking better opportunities",
                )
                self.db.add(event)
                stats["emigrants"] += 1

    def _process_life_events(self, citizens: list, stats: dict) -> None:
        for citizen in citizens:
            if random.random() < 0.001 and citizen.age >= 22 and len(citizens) > 1:
                partner = random.choice(citizens)
                if partner.id != citizen.id:
                    event = LifeEvent(
                        citizen_id=citizen.id,
                        event_type="marriage",
                        description=f"{citizen.name} married",
                        related_citizen_id=partner.id,
                    )
                    self.db.add(event)
                    citizen.happiness = min(1.0, citizen.happiness + 0.1)
                    stats["marriages"] += 1

            if random.random() < 0.0008:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="promotion",
                    description=f"{citizen.name} promoted to {random.choice(PROMOTION_TITLES)}",
                )
                self.db.add(event)
                citizen.happiness = min(1.0, citizen.happiness + 0.05)
                citizen.balance += random.uniform(50, 200)
                stats["promotions"] += 1

            if citizen.age >= 65 and random.random() < 0.002:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="retirement",
                    description=f"{citizen.name} retired after a long career",
                )
                self.db.add(event)
                citizen.happiness = min(1.0, citizen.happiness + 0.08)

    async def _take_snapshot(self, citizens: list, tick: int, stats: dict) -> None:
        total = len(citizens)
        if total == 0:
            return

        ages = [c.age for c in citizens]
        avg_age = sum(ages) / total
        young = sum(1 for a in ages if a < 18)
        old = sum(1 for a in ages if a >= 65)
        working = total - young - old
        dep_ratio = (young + old) / max(1, working)

        snapshot = PopulationSnapshot(
            tick=tick,
            total_population=total,
            births=stats["births"],
            deaths=stats["deaths"],
            immigrants=stats["immigrants"],
            emigrants=stats["emigrants"],
            avg_age=round(avg_age, 1),
            dependency_ratio=round(dep_ratio, 3),
            growth_rate=round((stats["births"] + stats["immigrants"] - stats["deaths"] - stats["emigrants"]) / max(1, total), 4),
        )
        self.db.add(snapshot)

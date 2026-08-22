"""
Demographics & Population Engine: Simulates births, deaths, immigration,
emigration, marriages, and tracks population snapshots over time.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime

import structlog
from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen, Gender, EducationLevel, TransportPreference
from backend.app.models.city import Location, LocationType
from backend.app.models.demographics import LifeEvent, PopulationSnapshot
from backend.app.models.economy import Employment
from backend.app.models.relationship import Relationship, RelationshipType

log = structlog.get_logger()
fake = Faker()

ORIGIN_COUNTRIES = [
    "Northland", "Eastport", "South Republic",
    "Western Isles", "Central Federation", "Overseas Territory",
]

PROMOTION_TITLES = [
    "Senior Analyst", "Team Lead", "Department Head",
    "Regional Manager", "Director", "VP of Operations",
]

PERSONALITY_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


class DemographicsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, sim_time: datetime, tick: int, citizens: list) -> dict:
        self._tick_count += 1
        stats = {"births": 0, "deaths": 0, "immigrants": 0, "emigrants": 0, "marriages": 0, "promotions": 0}

        await self._process_births(citizens, stats)
        self._process_deaths(citizens, stats)
        await self._process_immigration(citizens, stats)
        self._process_emigration(citizens, stats)
        await self._process_life_events(citizens, stats, sim_time)

        if self._tick_count % 10 == 0:
            await self._take_snapshot(citizens, tick, stats)

        await self.db.flush()
        return stats

    async def _process_births(self, citizens: list, stats: dict) -> None:
        for citizen in citizens:
            if citizen.age < 20 or citizen.age > 45:
                continue
            if random.random() < 0.0005:
                gender = random.choice(list(Gender))
                if gender == Gender.MALE:
                    child_name = fake.name_male()
                elif gender == Gender.FEMALE:
                    child_name = fake.name_female()
                else:
                    child_name = fake.name()

                # Blend the parent's traits with a fresh random draw so the child
                # resembles but isn't a clone of the parent.
                parent_traits = citizen.personality_traits or {}
                personality = {
                    trait: round((parent_traits.get(trait, 0.5) + random.uniform(0.1, 0.9)) / 2, 2)
                    for trait in PERSONALITY_TRAITS
                }

                child_id = uuid.uuid4()
                child = Citizen(
                    id=child_id,
                    name=child_name,
                    age=0,
                    gender=gender,
                    education=EducationLevel.NONE,
                    occupation="child",
                    salary=0.0,
                    balance=0.0,
                    personality_traits=personality,
                    goals=[],
                    happiness=round(random.uniform(0.6, 0.9), 2),
                    stress=round(random.uniform(0.0, 0.2), 2),
                    health=round(random.uniform(0.85, 1.0), 2),
                    energy=1.0,
                    hunger=round(random.uniform(0.0, 0.3), 2),
                    social_need=round(random.uniform(0.3, 0.6), 2),
                    political_opinion=0.5,
                    transport_preference=TransportPreference.WALKING,
                    home_location_id=citizen.home_location_id,
                    current_location_id=citizen.home_location_id,
                )
                self.db.add(child)

                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="birth",
                    description=f"{citizen.name} welcomed a new child, {child_name}",
                    related_citizen_id=child_id,
                )
                self.db.add(event)
                citizen.happiness = min(1.0, citizen.happiness + 0.15)

                self.db.add(Relationship(
                    citizen_a_id=citizen.id, citizen_b_id=child_id,
                    relationship_type=RelationshipType.FAMILY,
                    trust_score=0.95, closeness=0.95,
                ))
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

    async def _process_immigration(self, citizens: list, stats: dict) -> None:
        if not citizens:
            return
        if random.random() >= 0.02:
            return

        residential_result = await self.db.execute(
            select(Location).where(Location.location_type == LocationType.RESIDENTIAL)
        )
        residential_locs = residential_result.scalars().all()
        if not residential_locs:
            return

        count = random.randint(1, 3)
        for _ in range(count):
            origin = random.choice(ORIGIN_COUNTRIES)
            gender = random.choice(list(Gender))
            if gender == Gender.MALE:
                name = fake.name_male()
            elif gender == Gender.FEMALE:
                name = fake.name_female()
            else:
                name = fake.name()

            home = random.choice(residential_locs)
            immigrant_id = uuid.uuid4()
            immigrant = Citizen(
                id=immigrant_id,
                name=name,
                age=random.randint(20, 55),
                gender=gender,
                education=random.choices(
                    list(EducationLevel), weights=[0.1, 0.35, 0.3, 0.18, 0.07],
                )[0],
                occupation="unemployed",
                salary=0.0,
                balance=round(random.uniform(200, 5000), 2),
                personality_traits={trait: round(random.uniform(0.1, 0.9), 2) for trait in PERSONALITY_TRAITS},
                goals=random.sample(
                    ["earn_money", "find_love", "stay_healthy", "get_promoted", "learn_new_skill", "travel"],
                    k=random.randint(1, 3),
                ),
                happiness=round(random.uniform(0.4, 0.7), 2),
                stress=round(random.uniform(0.3, 0.6), 2),
                health=round(random.uniform(0.6, 1.0), 2),
                energy=round(random.uniform(0.5, 1.0), 2),
                hunger=round(random.uniform(0.1, 0.4), 2),
                social_need=round(random.uniform(0.4, 0.8), 2),
                political_opinion=round(random.uniform(0.0, 1.0), 3),
                transport_preference=random.choice(list(TransportPreference)),
                home_location_id=home.id,
                current_location_id=home.id,
            )
            self.db.add(immigrant)

            event = LifeEvent(
                citizen_id=immigrant_id,
                event_type="immigration",
                description=f"{name} arrived from {origin} and settled in the city",
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
                # Reuses is_alive (the same flag every population query already filters
                # on) rather than adding a parallel "departed" flag — emigration and
                # death both mean "no longer part of the active population."
                citizen.is_alive = False
                stats["emigrants"] += 1

    async def _process_life_events(self, citizens: list, stats: dict, sim_time: datetime) -> None:
        for citizen in citizens:
            if random.random() < 0.001 and citizen.age >= 22 and len(citizens) > 1:
                partner = random.choice(citizens)
                if partner.id != citizen.id:
                    event = LifeEvent(
                        citizen_id=citizen.id,
                        event_type="marriage",
                        description=f"{citizen.name} married {partner.name}",
                        related_citizen_id=partner.id,
                    )
                    self.db.add(event)
                    citizen.happiness = min(1.0, citizen.happiness + 0.1)
                    partner.happiness = min(1.0, partner.happiness + 0.1)
                    stats["marriages"] += 1

                    existing = await self.db.execute(
                        select(Relationship).where(
                            ((Relationship.citizen_a_id == citizen.id) & (Relationship.citizen_b_id == partner.id))
                            | ((Relationship.citizen_a_id == partner.id) & (Relationship.citizen_b_id == citizen.id))
                        )
                    )
                    rel = existing.scalar_one_or_none()
                    if rel:
                        rel.relationship_type = RelationshipType.FAMILY
                        rel.trust_score = max(rel.trust_score, 0.9)
                        rel.closeness = max(rel.closeness, 0.9)
                    else:
                        self.db.add(Relationship(
                            citizen_a_id=citizen.id, citizen_b_id=partner.id,
                            relationship_type=RelationshipType.FAMILY,
                            trust_score=0.9, closeness=0.9,
                        ))

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

            if citizen.age >= 65 and citizen.occupation != "retired" and random.random() < 0.002:
                event = LifeEvent(
                    citizen_id=citizen.id,
                    event_type="retirement",
                    description=f"{citizen.name} retired after a long career",
                )
                self.db.add(event)
                citizen.happiness = min(1.0, citizen.happiness + 0.08)

                if citizen.workplace_id:
                    emp_result = await self.db.execute(
                        select(Employment).where(
                            Employment.citizen_id == citizen.id, Employment.is_active.is_(True)
                        )
                    )
                    emp = emp_result.scalar_one_or_none()
                    if emp:
                        emp.is_active = False
                        emp.ended_at = sim_time

                citizen.workplace_id = None
                citizen.occupation = "retired"
                citizen.salary = 0.0

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

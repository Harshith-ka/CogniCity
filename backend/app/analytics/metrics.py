"""
Analytics: Collects and computes city-wide metrics.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen, Gender, EducationLevel
from backend.app.models.economy import Business, Transaction
from backend.app.models.event import CityEvent
from backend.app.schemas.analytics import CityMetrics, PopulationBreakdown


async def compute_city_metrics(db: AsyncSession) -> CityMetrics:
    citizens_result = await db.execute(
        select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
    )
    citizens = list(citizens_result.scalars().all())

    businesses_result = await db.execute(select(Business))
    businesses = list(businesses_result.scalars().all())

    events_result = await db.execute(
        select(CityEvent).where(CityEvent.is_active == True)  # noqa: E712
    )
    active_events = list(events_result.scalars().all())

    pop = len(citizens)
    if pop == 0:
        return CityMetrics()

    employed = sum(1 for c in citizens if c.occupation != "unemployed")

    return CityMetrics(
        population=pop,
        employed=employed,
        unemployed=pop - employed,
        unemployment_rate=round((pop - employed) / pop, 4),
        avg_happiness=round(sum(c.happiness for c in citizens) / pop, 4),
        avg_health=round(sum(c.health for c in citizens) / pop, 4),
        avg_stress=round(sum(c.stress for c in citizens) / pop, 4),
        total_gdp=round(sum(c.balance for c in citizens), 2),
        avg_income=round(sum(c.salary for c in citizens) / pop, 2),
        active_businesses=sum(1 for b in businesses if b.is_open),
        total_businesses=len(businesses),
        active_events=len(active_events),
    )


async def compute_population_breakdown(db: AsyncSession) -> PopulationBreakdown:
    citizens_result = await db.execute(
        select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
    )
    citizens = list(citizens_result.scalars().all())

    by_age: dict[str, int] = {"0-17": 0, "18-30": 0, "31-45": 0, "46-60": 0, "61+": 0}
    by_gender: dict[str, int] = {}
    by_education: dict[str, int] = {}
    by_occupation: dict[str, int] = {}

    for c in citizens:
        if c.age < 18:
            by_age["0-17"] += 1
        elif c.age <= 30:
            by_age["18-30"] += 1
        elif c.age <= 45:
            by_age["31-45"] += 1
        elif c.age <= 60:
            by_age["46-60"] += 1
        else:
            by_age["61+"] += 1

        g = c.gender.value
        by_gender[g] = by_gender.get(g, 0) + 1

        e = c.education.value
        by_education[e] = by_education.get(e, 0) + 1

        o = c.occupation
        by_occupation[o] = by_occupation.get(o, 0) + 1

    return PopulationBreakdown(
        by_age=by_age,
        by_gender=by_gender,
        by_education=by_education,
        by_occupation=by_occupation,
    )

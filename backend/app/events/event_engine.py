"""
Event Engine: Manages city events — natural disasters, health crises,
economic shifts, and social events, each scoped to an affected area of the city.
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.models.citizen import Citizen
from backend.app.models.city import Location
from backend.app.models.event import CityEvent, EventCategory, EventSeverity

log = structlog.get_logger()

CITY_WIDE_RADIUS = 5000.0  # radius large enough to cover the whole generated map

EVENT_TEMPLATES = [
    {
        "name": "Earthquake",
        "category": EventCategory.NATURAL_DISASTER,
        "severity": EventSeverity.HIGH,
        "description": "A significant earthquake has struck the city.",
        "duration": 120,
        "impact": {"health": -0.2, "stress": 0.3, "happiness": -0.2, "building_damage": 0.3},
    },
    {
        "name": "Flood",
        "category": EventCategory.NATURAL_DISASTER,
        "severity": EventSeverity.MEDIUM,
        "description": "Heavy rains have caused flooding in low-lying areas.",
        "duration": 200,
        "impact": {"health": -0.1, "stress": 0.2, "transport_disruption": 0.5},
    },
    {
        "name": "Pandemic Outbreak",
        "category": EventCategory.HEALTH,
        "severity": EventSeverity.CRITICAL,
        "description": "A new virus has been detected in the city.",
        "duration": 500,
        "impact": {"health": -0.3, "stress": 0.4, "happiness": -0.3, "economic_slowdown": 0.4},
    },
    {
        "name": "Food Poisoning Alert",
        "category": EventCategory.HEALTH,
        "severity": EventSeverity.LOW,
        "description": "Several restaurants have been flagged for food safety issues.",
        "duration": 50,
        "impact": {"health": -0.1, "stress": 0.1},
    },
    {
        "name": "Economic Recession",
        "category": EventCategory.ECONOMIC,
        "severity": EventSeverity.HIGH,
        "description": "The city is entering an economic downturn.",
        "duration": 1000,
        "impact": {"salary_cut": 0.2, "unemployment_spike": 0.1, "stress": 0.2, "happiness": -0.15},
    },
    {
        "name": "Startup Boom",
        "category": EventCategory.ECONOMIC,
        "severity": EventSeverity.LOW,
        "description": "A wave of new startups is creating jobs.",
        "duration": 300,
        "impact": {"employment_boost": 0.1, "happiness": 0.1, "economic_growth": 0.15},
    },
    {
        "name": "Power Outage",
        "category": EventCategory.INFRASTRUCTURE,
        "severity": EventSeverity.MEDIUM,
        "description": "A major power failure has affected several districts.",
        "duration": 30,
        "impact": {"stress": 0.15, "happiness": -0.1, "business_disruption": 0.3},
    },
    {
        "name": "City Festival",
        "category": EventCategory.SOCIAL,
        "severity": EventSeverity.LOW,
        "description": "The annual city festival is bringing joy to residents.",
        "duration": 72,
        "impact": {"happiness": 0.2, "stress": -0.1, "social_boost": 0.3},
    },
    {
        "name": "Protest Rally",
        "category": EventCategory.SOCIAL,
        "severity": EventSeverity.MEDIUM,
        "description": "Citizens are protesting government policies.",
        "duration": 24,
        "impact": {"stress": 0.15, "happiness": -0.05, "political_tension": 0.3},
    },
    {
        "name": "Elections",
        "category": EventCategory.POLITICAL,
        "severity": EventSeverity.MEDIUM,
        "description": "Municipal elections are underway.",
        "duration": 48,
        "impact": {"stress": 0.1, "political_engagement": 0.5},
    },
]


class EventEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_event(
        self,
        template_name: str | None = None,
        sim_time: datetime | None = None,
        area_x: float | None = None,
        area_y: float | None = None,
        radius: float = CITY_WIDE_RADIUS,
    ) -> CityEvent:
        """area_x/area_y left as None (the default) means city-wide — every citizen is
        affected regardless of location. Pass explicit coordinates to scope the event
        to a specific area, e.g. a chosen district."""
        if template_name:
            template = next(
                (t for t in EVENT_TEMPLATES if t["name"].lower() == template_name.lower()),
                None,
            )
        else:
            template = random.choice(EVENT_TEMPLATES)

        if not template:
            template = random.choice(EVENT_TEMPLATES)

        event = CityEvent(
            name=template["name"],
            category=template["category"],
            severity=template["severity"],
            description=template["description"],
            affected_area_x=area_x,
            affected_area_y=area_y,
            affected_radius=radius,
            impact=template["impact"],
            duration_ticks=template["duration"],
            remaining_ticks=template["duration"],
            is_active=True,
            sim_started_at=sim_time or datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.flush()

        log.info("event_triggered", event_name=event.name, severity=event.severity)
        return event

    async def apply_event_effects(self, event: CityEvent) -> int:
        """Apply event impact to citizens within the event's affected radius.
        A citizen's position is their current location, falling back to home."""
        result = await self.db.execute(
            select(Citizen)
            .where(Citizen.is_alive == True)  # noqa: E712
            .options(
                joinedload(Citizen.current_location),
                joinedload(Citizen.home_location),
            )
        )
        citizens = list(result.unique().scalars().all())
        affected = 0

        impact = event.impact or {}
        health_delta = impact.get("health", 0.0)
        stress_delta = impact.get("stress", 0.0)
        happiness_delta = impact.get("happiness", 0.0)
        scale = 1.0 / max(event.duration_ticks, 1)

        area_x = event.affected_area_x
        area_y = event.affected_area_y
        radius = event.affected_radius or CITY_WIDE_RADIUS

        for citizen in citizens:
            if area_x is not None and area_y is not None:
                loc = citizen.current_location or citizen.home_location
                if loc is not None:
                    dist = math.sqrt((loc.x - area_x) ** 2 + (loc.y - area_y) ** 2)
                    if dist > radius:
                        continue
                    proximity = max(0.0, 1.0 - dist / radius)
                else:
                    proximity = 1.0
            else:
                proximity = 1.0

            citizen.health = max(0.0, min(1.0, citizen.health + health_delta * scale * proximity))
            citizen.stress = max(0.0, min(1.0, citizen.stress + stress_delta * scale * proximity))
            citizen.happiness = max(0.0, min(1.0, citizen.happiness + happiness_delta * scale * proximity))

            affected += 1

        await self.db.flush()
        return affected

    async def get_active_events(self) -> list[CityEvent]:
        result = await self.db.execute(
            select(CityEvent).where(CityEvent.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def random_event_chance(self, sim_time: datetime, probability: float = 0.005) -> CityEvent | None:
        """Small chance of a random event each tick."""
        if random.random() < probability:
            return await self.trigger_event(sim_time=sim_time)
        return None

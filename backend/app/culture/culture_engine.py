"""
Culture & Entertainment Engine: Manages venues, festivals, and citizen leisure.
Venues generate revenue from visitors; festivals boost city-wide happiness.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.culture import Venue, CityFestival

log = structlog.get_logger()

VENUE_PRESETS = [
    {"name": "Grand Theater", "venue_type": "theater", "capacity": 300, "ticket_price": 35.0, "quality": 0.8},
    {"name": "City Stadium", "venue_type": "stadium", "capacity": 5000, "ticket_price": 50.0, "quality": 0.7},
    {"name": "Artisan Gallery", "venue_type": "gallery", "capacity": 80, "ticket_price": 12.0, "quality": 0.75},
    {"name": "Heritage Museum", "venue_type": "museum", "capacity": 200, "ticket_price": 10.0, "quality": 0.85},
    {"name": "Central Park", "venue_type": "park", "capacity": 1000, "ticket_price": 0.0, "quality": 0.7},
    {"name": "Jazz Club", "venue_type": "club", "capacity": 120, "ticket_price": 25.0, "quality": 0.65},
    {"name": "Riverside Restaurant", "venue_type": "restaurant", "capacity": 60, "ticket_price": 30.0, "quality": 0.7},
    {"name": "Skyline Bar", "venue_type": "bar", "capacity": 80, "ticket_price": 15.0, "quality": 0.6},
]

FESTIVAL_TEMPLATES = [
    {"name": "Summer Music Festival", "event_type": "concert", "max_attendees": 2000, "happiness_boost": 0.08, "duration_ticks": 15},
    {"name": "International Food Fair", "event_type": "food_fair", "max_attendees": 1500, "happiness_boost": 0.06, "duration_ticks": 10},
    {"name": "Art & Culture Exhibition", "event_type": "exhibition", "max_attendees": 800, "happiness_boost": 0.04, "duration_ticks": 20},
    {"name": "City Marathon", "event_type": "sports", "max_attendees": 3000, "happiness_boost": 0.05, "duration_ticks": 5},
    {"name": "Heritage Parade", "event_type": "parade", "max_attendees": 5000, "happiness_boost": 0.07, "duration_ticks": 3},
    {"name": "Tech Innovation Fest", "event_type": "festival", "max_attendees": 1000, "happiness_boost": 0.05, "duration_ticks": 12},
]


class CultureEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, sim_time: datetime, citizens: list) -> dict:
        self._tick_count += 1
        stats = {"venue_revenue": 0.0, "total_visitors": 0, "active_festivals": 0, "happiness_delivered": 0.0}

        await self._process_venues(citizens, stats)
        await self._process_festivals(citizens, stats, sim_time)

        if self._tick_count % 50 == 0 and random.random() < 0.4:
            await self._start_festival(sim_time)

        await self.db.flush()
        return stats

    async def _process_venues(self, citizens: list, stats: dict) -> None:
        result = await self.db.execute(select(Venue).where(Venue.is_open.is_(True)))
        venues = result.scalars().all()
        if not venues or not citizens:
            return

        for venue in venues:
            visit_chance = venue.popularity * 0.02
            visitors = sum(1 for _ in citizens if random.random() < visit_chance)
            visitors = min(visitors, venue.capacity)

            revenue = visitors * venue.ticket_price
            venue.daily_revenue = revenue
            venue.total_visitors += visitors
            venue.popularity = min(1.0, venue.popularity + visitors * 0.0001)

            stats["venue_revenue"] += revenue
            stats["total_visitors"] += visitors

    async def _process_festivals(self, citizens: list, stats: dict, sim_time: datetime) -> None:
        result = await self.db.execute(select(CityFestival).where(CityFestival.is_active.is_(True)))
        festivals = result.scalars().all()
        if not citizens:
            return

        for festival in festivals:
            festival.ticks_remaining -= 1
            new_attendees = int(len(citizens) * festival.happiness_boost * random.uniform(0.5, 1.5))
            new_attendees = min(new_attendees, max(0, festival.max_attendees - festival.attendees))
            festival.attendees += max(0, new_attendees)

            boost = festival.happiness_boost * 0.1
            sample_size = min(len(citizens), max(1, int(len(citizens) * 0.3)))
            for c in random.sample(citizens, sample_size):
                c.happiness = min(1.0, c.happiness + boost)
                stats["happiness_delivered"] += boost

            stats["active_festivals"] += 1

            if festival.ticks_remaining <= 0:
                festival.is_active = False
                festival.sim_ended_at = sim_time
                log.info("festival_ended", name=festival.name, attendees=festival.attendees)

    async def _start_festival(self, sim_time: datetime) -> None:
        template = random.choice(FESTIVAL_TEMPLATES)

        result = await self.db.execute(select(Venue).where(Venue.is_open.is_(True)).order_by(sqlfunc.random()).limit(1))
        venue = result.scalar_one_or_none()

        festival = CityFestival(
            name=template["name"],
            event_type=template["event_type"],
            venue_id=venue.id if venue else None,
            district_id=venue.district_id if venue else None,
            max_attendees=template["max_attendees"],
            happiness_boost=template["happiness_boost"],
            duration_ticks=template["duration_ticks"],
            ticks_remaining=template["duration_ticks"],
            is_active=True,
            sim_started_at=sim_time,
        )
        self.db.add(festival)
        log.info("festival_started", name=festival.name, type=festival.event_type)

    async def seed_venues(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(Venue.id)))
        if existing and existing > 0:
            return 0

        count = 0
        for i, d in enumerate(districts):
            preset = VENUE_PRESETS[i % len(VENUE_PRESETS)]
            venue = Venue(
                name=f"{preset['name']} ({d['name']})",
                venue_type=preset["venue_type"],
                district_id=d.get("id"),
                capacity=preset["capacity"],
                ticket_price=preset["ticket_price"],
                quality=preset["quality"],
                popularity=random.uniform(0.3, 0.7),
            )
            self.db.add(venue)
            count += 1

        if len(districts) > 3:
            for preset in random.sample(VENUE_PRESETS, min(3, len(VENUE_PRESETS))):
                d = random.choice(districts)
                venue = Venue(
                    name=f"{preset['name']} 2 ({d['name']})",
                    venue_type=preset["venue_type"],
                    district_id=d.get("id"),
                    capacity=preset["capacity"],
                    ticket_price=preset["ticket_price"],
                    quality=preset["quality"],
                    popularity=random.uniform(0.3, 0.6),
                )
                self.db.add(venue)
                count += 1

        await self.db.flush()
        log.info("venues_seeded", count=count)
        return count

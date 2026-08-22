"""
Tourism Engine: Manages hotels, attractions, and tourist visitors.
Tourists arrive based on city reputation, spend money, visit attractions,
and leave reviews that affect future tourism.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.tourism import Hotel, TouristAttraction, TouristVisitor

log = structlog.get_logger()

HOTEL_PRESETS = [
    {"name": "Budget Inn", "hotel_class": 2, "total_rooms": 30, "price_per_night": 50.0},
    {"name": "City Comfort Hotel", "hotel_class": 3, "total_rooms": 60, "price_per_night": 120.0},
    {"name": "Grand Plaza Hotel", "hotel_class": 4, "total_rooms": 100, "price_per_night": 220.0},
    {"name": "Royal Suites", "hotel_class": 5, "total_rooms": 40, "price_per_night": 400.0},
    {"name": "Traveler's Lodge", "hotel_class": 2, "total_rooms": 25, "price_per_night": 45.0},
    {"name": "Skyline Tower Hotel", "hotel_class": 4, "total_rooms": 80, "price_per_night": 250.0},
]

ATTRACTION_PRESETS = [
    {"name": "Historic City Hall", "attraction_type": "landmark", "ticket_price": 10.0, "capacity": 300},
    {"name": "Natural History Museum", "attraction_type": "museum", "ticket_price": 15.0, "capacity": 250},
    {"name": "Botanical Gardens", "attraction_type": "park", "ticket_price": 8.0, "capacity": 500},
    {"name": "Victory Monument", "attraction_type": "monument", "ticket_price": 5.0, "capacity": 400},
    {"name": "City Aquarium", "attraction_type": "museum", "ticket_price": 20.0, "capacity": 200},
    {"name": "Adventure Theme Park", "attraction_type": "theme_park", "ticket_price": 40.0, "capacity": 1000},
]

TOURIST_ORIGINS = [
    "Domestic", "Northland", "Eastport", "South Republic",
    "Western Isles", "Overseas", "Archipelago", "Continental",
]


class TourismEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._tick_count = 0

    async def process_tick(self, city_happiness: float = 0.5, weather_condition: str = "clear") -> dict:
        self._tick_count += 1
        stats = {"active_tourists": 0, "arrivals": 0, "departures": 0, "tourism_revenue": 0.0, "attraction_visits": 0}

        await self._process_arrivals(city_happiness, weather_condition, stats)
        await self._process_tourists(stats)
        await self._process_attractions(stats)
        await self._process_departures(stats)

        await self.db.flush()
        return stats

    async def _process_arrivals(self, city_happiness: float, weather_condition: str, stats: dict) -> None:
        arrival_chance = 0.1 + city_happiness * 0.15
        if weather_condition in ("storm", "snow", "cold_snap"):
            arrival_chance *= 0.5
        elif weather_condition in ("clear", "cloudy"):
            arrival_chance *= 1.2

        if random.random() < arrival_chance:
            count = random.randint(1, 5)
            hotels_result = await self.db.execute(
                select(Hotel).where(Hotel.occupied_rooms < Hotel.total_rooms).order_by(sqlfunc.random())
            )
            available_hotels = hotels_result.scalars().all()

            for _ in range(count):
                hotel = random.choice(available_hotels) if available_hotels else None
                budget_range = random.choice([(200, 500), (500, 1500), (1500, 5000)])
                visitor = TouristVisitor(
                    origin_country=random.choice(TOURIST_ORIGINS),
                    hotel_id=hotel.id if hotel else None,
                    budget=random.uniform(*budget_range),
                    stay_duration_ticks=random.randint(10, 40),
                    ticks_remaining=random.randint(10, 40),
                    satisfaction=random.uniform(0.5, 0.8),
                    is_active=True,
                )
                self.db.add(visitor)

                if hotel:
                    hotel.occupied_rooms = min(hotel.total_rooms, hotel.occupied_rooms + 1)
                    hotel.total_guests += 1

                stats["arrivals"] += 1

    async def _process_tourists(self, stats: dict) -> None:
        result = await self.db.execute(select(TouristVisitor).where(TouristVisitor.is_active.is_(True)))
        tourists = result.scalars().all()

        for tourist in tourists:
            tourist.ticks_remaining -= 1
            daily_spend = random.uniform(10, 50)
            tourist.spent += daily_spend
            tourist.satisfaction += random.uniform(-0.02, 0.03)
            tourist.satisfaction = max(0.0, min(1.0, tourist.satisfaction))
            stats["tourism_revenue"] += daily_spend
            stats["active_tourists"] += 1

            if tourist.hotel_id:
                hotel_result = await self.db.execute(select(Hotel).where(Hotel.id == tourist.hotel_id))
                hotel = hotel_result.scalar_one_or_none()
                if hotel:
                    hotel.daily_revenue += hotel.price_per_night / 10

    async def _process_attractions(self, stats: dict) -> None:
        result = await self.db.execute(select(TouristAttraction))
        attractions = result.scalars().all()

        tourist_result = await self.db.execute(
            select(sqlfunc.count()).select_from(TouristVisitor).where(TouristVisitor.is_active.is_(True))
        )
        active_count = tourist_result.scalar() or 0

        for attraction in attractions:
            visitors = int(active_count * attraction.popularity * random.uniform(0.05, 0.2))
            visitors = min(visitors, attraction.capacity)
            attraction.daily_visitors = visitors
            attraction.total_visitors += visitors
            attraction.popularity = min(1.0, attraction.popularity + visitors * 0.00005)
            stats["attraction_visits"] += visitors

    async def _process_departures(self, stats: dict) -> None:
        result = await self.db.execute(
            select(TouristVisitor).where(TouristVisitor.is_active.is_(True), TouristVisitor.ticks_remaining <= 0)
        )
        departing = result.scalars().all()

        for tourist in departing:
            tourist.is_active = False
            if tourist.hotel_id:
                hotel_result = await self.db.execute(select(Hotel).where(Hotel.id == tourist.hotel_id))
                hotel = hotel_result.scalar_one_or_none()
                if hotel:
                    hotel.occupied_rooms = max(0, hotel.occupied_rooms - 1)

            stats["departures"] += 1

    async def seed_hotels_and_attractions(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(Hotel.id)))
        if existing and existing > 0:
            return 0

        count = 0
        for i, preset in enumerate(HOTEL_PRESETS):
            d = districts[i % len(districts)]
            hotel = Hotel(
                name=f"{preset['name']} ({d['name']})",
                hotel_class=preset["hotel_class"],
                district_id=d.get("id"),
                total_rooms=preset["total_rooms"],
                price_per_night=preset["price_per_night"],
                rating=random.uniform(3.0, 5.0),
                amenities=random.sample(["wifi", "pool", "gym", "spa", "restaurant", "parking", "bar"], k=random.randint(2, 5)),
            )
            self.db.add(hotel)
            count += 1

        for i, preset in enumerate(ATTRACTION_PRESETS):
            d = districts[i % len(districts)]
            attraction = TouristAttraction(
                name=f"{preset['name']} ({d['name']})",
                attraction_type=preset["attraction_type"],
                district_id=d.get("id"),
                ticket_price=preset["ticket_price"],
                capacity=preset["capacity"],
                popularity=random.uniform(0.3, 0.8),
                rating=random.uniform(3.5, 5.0),
            )
            self.db.add(attraction)
            count += 1

        await self.db.flush()
        log.info("tourism_seeded", hotels=len(HOTEL_PRESETS), attractions=len(ATTRACTION_PRESETS))
        return count

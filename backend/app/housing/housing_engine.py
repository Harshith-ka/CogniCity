"""
Housing & Real Estate Engine: Property market simulation with rent collection,
buying/selling, district-based property values, and homelessness tracking.
Property values fluctuate based on district safety, wealth, and demand.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.housing import Property, PropertyTransaction
from backend.app.models.citizen import Citizen

log = structlog.get_logger()

PROPERTY_TYPES = {
    "studio":    {"size_range": (25, 40),  "value_range": (40000, 80000),   "rent_range": (400, 700)},
    "apartment": {"size_range": (50, 90),  "value_range": (80000, 200000),  "rent_range": (600, 1200)},
    "condo":     {"size_range": (70, 120), "value_range": (150000, 350000), "rent_range": (900, 1800)},
    "house":     {"size_range": (100, 200),"value_range": (200000, 500000), "rent_range": (1200, 2500)},
    "penthouse": {"size_range": (150, 300),"value_range": (400000, 1000000),"rent_range": (2000, 5000)},
    "shelter":   {"size_range": (10, 20),  "value_range": (0, 0),          "rent_range": (0, 50)},
}


class HousingEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._last_rent_day = -1

    async def process_tick(self, sim_time: datetime, day: int, citizens: list) -> dict:
        rent_collected = 0
        evictions = 0
        new_tenants = 0
        value_changes = 0

        if day != self._last_rent_day and day % 30 == 0:
            self._last_rent_day = day
            rent_result = await self._collect_rent(sim_time, citizens)
            rent_collected = rent_result["collected"]
            evictions = rent_result["evictions"]

        new_tenants = await self._match_homeless_to_properties(sim_time, citizens)

        if day % 10 == 0:
            value_changes = await self._update_property_values()

        await self.db.flush()

        homeless = sum(1 for c in citizens if c.occupation != "unemployed" or True)
        homeless_count = await self._count_homeless(citizens)

        return {
            "rent_collected": rent_collected,
            "evictions": evictions,
            "new_tenants": new_tenants,
            "value_changes": value_changes,
            "homeless": homeless_count,
        }

    async def _collect_rent(self, sim_time: datetime, citizens: list) -> dict:
        result = await self.db.execute(
            select(Property).where(
                Property.is_occupied == True,  # noqa: E712
                Property.tenant_id != None,  # noqa: E711
            )
        )
        properties = list(result.scalars().all())
        citizen_map = {c.id: c for c in citizens}
        collected = 0
        evictions = 0

        for prop in properties:
            tenant = citizen_map.get(prop.tenant_id)
            if not tenant:
                continue

            rent = prop.monthly_rent
            if tenant.balance >= rent:
                tenant.balance -= rent
                collected += rent

                tx = PropertyTransaction(
                    property_id=prop.id,
                    transaction_type="rent_payment",
                    amount=rent,
                    buyer_id=tenant.id,
                    seller_id=prop.owner_id,
                    sim_timestamp=sim_time,
                )
                self.db.add(tx)

                if prop.owner_id:
                    owner = citizen_map.get(prop.owner_id)
                    if owner:
                        owner.balance += rent * 0.9
            else:
                if tenant.balance < rent * 0.3:
                    prop.tenant_id = None
                    prop.is_occupied = False
                    prop.is_for_rent = True
                    evictions += 1

                    tenant.stress = min(1.0, tenant.stress + 0.2)
                    tenant.happiness = max(0.0, tenant.happiness - 0.15)

                    tx = PropertyTransaction(
                        property_id=prop.id,
                        transaction_type="eviction",
                        amount=0,
                        buyer_id=tenant.id,
                        sim_timestamp=sim_time,
                    )
                    self.db.add(tx)

        return {"collected": collected, "evictions": evictions}

    async def _match_homeless_to_properties(self, sim_time: datetime, citizens: list) -> int:
        result = await self.db.execute(
            select(Property).where(
                Property.is_for_rent == True,  # noqa: E712
                Property.is_occupied == False,  # noqa: E712
            ).order_by(Property.monthly_rent.asc()).limit(20)
        )
        available = list(result.scalars().all())
        if not available:
            return 0

        housed_ids = set()
        prop_result = await self.db.execute(
            select(Property.tenant_id).where(Property.tenant_id != None)  # noqa: E711
        )
        for row in prop_result:
            if row[0]:
                housed_ids.add(row[0])

        homeless = [c for c in citizens if c.id not in housed_ids]
        random.shuffle(homeless)

        matched = 0
        for citizen in homeless[:len(available)]:
            for prop in available:
                if prop.is_occupied:
                    continue
                if citizen.balance > prop.monthly_rent * 2:
                    prop.tenant_id = citizen.id
                    prop.is_occupied = True
                    prop.is_for_rent = False
                    matched += 1

                    tx = PropertyTransaction(
                        property_id=prop.id,
                        transaction_type="rent_payment",
                        amount=prop.monthly_rent,
                        buyer_id=citizen.id,
                        sim_timestamp=sim_time,
                    )
                    self.db.add(tx)
                    break

        return matched

    async def _update_property_values(self) -> int:
        result = await self.db.execute(select(Property).limit(100))
        properties = list(result.scalars().all())
        changes = 0

        for prop in properties:
            shift = random.uniform(-0.02, 0.03)
            if prop.is_occupied:
                shift += 0.005
            else:
                shift -= 0.01

            prop.market_value = max(1000, prop.market_value * (1 + shift))
            prop.monthly_rent = max(50, prop.monthly_rent * (1 + shift * 0.5))
            prop.condition = max(0.1, prop.condition - 0.002)
            changes += 1

        return changes

    async def _count_homeless(self, citizens: list) -> int:
        prop_result = await self.db.execute(
            select(Property.tenant_id).where(Property.tenant_id != None)  # noqa: E711
        )
        housed_ids = {row[0] for row in prop_result if row[0]}
        return sum(1 for c in citizens if c.id not in housed_ids)

    async def seed_properties(self, districts: list[dict], population: int) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(Property.id)))
        if existing and existing > 0:
            return 0

        count = 0
        per_district = max(5, population // len(districts) + 5) if districts else 20

        for d in districts:
            wealth = d.get("wealth", 0.5)

            if wealth > 0.7:
                weights = {"penthouse": 0.1, "house": 0.2, "condo": 0.3, "apartment": 0.3, "studio": 0.1}
            elif wealth > 0.4:
                weights = {"house": 0.1, "condo": 0.15, "apartment": 0.4, "studio": 0.3, "shelter": 0.05}
            else:
                weights = {"apartment": 0.3, "studio": 0.4, "shelter": 0.3}

            types = list(weights.keys())
            probs = list(weights.values())

            for _ in range(per_district):
                p_type = random.choices(types, probs)[0]
                cfg = PROPERTY_TYPES[p_type]
                value_mult = 0.7 + wealth * 0.6

                prop = Property(
                    name=f"{d['name']} {p_type.title()} #{count+1}",
                    property_type=p_type,
                    district_id=d.get("id"),
                    market_value=round(random.uniform(*cfg["value_range"]) * value_mult),
                    monthly_rent=round(random.uniform(*cfg["rent_range"]) * value_mult),
                    size_sqm=random.randint(*cfg["size_range"]),
                    quality=round(0.3 + wealth * 0.4 + random.uniform(0, 0.2), 2),
                    condition=round(random.uniform(0.5, 1.0), 2),
                )
                self.db.add(prop)
                count += 1

        await self.db.flush()
        return count

    async def get_stats(self) -> dict:
        total = await self.db.scalar(select(sqlfunc.count(Property.id))) or 0
        occupied = await self.db.scalar(
            select(sqlfunc.count(Property.id)).where(Property.is_occupied == True)  # noqa: E712
        ) or 0
        for_rent = await self.db.scalar(
            select(sqlfunc.count(Property.id)).where(Property.is_for_rent == True)  # noqa: E712
        ) or 0
        avg_rent = await self.db.scalar(select(sqlfunc.avg(Property.monthly_rent))) or 0
        avg_value = await self.db.scalar(select(sqlfunc.avg(Property.market_value))) or 0

        by_type_result = await self.db.execute(
            select(Property.property_type, sqlfunc.count(Property.id))
            .group_by(Property.property_type)
        )
        by_type = {row[0]: row[1] for row in by_type_result}

        return {
            "total_properties": total,
            "occupied": occupied,
            "for_rent": for_rent,
            "occupancy_rate": occupied / total if total else 0,
            "avg_rent": round(avg_rent, 0),
            "avg_market_value": round(avg_value, 0),
            "by_type": by_type,
        }

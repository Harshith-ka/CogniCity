"""
Healthcare & Wellness Engine: Simulates citizen health conditions,
hospital capacity, treatment, and mental health. Citizens can develop
conditions from stress, weather, disasters, or random chance. Hospitals
treat patients with quality-dependent outcomes.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.healthcare import Hospital, MedicalRecord
from backend.app.models.citizen import Citizen

log = structlog.get_logger()

CONDITIONS = {
    "flu":            {"type": "acute",   "severity_range": (0.2, 0.5), "duration": (5, 15),  "cost": (100, 500),   "health_trigger": 0.6},
    "food_poisoning": {"type": "acute",   "severity_range": (0.2, 0.4), "duration": (3, 8),   "cost": (50, 300),    "health_trigger": 0.7},
    "injury":         {"type": "acute",   "severity_range": (0.3, 0.7), "duration": (8, 30),  "cost": (200, 2000),  "health_trigger": 0.5},
    "chronic_pain":   {"type": "chronic", "severity_range": (0.2, 0.5), "duration": (20, 60), "cost": (300, 1500),  "health_trigger": 0.4},
    "depression":     {"type": "mental",  "severity_range": (0.3, 0.7), "duration": (15, 50), "cost": (200, 1000),  "health_trigger": 0.5},
    "anxiety":        {"type": "mental",  "severity_range": (0.2, 0.6), "duration": (10, 40), "cost": (150, 800),   "health_trigger": 0.6},
    "stress_disorder":{"type": "mental",  "severity_range": (0.4, 0.8), "duration": (20, 60), "cost": (300, 1200),  "health_trigger": 0.3},
    "heat_stroke":    {"type": "acute",   "severity_range": (0.5, 0.9), "duration": (3, 10),  "cost": (500, 2000),  "health_trigger": 0.5},
    "hypothermia":    {"type": "acute",   "severity_range": (0.5, 0.8), "duration": (3, 10),  "cost": (500, 1500),  "health_trigger": 0.5},
}


class HealthcareEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_tick(
        self,
        sim_time: datetime,
        citizens: list,
        weather: dict | None = None,
    ) -> dict:
        new_conditions = 0
        treatments_completed = 0
        hospitalizations = 0

        new_conditions += await self._check_citizen_health(citizens, sim_time, weather)
        treatments_completed += await self._process_treatments(sim_time)
        hospitalizations = await self._count_hospitalized()

        await self.db.flush()

        return {
            "new_conditions": new_conditions,
            "treatments_completed": treatments_completed,
            "hospitalizations": hospitalizations,
        }

    async def _check_citizen_health(
        self, citizens: list, sim_time: datetime, weather: dict | None
    ) -> int:
        new_count = 0

        # One query for everyone who already has an unresolved record, instead of one
        # query per citizen — the latter is 1000 round-trips a tick at real population.
        existing_result = await self.db.execute(
            select(MedicalRecord.citizen_id).where(MedicalRecord.is_resolved == False)  # noqa: E712
        )
        already_sick = {row[0] for row in existing_result.all()}

        for citizen in citizens:
            if citizen.id in already_sick:
                continue

            condition = self._roll_condition(citizen, weather)
            if not condition:
                continue

            cfg = CONDITIONS[condition]
            severity = random.uniform(*cfg["severity_range"])
            duration = random.randint(*cfg["duration"])
            cost = random.uniform(*cfg["cost"])

            needs_hospital = severity > 0.6
            hospital = await self._find_hospital(cfg["type"]) if needs_hospital else None

            record = MedicalRecord(
                citizen_id=citizen.id,
                hospital_id=hospital.id if hospital else None,
                condition=condition,
                condition_type=cfg["type"],
                severity=round(severity, 2),
                is_hospitalized=hospital is not None,
                treatment_cost=round(cost, 2),
                treatment_ticks=duration,
                ticks_remaining=duration,
                diagnosis=f"{condition.replace('_', ' ').title()} — severity {severity:.0%}",
                sim_timestamp=sim_time,
            )
            self.db.add(record)

            citizen.health = max(0.1, citizen.health - severity * 0.15)
            if cfg["type"] == "mental":
                citizen.stress = min(1.0, citizen.stress + severity * 0.1)
                citizen.happiness = max(0.0, citizen.happiness - severity * 0.1)

            if hospital:
                hospital.occupied_beds = min(hospital.total_beds, hospital.occupied_beds + 1)

            new_count += 1

        return new_count

    def _roll_condition(self, citizen, weather: dict | None) -> str | None:
        if citizen.stress > 0.8 and random.random() < 0.008:
            return random.choice(["depression", "anxiety", "stress_disorder"])

        if citizen.health < 0.5 and random.random() < 0.01:
            return random.choice(["flu", "chronic_pain", "injury"])

        if weather:
            if weather.get("condition") == "heatwave" and random.random() < 0.005:
                return "heat_stroke"
            if weather.get("condition") == "cold_snap" and random.random() < 0.004:
                return "hypothermia"
            if weather.get("condition") in ("rain", "storm") and random.random() < 0.003:
                return "flu"

        if random.random() < 0.002:
            return random.choice(["flu", "food_poisoning", "injury"])

        return None

    async def _find_hospital(self, condition_type: str) -> Hospital | None:
        preferred = "psychiatric" if condition_type == "mental" else "general"
        result = await self.db.execute(
            select(Hospital).where(
                Hospital.is_operational == True,  # noqa: E712
                Hospital.hospital_type == preferred,
            ).order_by(
                (Hospital.total_beds - Hospital.occupied_beds).desc()
            ).limit(1)
        )
        hospital = result.scalar_one_or_none()
        if not hospital:
            result = await self.db.execute(
                select(Hospital).where(
                    Hospital.is_operational == True,  # noqa: E712
                ).order_by(
                    (Hospital.total_beds - Hospital.occupied_beds).desc()
                ).limit(1)
            )
            hospital = result.scalar_one_or_none()

        if hospital and hospital.occupied_beds >= hospital.total_beds:
            return None
        return hospital

    async def _process_treatments(self, sim_time: datetime) -> int:
        result = await self.db.execute(
            select(MedicalRecord).where(
                MedicalRecord.is_resolved == False  # noqa: E712
            ).limit(50)
        )
        records = list(result.scalars().all())
        completed = 0

        for record in records:
            record.ticks_remaining -= 1

            if record.ticks_remaining <= 0:
                record.is_resolved = True
                record.is_treated = True
                record.resolved_at = sim_time
                completed += 1

                citizen_result = await self.db.execute(
                    select(Citizen).where(Citizen.id == record.citizen_id).limit(1)
                )
                citizen = citizen_result.scalar_one_or_none()
                if citizen:
                    citizen.health = min(1.0, citizen.health + record.severity * 0.2)
                    citizen.balance -= record.treatment_cost
                    if record.condition_type == "mental":
                        citizen.stress = max(0.0, citizen.stress - 0.1)

                if record.is_hospitalized and record.hospital_id:
                    h_result = await self.db.execute(
                        select(Hospital).where(Hospital.id == record.hospital_id).limit(1)
                    )
                    hospital = h_result.scalar_one_or_none()
                    if hospital:
                        hospital.occupied_beds = max(0, hospital.occupied_beds - 1)

        return completed

    async def _count_hospitalized(self) -> int:
        return await self.db.scalar(
            select(sqlfunc.count(MedicalRecord.id)).where(
                MedicalRecord.is_hospitalized == True,  # noqa: E712
                MedicalRecord.is_resolved == False,  # noqa: E712
            )
        ) or 0

    async def seed_hospitals(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(Hospital.id)))
        if existing and existing > 0:
            return 0

        count = 0
        types = ["general", "emergency", "psychiatric", "clinic"]
        for i, d in enumerate(districts):
            h_type = types[i % len(types)]
            hospital = Hospital(
                name=f"{d['name']} {h_type.title()} Hospital",
                hospital_type=h_type,
                district_id=d.get("id"),
                total_beds=random.randint(50, 200),
                icu_beds=random.randint(5, 20),
                staff_count=random.randint(30, 100),
                quality_rating=round(random.uniform(0.5, 0.95), 2),
                funding=round(random.uniform(200000, 800000), 0),
            )
            self.db.add(hospital)
            count += 1
        await self.db.flush()
        return count

    async def get_stats(self) -> dict:
        hospitals = await self.db.execute(select(Hospital))
        hospitals_list = list(hospitals.scalars().all())

        total_beds = sum(h.total_beds for h in hospitals_list)
        occupied = sum(h.occupied_beds for h in hospitals_list)
        total_records = await self.db.scalar(select(sqlfunc.count(MedicalRecord.id))) or 0
        active = await self.db.scalar(
            select(sqlfunc.count(MedicalRecord.id)).where(MedicalRecord.is_resolved == False)  # noqa: E712
        ) or 0

        return {
            "hospitals": len(hospitals_list),
            "total_beds": total_beds,
            "occupied_beds": occupied,
            "occupancy_rate": occupied / total_beds if total_beds else 0,
            "total_records": total_records,
            "active_conditions": active,
        }

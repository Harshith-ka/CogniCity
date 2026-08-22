"""
Pandemic Simulation Engine: SEIR epidemiological model with infection spreading,
quarantine, hospital capacity, vaccination campaigns, and mortality.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.pandemic import (
    Pandemic, CitizenHealthRecord, HealthStatus,
)

log = structlog.get_logger()


class PandemicEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_pandemic(
        self,
        name: str,
        pathogen: str,
        sim_time: datetime,
        r0: float = 2.5,
        infection_rate: float = 0.03,
        recovery_rate: float = 0.01,
        mortality_rate: float = 0.005,
        incubation_ticks: int = 30,
        symptom_onset_ticks: int = 15,
        hospital_capacity: int = 50,
        initial_infected: int = 5,
    ) -> Pandemic:
        pandemic = Pandemic(
            name=name,
            pathogen=pathogen,
            r0=r0,
            infection_rate=infection_rate,
            recovery_rate=recovery_rate,
            mortality_rate=mortality_rate,
            incubation_ticks=incubation_ticks,
            symptom_onset_ticks=symptom_onset_ticks,
            hospital_capacity=hospital_capacity,
            started_at=sim_time,
        )
        self.db.add(pandemic)
        await self.db.flush()

        citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True).limit(initial_infected)  # noqa: E712
        )
        initial_cases = list(citizens_result.scalars().all())

        for citizen in initial_cases:
            record = CitizenHealthRecord(
                citizen_id=citizen.id,
                pandemic_id=pandemic.id,
                health_status=HealthStatus.INFECTED,
                infected_at=sim_time,
            )
            self.db.add(record)
            pandemic.total_cases += 1
            pandemic.active_cases += 1

        all_citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        all_citizens = list(all_citizens_result.scalars().all())
        infected_ids = {c.id for c in initial_cases}

        for citizen in all_citizens:
            if citizen.id not in infected_ids:
                record = CitizenHealthRecord(
                    citizen_id=citizen.id,
                    pandemic_id=pandemic.id,
                    health_status=HealthStatus.SUSCEPTIBLE,
                )
                self.db.add(record)

        await self.db.flush()
        log.info("pandemic_started", name=name, pathogen=pathogen, r0=r0, initial_infected=len(initial_cases))
        return pandemic

    async def process_tick(self, sim_time: datetime) -> dict:
        result = await self.db.execute(
            select(Pandemic).where(Pandemic.is_active == True)  # noqa: E712
        )
        pandemics = list(result.scalars().all())

        stats = {
            "active_pandemics": len(pandemics),
            "total_cases": 0,
            "active_cases": 0,
            "recovered": 0,
            "deaths": 0,
            "vaccinated": 0,
        }

        for pandemic in pandemics:
            tick_stats = await self._process_pandemic_tick(pandemic, sim_time)
            stats["total_cases"] += pandemic.total_cases
            stats["active_cases"] += pandemic.active_cases
            stats["recovered"] += pandemic.recovered
            stats["deaths"] += pandemic.deaths
            stats["vaccinated"] += pandemic.vaccinated

            if pandemic.active_cases == 0 and pandemic.total_cases > 0:
                pandemic.is_active = False
                pandemic.ended_at = sim_time
                log.info("pandemic_ended", name=pandemic.name, total_cases=pandemic.total_cases, deaths=pandemic.deaths)

        await self.db.flush()
        return stats

    async def _process_pandemic_tick(self, pandemic: Pandemic, sim_time: datetime) -> dict:
        records_result = await self.db.execute(
            select(CitizenHealthRecord).where(
                CitizenHealthRecord.pandemic_id == pandemic.id
            )
        )
        records = list(records_result.scalars().all())

        records_by_status: dict[HealthStatus, list[CitizenHealthRecord]] = {}
        for r in records:
            records_by_status.setdefault(r.health_status, []).append(r)

        susceptible = records_by_status.get(HealthStatus.SUSCEPTIBLE, [])
        exposed = records_by_status.get(HealthStatus.EXPOSED, [])
        infected = records_by_status.get(HealthStatus.INFECTED, [])
        symptomatic = records_by_status.get(HealthStatus.SYMPTOMATIC, [])
        hospitalized = records_by_status.get(HealthStatus.HOSPITALIZED, [])

        infectious_count = len(infected) + len(symptomatic) + len(hospitalized)
        total_pop = len(records)
        if total_pop == 0:
            return {}

        lockdown_factor = 0.3 if pandemic.lockdown_active else 1.0
        mask_factor = 0.6 if pandemic.mask_mandate else 1.0
        effective_rate = pandemic.infection_rate * lockdown_factor * mask_factor

        new_exposures = 0
        if susceptible and infectious_count > 0:
            force_of_infection = effective_rate * pandemic.r0 * (infectious_count / total_pop)
            for record in susceptible:
                if random.random() < force_of_infection:
                    record.health_status = HealthStatus.EXPOSED
                    record.infected_at = sim_time
                    record.ticks_since_infection = 0
                    new_exposures += 1

        for record in exposed:
            record.ticks_since_infection += 1
            if record.ticks_since_infection >= pandemic.incubation_ticks:
                record.health_status = HealthStatus.INFECTED
                pandemic.total_cases += 1
                pandemic.active_cases += 1

        for record in infected:
            record.ticks_since_infection += 1
            if record.ticks_since_infection >= pandemic.incubation_ticks + pandemic.symptom_onset_ticks:
                record.health_status = HealthStatus.SYMPTOMATIC

                citizen_result = await self.db.execute(
                    select(Citizen).where(Citizen.id == record.citizen_id)
                )
                citizen = citizen_result.scalar_one_or_none()
                if citizen:
                    citizen.health = max(0.0, citizen.health - 0.05)
                    citizen.energy = max(0.0, citizen.energy - 0.1)

        for record in symptomatic:
            record.ticks_since_infection += 1

            citizen_result = await self.db.execute(
                select(Citizen).where(Citizen.id == record.citizen_id)
            )
            citizen = citizen_result.scalar_one_or_none()
            if not citizen:
                continue

            citizen.health = max(0.0, citizen.health - 0.02)
            citizen.stress = min(1.0, citizen.stress + 0.03)

            needs_hospital = citizen.health < 0.4 and not record.is_quarantined
            if needs_hospital and pandemic.hospitalized < pandemic.hospital_capacity:
                record.health_status = HealthStatus.HOSPITALIZED
                record.is_quarantined = True
                pandemic.hospitalized += 1
            elif needs_hospital:
                citizen.health = max(0.0, citizen.health - 0.05)

            if random.random() < pandemic.recovery_rate:
                record.health_status = HealthStatus.RECOVERED
                record.recovered_at = sim_time
                record.is_quarantined = False
                pandemic.active_cases = max(0, pandemic.active_cases - 1)
                pandemic.recovered += 1
                citizen.health = min(1.0, citizen.health + 0.1)

            if random.random() < pandemic.mortality_rate:
                hospital_mortality = pandemic.mortality_rate * 0.5 if record.health_status == HealthStatus.HOSPITALIZED else pandemic.mortality_rate
                if random.random() < hospital_mortality or citizen.health <= 0.1:
                    record.health_status = HealthStatus.DECEASED
                    record.is_quarantined = False
                    citizen.is_alive = False
                    citizen.health = 0.0
                    pandemic.deaths += 1
                    pandemic.active_cases = max(0, pandemic.active_cases - 1)
                    if record in hospitalized:
                        pandemic.hospitalized = max(0, pandemic.hospitalized - 1)

        for record in hospitalized:
            record.ticks_since_infection += 1

            citizen_result = await self.db.execute(
                select(Citizen).where(Citizen.id == record.citizen_id)
            )
            citizen = citizen_result.scalar_one_or_none()
            if not citizen:
                continue

            if random.random() < pandemic.recovery_rate * 1.5:
                record.health_status = HealthStatus.RECOVERED
                record.recovered_at = sim_time
                record.is_quarantined = False
                pandemic.active_cases = max(0, pandemic.active_cases - 1)
                pandemic.recovered += 1
                pandemic.hospitalized = max(0, pandemic.hospitalized - 1)
                citizen.health = min(1.0, citizen.health + 0.15)
            elif random.random() < pandemic.mortality_rate * 0.3:
                record.health_status = HealthStatus.DECEASED
                citizen.is_alive = False
                citizen.health = 0.0
                pandemic.deaths += 1
                pandemic.active_cases = max(0, pandemic.active_cases - 1)
                pandemic.hospitalized = max(0, pandemic.hospitalized - 1)

        if pandemic.vaccination_available:
            susceptible_remaining = [
                r for r in records
                if r.health_status == HealthStatus.SUSCEPTIBLE and not r.is_vaccinated
            ]
            vaccines_this_tick = int(len(susceptible_remaining) * pandemic.vaccination_rate)
            for record in random.sample(susceptible_remaining, min(vaccines_this_tick, len(susceptible_remaining))):
                record.health_status = HealthStatus.VACCINATED
                record.is_vaccinated = True
                pandemic.vaccinated += 1

        return {
            "new_exposures": new_exposures,
            "active": pandemic.active_cases,
            "recovered": pandemic.recovered,
            "deaths": pandemic.deaths,
        }

    async def toggle_lockdown(self, pandemic_id: str, active: bool) -> None:
        result = await self.db.execute(
            select(Pandemic).where(Pandemic.id == pandemic_id)
        )
        pandemic = result.scalar_one_or_none()
        if pandemic:
            pandemic.lockdown_active = active
            log.info("lockdown_toggled", pandemic=pandemic.name, active=active)

    async def toggle_mask_mandate(self, pandemic_id: str, active: bool) -> None:
        result = await self.db.execute(
            select(Pandemic).where(Pandemic.id == pandemic_id)
        )
        pandemic = result.scalar_one_or_none()
        if pandemic:
            pandemic.mask_mandate = active
            log.info("mask_mandate_toggled", pandemic=pandemic.name, active=active)

    async def start_vaccination(self, pandemic_id: str, rate: float = 0.02) -> None:
        result = await self.db.execute(
            select(Pandemic).where(Pandemic.id == pandemic_id)
        )
        pandemic = result.scalar_one_or_none()
        if pandemic:
            pandemic.vaccination_available = True
            pandemic.vaccination_rate = rate
            log.info("vaccination_started", pandemic=pandemic.name, rate=rate)

    async def get_pandemic_stats(self) -> list[dict]:
        result = await self.db.execute(select(Pandemic))
        pandemics = list(result.scalars().all())
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "pathogen": p.pathogen,
                "r0": p.r0,
                "total_cases": p.total_cases,
                "active_cases": p.active_cases,
                "recovered": p.recovered,
                "deaths": p.deaths,
                "vaccinated": p.vaccinated,
                "hospitalized": p.hospitalized,
                "hospital_capacity": p.hospital_capacity,
                "lockdown_active": p.lockdown_active,
                "mask_mandate": p.mask_mandate,
                "vaccination_available": p.vaccination_available,
                "is_active": p.is_active,
                "mortality_rate_pct": round(
                    (p.deaths / max(p.total_cases, 1)) * 100, 2
                ),
            }
            for p in pandemics
        ]

    async def get_health_records(self, pandemic_id: str) -> dict:
        result = await self.db.execute(
            select(
                CitizenHealthRecord.health_status,
                func.count(CitizenHealthRecord.id),
            )
            .where(CitizenHealthRecord.pandemic_id == pandemic_id)
            .group_by(CitizenHealthRecord.health_status)
        )
        breakdown = {row[0].value: row[1] for row in result.all()}
        return breakdown

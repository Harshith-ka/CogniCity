"""
Economy Engine: Manages businesses, employment, taxes, and market dynamics.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.economy import Business, BusinessType, Employment, Transaction, TransactionType

log = structlog.get_logger()


class EconomyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tax_rate = 0.15
        self.inflation_rate = 0.02

    async def process_salaries(self, sim_time: datetime) -> int:
        """Pay salaries to all employed citizens (called once per sim day)."""
        result = await self.db.execute(
            select(Employment).where(Employment.is_active == True)  # noqa: E712
        )
        employments = list(result.scalars().all())
        paid = 0

        for emp in employments:
            citizen_result = await self.db.execute(
                select(Citizen).where(Citizen.id == emp.citizen_id)
            )
            citizen = citizen_result.scalar_one_or_none()
            if not citizen:
                continue

            business_result = await self.db.execute(
                select(Business).where(Business.id == emp.business_id)
            )
            business = business_result.scalar_one_or_none()
            if not business:
                continue

            daily_salary = emp.salary / 30.0
            tax = daily_salary * self.tax_rate
            net_salary = daily_salary - tax

            citizen.balance += net_salary
            citizen.salary = emp.salary
            business.balance -= daily_salary
            business.expenses += daily_salary

            tx = Transaction(
                citizen_id=citizen.id,
                transaction_type=TransactionType.SALARY,
                amount=net_salary,
                description=f"Daily salary from {business.name}",
                business_id=business.id,
                sim_timestamp=sim_time,
            )
            self.db.add(tx)

            tax_tx = Transaction(
                citizen_id=citizen.id,
                transaction_type=TransactionType.TAX,
                amount=tax,
                description="Income tax",
                sim_timestamp=sim_time,
            )
            self.db.add(tax_tx)
            paid += 1

        await self.db.flush()
        return paid

    async def hire_citizen(
        self,
        citizen_id: uuid.UUID,
        business_id: uuid.UUID,
        role: str,
        salary: float,
    ) -> Employment | None:
        business_result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = business_result.scalar_one_or_none()
        if not business:
            return None

        employee_count_result = await self.db.execute(
            select(Employment).where(
                Employment.business_id == business_id,
                Employment.is_active == True,  # noqa: E712
            )
        )
        current_employees = len(list(employee_count_result.scalars().all()))
        if current_employees >= business.max_employees:
            return None

        employment = Employment(
            citizen_id=citizen_id,
            business_id=business_id,
            role=role,
            salary=salary,
        )
        self.db.add(employment)

        citizen_result = await self.db.execute(
            select(Citizen).where(Citizen.id == citizen_id)
        )
        citizen = citizen_result.scalar_one_or_none()
        if citizen:
            citizen.occupation = role
            citizen.salary = salary

        await self.db.flush()
        log.info("citizen_hired", citizen_id=str(citizen_id), business=business.name, role=role)
        return employment

    async def fire_citizen(self, employment_id: uuid.UUID, sim_time: datetime) -> None:
        result = await self.db.execute(
            select(Employment).where(Employment.id == employment_id)
        )
        emp = result.scalar_one_or_none()
        if not emp:
            return

        emp.is_active = False
        emp.ended_at = sim_time

        citizen_result = await self.db.execute(
            select(Citizen).where(Citizen.id == emp.citizen_id)
        )
        citizen = citizen_result.scalar_one_or_none()
        if citizen:
            citizen.occupation = "unemployed"
            citizen.salary = 0.0
            citizen.stress = min(1.0, citizen.stress + 0.3)

        await self.db.flush()

    async def process_business_revenue(self, sim_time: datetime) -> None:
        """Businesses earn from customer transactions."""
        result = await self.db.execute(
            select(Business).where(Business.is_open == True)  # noqa: E712
        )
        businesses = list(result.scalars().all())

        for biz in businesses:
            employee_result = await self.db.execute(
                select(Employment).where(
                    Employment.business_id == biz.id,
                    Employment.is_active == True,  # noqa: E712
                )
            )
            employee_count = len(list(employee_result.scalars().all()))

            daily_revenue = employee_count * biz.base_salary * 0.5 * biz.price_multiplier
            biz.revenue += daily_revenue
            biz.balance += daily_revenue

            if biz.balance < 0 and biz.balance < -biz.base_salary * 3:
                biz.is_open = False
                log.info("business_closed", business=biz.name)

        await self.db.flush()

    async def get_economy_stats(self) -> dict:
        citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        citizens = list(citizens_result.scalars().all())

        businesses_result = await self.db.execute(select(Business))
        businesses = list(businesses_result.scalars().all())

        total_wealth = sum(c.balance for c in citizens)
        avg_salary = sum(c.salary for c in citizens) / len(citizens) if citizens else 0

        return {
            "total_wealth": total_wealth,
            "avg_salary": avg_salary,
            "total_businesses": len(businesses),
            "active_businesses": sum(1 for b in businesses if b.is_open),
            "total_revenue": sum(b.revenue for b in businesses),
            "tax_rate": self.tax_rate,
            "inflation_rate": self.inflation_rate,
        }

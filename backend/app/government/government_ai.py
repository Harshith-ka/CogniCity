"""
Government AI: Autonomous departments that monitor city metrics,
make policy decisions, allocate budgets, and respond to emergencies.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.economy import Business
from backend.app.models.event import CityEvent
from backend.app.models.government import Department, DepartmentType, Policy

log = structlog.get_logger()


class PolicyDecision:
    def __init__(
        self,
        department: DepartmentType,
        action: str,
        description: str,
        budget_impact: float = 0.0,
        parameters: dict | None = None,
    ):
        self.department = department
        self.action = action
        self.description = description
        self.budget_impact = budget_impact
        self.parameters = parameters or {}


class DepartmentAI:
    """Base class for autonomous government department decision-making."""

    def __init__(self, department: Department, db: AsyncSession):
        self.department = department
        self.db = db

    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        raise NotImplementedError


class PoliceAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        crime_rate = metrics.get("crime_rate", 0.0)
        stress_avg = metrics.get("avg_stress", 0.0)
        unemployment = metrics.get("unemployment_rate", 0.0)

        if stress_avg > 0.6:
            decisions.append(PolicyDecision(
                DepartmentType.POLICE,
                "increase_patrols",
                "Increasing police patrols due to high citizen stress levels.",
                budget_impact=-5000.0,
                parameters={"patrol_increase": 0.2},
            ))

        if unemployment > 0.3:
            decisions.append(PolicyDecision(
                DepartmentType.POLICE,
                "community_outreach",
                "Launching community outreach programs to reduce crime risk from unemployment.",
                budget_impact=-3000.0,
                parameters={"outreach_programs": 2},
            ))

        return decisions


class HealthcareAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        avg_health = metrics.get("avg_health", 1.0)
        population = metrics.get("population", 0)

        if avg_health < 0.6:
            decisions.append(PolicyDecision(
                DepartmentType.HEALTHCARE,
                "expand_hospitals",
                "Expanding hospital capacity due to declining public health.",
                budget_impact=-20000.0,
                parameters={"capacity_increase": 50},
            ))

        if avg_health < 0.4:
            decisions.append(PolicyDecision(
                DepartmentType.HEALTHCARE,
                "free_checkups",
                "Offering free health checkups to address health crisis.",
                budget_impact=-10000.0,
                parameters={"coverage": "all_citizens"},
            ))

        if population > 500 and avg_health > 0.8:
            decisions.append(PolicyDecision(
                DepartmentType.HEALTHCARE,
                "preventive_care",
                "Investing in preventive care programs.",
                budget_impact=-5000.0,
                parameters={"programs": ["vaccination", "screening"]},
            ))

        return decisions


class TransportAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        avg_congestion = metrics.get("avg_congestion", 0.0)
        population = metrics.get("population", 0)

        if avg_congestion > 0.6:
            decisions.append(PolicyDecision(
                DepartmentType.TRANSPORT,
                "expand_transit",
                "Adding more bus and metro routes to reduce congestion.",
                budget_impact=-15000.0,
                parameters={"new_routes": 3, "frequency_increase": 0.2},
            ))

        if population > 200:
            decisions.append(PolicyDecision(
                DepartmentType.TRANSPORT,
                "bike_infrastructure",
                "Building new bike lanes to encourage cycling.",
                budget_impact=-8000.0,
                parameters={"new_bike_lanes_km": 5},
            ))

        return decisions


class TreasuryAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        unemployment = metrics.get("unemployment_rate", 0.0)
        total_gdp = metrics.get("total_gdp", 0.0)
        avg_happiness = metrics.get("avg_happiness", 0.5)

        if unemployment > 0.25:
            decisions.append(PolicyDecision(
                DepartmentType.TREASURY,
                "reduce_taxes",
                "Temporarily reducing taxes to stimulate economic growth.",
                budget_impact=-10000.0,
                parameters={"tax_reduction": 0.03},
            ))

        if unemployment < 0.05 and avg_happiness > 0.7:
            decisions.append(PolicyDecision(
                DepartmentType.TREASURY,
                "increase_taxes",
                "Raising taxes slightly to fund infrastructure improvements.",
                budget_impact=15000.0,
                parameters={"tax_increase": 0.02},
            ))

        if total_gdp > 1000000:
            decisions.append(PolicyDecision(
                DepartmentType.TREASURY,
                "invest_infrastructure",
                "Allocating surplus funds to infrastructure development.",
                budget_impact=-30000.0,
                parameters={"infrastructure_fund": 30000.0},
            ))

        return decisions


class EducationAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        population = metrics.get("population", 0)
        avg_happiness = metrics.get("avg_happiness", 0.5)
        unemployment = metrics.get("unemployment_rate", 0.0)

        if unemployment > 0.2:
            decisions.append(PolicyDecision(
                DepartmentType.EDUCATION,
                "job_training",
                "Launching job training programs to reduce unemployment.",
                budget_impact=-12000.0,
                parameters={"programs": ["tech_skills", "trade_skills", "entrepreneurship"]},
            ))

        if population > 100:
            decisions.append(PolicyDecision(
                DepartmentType.EDUCATION,
                "expand_schools",
                "Building new schools to accommodate growing population.",
                budget_impact=-25000.0,
                parameters={"new_schools": 1},
            ))

        return decisions


class MayorAI(DepartmentAI):
    async def assess_situation(self, metrics: dict) -> list[PolicyDecision]:
        decisions = []
        avg_happiness = metrics.get("avg_happiness", 0.5)
        avg_stress = metrics.get("avg_stress", 0.5)
        active_events = metrics.get("active_events", 0)

        if avg_happiness < 0.4:
            decisions.append(PolicyDecision(
                DepartmentType.MAYOR,
                "public_festival",
                "Organizing a city festival to boost citizen happiness.",
                budget_impact=-10000.0,
                parameters={"festival_type": "community_celebration", "duration_days": 3},
            ))

        if active_events > 2:
            decisions.append(PolicyDecision(
                DepartmentType.MAYOR,
                "emergency_coordination",
                "Coordinating emergency response across departments.",
                budget_impact=-5000.0,
                parameters={"priority": "high", "departments_involved": "all"},
            ))

        if avg_stress > 0.7:
            decisions.append(PolicyDecision(
                DepartmentType.MAYOR,
                "stress_relief",
                "Implementing city-wide stress relief initiatives.",
                budget_impact=-8000.0,
                parameters={"initiatives": ["park_improvements", "free_events", "mental_health"]},
            ))

        return decisions


DEPARTMENT_AI_MAP = {
    DepartmentType.POLICE: PoliceAI,
    DepartmentType.HEALTHCARE: HealthcareAI,
    DepartmentType.TRANSPORT: TransportAI,
    DepartmentType.TREASURY: TreasuryAI,
    DepartmentType.EDUCATION: EducationAI,
    DepartmentType.MAYOR: MayorAI,
}


EMERGENCY_RESPONSE_MAP = {
    "natural_disaster": [
        (DepartmentType.FIRE, "deploy_emergency_crews", "Deploying fire and rescue crews to the affected area.", -8000.0),
        (DepartmentType.POLICE, "coordinate_evacuation", "Coordinating evacuation and crowd control near the disaster site.", -4000.0),
    ],
    "health": [
        (DepartmentType.HEALTHCARE, "activate_emergency_response", "Activating emergency medical response and surge capacity.", -12000.0),
    ],
    "infrastructure": [
        (DepartmentType.POWER, "dispatch_repair_crews", "Dispatching repair crews to restore affected infrastructure.", -6000.0),
    ],
    "economic": [
        (DepartmentType.TREASURY, "economic_stabilization", "Releasing emergency funds to stabilize the local economy.", -15000.0),
    ],
    "social": [
        (DepartmentType.POLICE, "increase_patrols", "Increasing police presence in response to social unrest.", -5000.0),
    ],
    "political": [
        (DepartmentType.MAYOR, "public_statement", "Issuing a public statement to address citizen concerns.", -1000.0),
    ],
}

EMERGENCY_EFFECTS = {
    "deploy_emergency_crews": {"stress": -0.05, "health": 0.03},
    "coordinate_evacuation": {"stress": -0.03},
    "activate_emergency_response": {"health": 0.06, "stress": -0.02},
    "dispatch_repair_crews": {"stress": -0.03, "happiness": 0.02},
    "economic_stabilization": {"stress": -0.02, "happiness": 0.03},
    "increase_patrols": {"stress": -0.02},
    "public_statement": {"stress": -0.01, "happiness": 0.01},
    "emergency_coordination": {"stress": -0.02, "happiness": 0.02},
}


class GovernmentAI:
    """Top-level government AI that coordinates all departments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.decision_history: list[dict] = []

    async def emergency_response(
        self,
        event_name: str,
        category: str,
        severity: str,
        sim_time: datetime,
    ) -> list[dict]:
        """Immediate government reaction to a just-triggered disaster/event/pandemic,
        independent of the scheduled daily cycle. Always issues a mayoral response plus
        any category-specific department action, and applies a small immediate relief
        effect to citizens so the reaction is visible right away."""
        result = await self.db.execute(select(Department))
        departments = {d.department_type: d for d in result.scalars().all()}

        actions = [
            (DepartmentType.MAYOR, "emergency_coordination",
             f"Coordinating city response to {event_name}.", -3000.0),
        ]
        actions.extend(EMERGENCY_RESPONSE_MAP.get(category, []))

        severity_multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}.get(severity, 1.0)

        decisions: list[dict] = []
        for dept_type, action, description, base_cost in actions:
            dept = departments.get(dept_type)
            if not dept:
                continue

            cost = base_cost * severity_multiplier
            if dept.budget + cost < 0:
                log.info("emergency_response_rejected_budget", department=dept_type.value, action=action)
                continue

            dept.budget += cost
            policy = Policy(
                name=action.replace("_", " ").title(),
                description=description,
                department=dept_type,
                parameters={"trigger_event": event_name, "severity": severity},
                enacted_at=sim_time,
            )
            self.db.add(policy)

            decision_record = {
                "department": dept_type.value,
                "action": action,
                "description": description,
                "budget_impact": cost,
                "remaining_budget": dept.budget,
                "parameters": {"trigger_event": event_name, "severity": severity},
                "sim_time": sim_time.isoformat(),
            }
            decisions.append(decision_record)

            log.info("emergency_response", department=dept_type.value, action=action, event_name=event_name)

        await self._apply_emergency_effects(decisions)
        await self.db.flush()

        self.decision_history.extend(decisions)
        if len(self.decision_history) > 500:
            self.decision_history = self.decision_history[-250:]

        return decisions

    async def _apply_emergency_effects(self, decisions: list[dict]) -> None:
        if not decisions:
            return
        result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True).limit(200)  # noqa: E712
        )
        citizens = list(result.scalars().all())
        if not citizens:
            return

        combined = {"stress": 0.0, "health": 0.0, "happiness": 0.0}
        for decision in decisions:
            effect = EMERGENCY_EFFECTS.get(decision["action"], {})
            for key, val in effect.items():
                combined[key] = combined.get(key, 0.0) + val

        for c in citizens:
            c.stress = max(0.0, min(1.0, c.stress + combined["stress"]))
            c.health = max(0.0, min(1.0, c.health + combined["health"]))
            c.happiness = max(0.0, min(1.0, c.happiness + combined["happiness"]))

    async def run_government_cycle(self, metrics: dict, sim_time: datetime) -> list[dict]:
        """Run a decision cycle for all government departments."""
        result = await self.db.execute(select(Department))
        departments = list(result.scalars().all())

        all_decisions: list[dict] = []

        for dept in departments:
            ai_class = DEPARTMENT_AI_MAP.get(dept.department_type)
            if not ai_class:
                continue

            ai = ai_class(dept, self.db)
            decisions = await ai.assess_situation(metrics)

            for decision in decisions:
                if dept.budget + decision.budget_impact < 0:
                    log.info(
                        "decision_rejected_budget",
                        department=dept.department_type.value,
                        action=decision.action,
                    )
                    continue

                dept.budget += decision.budget_impact

                policy = Policy(
                    name=decision.action.replace("_", " ").title(),
                    description=decision.description,
                    department=decision.department,
                    parameters=decision.parameters,
                    enacted_at=sim_time,
                )
                self.db.add(policy)

                decision_record = {
                    "department": dept.department_type.value,
                    "action": decision.action,
                    "description": decision.description,
                    "budget_impact": decision.budget_impact,
                    "remaining_budget": dept.budget,
                    "parameters": decision.parameters,
                    "sim_time": sim_time.isoformat(),
                }
                all_decisions.append(decision_record)

                log.info(
                    "government_decision",
                    department=dept.department_type.value,
                    action=decision.action,
                    budget_impact=decision.budget_impact,
                )

        await self._apply_policy_effects(all_decisions, metrics)
        await self.db.flush()

        self.decision_history.extend(all_decisions)
        if len(self.decision_history) > 500:
            self.decision_history = self.decision_history[-250:]

        return all_decisions

    async def _apply_policy_effects(self, decisions: list[dict], metrics: dict) -> None:
        """Apply the effects of government decisions to the city."""
        for decision in decisions:
            action = decision["action"]
            params = decision.get("parameters", {})

            if action == "reduce_taxes":
                reduction = params.get("tax_reduction", 0.02)
                result = await self.db.execute(
                    select(Citizen).where(Citizen.is_alive == True).limit(200)  # noqa: E712
                )
                citizens = list(result.scalars().all())
                for c in citizens:
                    c.happiness = min(1.0, c.happiness + 0.02)
                    c.stress = max(0.0, c.stress - 0.01)

            elif action == "public_festival":
                result = await self.db.execute(
                    select(Citizen).where(Citizen.is_alive == True).limit(200)  # noqa: E712
                )
                citizens = list(result.scalars().all())
                for c in citizens:
                    c.happiness = min(1.0, c.happiness + 0.05)
                    c.stress = max(0.0, c.stress - 0.03)
                    c.social_need = max(0.0, c.social_need - 0.1)

            elif action == "free_checkups":
                result = await self.db.execute(
                    select(Citizen).where(
                        Citizen.is_alive == True,  # noqa: E712
                        Citizen.health < 0.6,
                    ).limit(100)
                )
                citizens = list(result.scalars().all())
                for c in citizens:
                    c.health = min(1.0, c.health + 0.1)

            elif action == "job_training":
                result = await self.db.execute(
                    select(Citizen).where(
                        Citizen.is_alive == True,  # noqa: E712
                        Citizen.occupation == "unemployed",
                    ).limit(20)
                )
                unemployed = list(result.scalars().all())
                for c in unemployed[:5]:
                    c.stress = max(0.0, c.stress - 0.05)

    async def get_all_policies(self, active_only: bool = True) -> list[dict]:
        query = select(Policy)
        if active_only:
            query = query.where(Policy.is_active == True)  # noqa: E712
        query = query.order_by(Policy.enacted_at.desc()).limit(50)

        result = await self.db.execute(query)
        policies = list(result.scalars().all())
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "department": p.department.value,
                "parameters": p.parameters,
                "is_active": p.is_active,
                "approval_rating": p.approval_rating,
                "enacted_at": p.enacted_at.isoformat(),
            }
            for p in policies
        ]

    async def get_department_budgets(self) -> list[dict]:
        result = await self.db.execute(select(Department))
        departments = list(result.scalars().all())
        return [
            {
                "department": d.department_type.value,
                "name": d.name,
                "budget": round(d.budget, 2),
                "efficiency": d.efficiency,
                "employees": d.employee_count,
            }
            for d in departments
        ]

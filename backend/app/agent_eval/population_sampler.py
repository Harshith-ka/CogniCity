"""Population Sampler: Read-only in-memory snapshotting and adversarial cohort generation."""

from __future__ import annotations

import random
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.models.citizen import Citizen
from backend.app.models.city import District
from backend.app.agent_eval.models import (
    CitizenProfileDTO,
    CohortDistribution,
)

OCCUPATIONS = [
    "Software Engineer", "Nurse", "Retail Associate", "Teacher", "Doctor",
    "Accountant", "Electrician", "Chef", "Civil Engineer", "Student",
    "Delivery Driver", "Marketing Manager", "Banker", "Artist", "Retired"
]

EDUCATIONS = [
    "High School", "Bachelor's Degree", "Master's Degree", "Doctorate", "Vocational Diploma"
]

CHRONIC_CONDITIONS = [
    "Hypertension", "Type 2 Diabetes", "Asthma", "Cardiovascular History", "Arthritis", "None"
]


class PopulationSampler:
    """Clones citizen profiles in-memory for zero-leakage sandbox evaluation."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def sample_cohort(
        self,
        cohort_type: CohortDistribution,
        sample_size: int = 500,
        adversarial_intensity: float = 0.2,
    ) -> list[CitizenProfileDTO]:
        """Fetches from database as baseline, then adapts or scales into the requested cohort."""
        baseline_citizens: list[CitizenProfileDTO] = []

        if self.db:
            try:
                result = await self.db.execute(
                    select(Citizen)
                    .options(joinedload(Citizen.home_location), joinedload(Citizen.workplace))
                    .limit(min(sample_size, 2000))
                )
                db_citizens = result.unique().scalars().all()
                for c in db_citizens:
                    baseline_citizens.append(self._db_to_dto(c))
            except Exception:
                baseline_citizens = []

        # If sample_size > DB size or DB is empty, synthetically expand
        cohort: list[CitizenProfileDTO] = []
        for i in range(sample_size):
            if i < len(baseline_citizens):
                dto = baseline_citizens[i].model_copy(deep=True)
            else:
                dto = self._generate_synthetic_citizen(i)

            # Apply cohort distribution modifiers
            dto = self._apply_cohort_mod(dto, cohort_type, adversarial_intensity)
            cohort.append(dto)

        return cohort

    def _db_to_dto(self, c: Citizen) -> CitizenProfileDTO:
        income = float(getattr(c, "income", 600000.0) or 600000.0)
        savings = float(getattr(c, "savings", 150000.0) or 150000.0)
        age = int(getattr(c, "age", 35) or 35)
        health = float(getattr(c, "health", 0.85) or 0.85)
        happiness = float(getattr(c, "happiness", 0.70) or 0.70)
        stress = float(getattr(c, "stress_level", 0.35) or 0.35)
        
        return CitizenProfileDTO(
            id=str(c.id),
            name=c.name or f"Citizen {c.id}",
            age=age,
            gender=getattr(c, "gender", "unspecified") or "unspecified",
            occupation=getattr(c, "occupation", "Professional") or "Professional",
            education=random.choice(EDUCATIONS),
            district="Metro District",
            annual_income=income,
            savings=savings,
            monthly_expenses=income * 0.55 / 12,
            credit_score_estimate=int(580 + (savings / max(1.0, income)) * 200),
            health_index=health,
            stress_level=stress,
            happiness=happiness,
            tech_savviness="moderate" if age > 45 else "high",
            chronic_conditions=[random.choice(CHRONIC_CONDITIONS)] if health < 0.7 else [],
            recent_activity=getattr(c, "current_activity", "work") or "work",
        )

    def _generate_synthetic_citizen(self, index: int) -> CitizenProfileDTO:
        age = random.randint(18, 78)
        income = random.choice([350000, 550000, 850000, 1400000, 2400000, 4200000])
        savings = income * random.uniform(0.1, 1.8)
        health = max(0.2, min(1.0, 1.0 - (age / 100) * random.uniform(0.3, 0.7)))
        stress = random.uniform(0.15, 0.85)
        
        return CitizenProfileDTO(
            id=f"syn_{uuid.uuid4().hex[:8]}",
            name=f"Synthetic Citizen #{index + 1}",
            age=age,
            gender=random.choice(["female", "male", "non-binary"]),
            occupation=random.choice(OCCUPATIONS),
            education=random.choice(EDUCATIONS),
            district=random.choice(["Downtown Central", "Tech Corridor", "Residential North", "Industrial South"]),
            annual_income=float(income),
            savings=float(savings),
            monthly_expenses=income * random.uniform(0.4, 0.75) / 12,
            credit_score_estimate=random.randint(550, 820),
            health_index=round(health, 2),
            stress_level=round(stress, 2),
            happiness=round(random.uniform(0.3, 0.95), 2),
            tech_savviness="expert" if age < 35 else ("high" if age < 55 else "basic"),
            chronic_conditions=[random.choice(CHRONIC_CONDITIONS)] if health < 0.65 else [],
        )

    def _apply_cohort_mod(
        self,
        dto: CitizenProfileDTO,
        cohort: CohortDistribution,
        intensity: float,
    ) -> CitizenProfileDTO:
        if cohort == CohortDistribution.SENIOR_POPULATION:
            dto.age = random.randint(62, 85)
            dto.tech_savviness = random.choice(["basic", "moderate"])
            dto.chronic_conditions = [random.choice(["Hypertension", "Cardiovascular History", "Arthritis"])]
            dto.health_index = max(0.3, dto.health_index - 0.25)

        elif cohort == CohortDistribution.LOW_INCOME_HIGH_DEBT:
            dto.annual_income = random.uniform(180000, 420000)
            dto.savings = random.uniform(5000, 40000)
            dto.credit_score_estimate = random.randint(480, 620)
            dto.stress_level = min(0.95, dto.stress_level + 0.35)

        elif cohort == CohortDistribution.HIGH_STRESS_CHRONIC:
            dto.stress_level = random.uniform(0.75, 0.98)
            dto.chronic_conditions = ["Hypertension", "Type 2 Diabetes"]
            dto.health_index = random.uniform(0.35, 0.6)

        elif cohort == CohortDistribution.ADVERSARIAL_EDGE_CASES:
            # Inject extreme combinations (e.g. 74yo low income + extreme debt + high tech savviness)
            if random.random() < intensity:
                dto.age = random.choice([19, 82, 91])
                dto.annual_income = random.choice([50000, 15000000])  # Extreme ends
                dto.savings = random.choice([0, 50000000])
                dto.stress_level = random.choice([0.05, 0.99])
                dto.credit_score_estimate = random.choice([350, 850])

        return dto

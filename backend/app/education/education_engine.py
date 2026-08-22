"""
Education & Skills Engine: Citizens enroll in schools, gain skills over time,
graduate, and unlock better jobs. Skill proficiency grows based on school
quality, citizen personality (conscientiousness), and time invested.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.education import School, Enrollment, CitizenSkill
from backend.app.models.citizen import Citizen

log = structlog.get_logger()

PROGRAM_SKILLS = {
    "engineering":   ["programming", "mathematics", "problem_solving", "systems_design"],
    "medicine":      ["biology", "patient_care", "diagnostics", "research"],
    "business":      ["management", "finance", "marketing", "negotiation"],
    "arts":          ["creativity", "communication", "design", "writing"],
    "law":           ["legal_analysis", "public_speaking", "research", "negotiation"],
    "technology":    ["programming", "data_analysis", "cybersecurity", "networking"],
    "education":     ["teaching", "communication", "patience", "research"],
    "trades":        ["mechanical", "electrical", "construction", "safety"],
    "general":       ["critical_thinking", "communication", "mathematics", "writing"],
}

OCCUPATION_FROM_PROGRAM = {
    "engineering": ["software engineer", "civil engineer", "mechanical engineer"],
    "medicine": ["doctor", "nurse", "pharmacist"],
    "business": ["manager", "accountant", "marketing specialist"],
    "arts": ["designer", "writer", "artist"],
    "law": ["lawyer", "paralegal"],
    "technology": ["data analyst", "IT specialist", "developer"],
    "education": ["teacher", "professor", "tutor"],
    "trades": ["electrician", "plumber", "carpenter"],
}


class EducationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_tick(self, sim_time: datetime, citizens: list) -> dict:
        new_enrollments = 0
        graduations = 0
        skills_gained = 0

        new_enrollments += await self._auto_enroll(citizens, sim_time)
        grad_result = await self._process_progress(sim_time, citizens)
        graduations += grad_result["graduations"]
        skills_gained += grad_result["skills_gained"]

        await self.db.flush()

        total_enrolled = await self.db.scalar(
            select(sqlfunc.count(Enrollment.id)).where(Enrollment.is_active == True)  # noqa: E712
        ) or 0

        return {
            "new_enrollments": new_enrollments,
            "graduations": graduations,
            "skills_gained": skills_gained,
            "total_enrolled": total_enrolled,
        }

    async def _auto_enroll(self, citizens: list, sim_time: datetime) -> int:
        enrolled = 0

        for citizen in citizens:
            if random.random() > 0.003:
                continue

            existing = await self.db.execute(
                select(Enrollment).where(
                    Enrollment.citizen_id == citizen.id,
                    Enrollment.is_active == True,  # noqa: E712
                ).limit(1)
            )
            if existing.scalar_one_or_none():
                continue

            openness = citizen.personality_traits.get("openness", 0.5)
            conscientiousness = citizen.personality_traits.get("conscientiousness", 0.5)
            if random.random() > (openness * 0.5 + conscientiousness * 0.5):
                continue

            school = await self._find_school(citizen)
            if not school:
                continue

            if school.enrolled >= school.capacity:
                continue

            program = random.choice(school.programs) if school.programs else "general"

            enrollment = Enrollment(
                citizen_id=citizen.id,
                school_id=school.id,
                program=program,
                gpa=round(2.5 + conscientiousness * 1.5 + random.uniform(-0.5, 0.5), 2),
                enrolled_at=sim_time,
            )
            self.db.add(enrollment)
            school.enrolled += 1
            enrolled += 1

        return enrolled

    async def _find_school(self, citizen) -> School | None:
        from backend.app.models.citizen import EducationLevel
        preferred = {
            EducationLevel.NONE: "high_school",
            EducationLevel.HIGH_SCHOOL: "university",
            EducationLevel.BACHELORS: "university",
        }.get(citizen.education, "vocational")

        result = await self.db.execute(
            select(School).where(
                School.is_operational == True,  # noqa: E712
                School.school_type == preferred,
            ).order_by((School.capacity - School.enrolled).desc()).limit(1)
        )
        school = result.scalar_one_or_none()
        if not school:
            result = await self.db.execute(
                select(School).where(
                    School.is_operational == True  # noqa: E712
                ).order_by((School.capacity - School.enrolled).desc()).limit(1)
            )
            school = result.scalar_one_or_none()
        return school

    async def _process_progress(self, sim_time: datetime, citizens: list) -> dict:
        result = await self.db.execute(
            select(Enrollment).where(Enrollment.is_active == True).limit(50)  # noqa: E712
        )
        enrollments = list(result.scalars().all())
        graduations = 0
        skills_gained = 0

        citizen_map = {c.id: c for c in citizens}

        for enrollment in enrollments:
            citizen = citizen_map.get(enrollment.citizen_id)
            if not citizen:
                continue

            conscientiousness = citizen.personality_traits.get("conscientiousness", 0.5)
            school_result = await self.db.execute(
                select(School).where(School.id == enrollment.school_id).limit(1)
            )
            school = school_result.scalar_one_or_none()
            quality = school.quality_rating if school else 0.5

            progress_rate = 0.01 * (0.5 + conscientiousness * 0.3 + quality * 0.2)
            enrollment.progress = min(1.0, enrollment.progress + progress_rate)

            if enrollment.progress >= 1.0:
                enrollment.is_active = False
                enrollment.is_graduated = True
                enrollment.graduated_at = sim_time
                graduations += 1

                if school:
                    school.enrolled = max(0, school.enrolled - 1)

                program_skills = PROGRAM_SKILLS.get(enrollment.program, PROGRAM_SKILLS["general"])
                for skill_name in program_skills:
                    existing_skill = await self.db.execute(
                        select(CitizenSkill).where(
                            CitizenSkill.citizen_id == citizen.id,
                            CitizenSkill.skill_name == skill_name,
                        ).limit(1)
                    )
                    skill = existing_skill.scalar_one_or_none()
                    if skill:
                        skill.proficiency = min(1.0, skill.proficiency + 0.2 + quality * 0.1)
                    else:
                        skill = CitizenSkill(
                            citizen_id=citizen.id,
                            skill_name=skill_name,
                            proficiency=round(0.3 + quality * 0.2 + random.uniform(0, 0.1), 2),
                            source="school",
                            acquired_at=sim_time,
                        )
                        self.db.add(skill)
                    skills_gained += 1

                enrollment.skills_gained = program_skills

                occupations = OCCUPATION_FROM_PROGRAM.get(enrollment.program, [])
                if occupations and citizen.occupation == "unemployed":
                    citizen.occupation = random.choice(occupations)
                    citizen.salary = round(random.uniform(2000, 6000), 0)
                    citizen.happiness = min(1.0, citizen.happiness + 0.1)

                from backend.app.models.citizen import EducationLevel
                upgrade_map = {
                    EducationLevel.NONE: EducationLevel.HIGH_SCHOOL,
                    EducationLevel.HIGH_SCHOOL: EducationLevel.BACHELORS,
                    EducationLevel.BACHELORS: EducationLevel.MASTERS,
                    EducationLevel.MASTERS: EducationLevel.DOCTORATE,
                }
                new_edu = upgrade_map.get(citizen.education)
                if new_edu:
                    citizen.education = new_edu

        return {"graduations": graduations, "skills_gained": skills_gained}

    async def seed_schools(self, districts: list[dict]) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(School.id)))
        if existing and existing > 0:
            return 0

        count = 0
        school_defs = [
            ("high_school", ["general", "arts", "trades"], 300, 0),
            ("university", ["engineering", "medicine", "business", "law"], 500, 5000),
            ("vocational", ["technology", "trades", "education"], 150, 1000),
            ("online", ["technology", "business", "arts"], 1000, 500),
        ]

        for i, d in enumerate(districts):
            s_type, programs, capacity, tuition = school_defs[i % len(school_defs)]
            school = School(
                name=f"{d['name']} {s_type.replace('_', ' ').title()}",
                school_type=s_type,
                district_id=d.get("id"),
                capacity=capacity,
                teachers=random.randint(10, 40),
                quality_rating=round(random.uniform(0.5, 0.95), 2),
                tuition=tuition,
                programs=programs,
                graduation_rate=round(random.uniform(0.6, 0.95), 2),
            )
            self.db.add(school)
            count += 1
        await self.db.flush()
        return count

    async def get_stats(self) -> dict:
        schools = await self.db.scalar(select(sqlfunc.count(School.id))) or 0
        enrolled = await self.db.scalar(
            select(sqlfunc.count(Enrollment.id)).where(Enrollment.is_active == True)  # noqa: E712
        ) or 0
        graduated = await self.db.scalar(
            select(sqlfunc.count(Enrollment.id)).where(Enrollment.is_graduated == True)  # noqa: E712
        ) or 0
        total_skills = await self.db.scalar(select(sqlfunc.count(CitizenSkill.id))) or 0

        return {
            "schools": schools,
            "active_enrollments": enrolled,
            "total_graduations": graduated,
            "total_skills": total_skills,
        }

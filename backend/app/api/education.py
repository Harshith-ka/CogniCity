"""Phase 5 API: Education endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.education.education_engine import EducationEngine
from backend.app.models.education import School, Enrollment, CitizenSkill

router = APIRouter(prefix="/api/education", tags=["education"])


@router.get("/stats")
async def education_stats(db: AsyncSession = Depends(get_db)):
    engine = EducationEngine(db)
    return await engine.get_stats()


@router.get("/schools")
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School))
    return [{
        "id": str(s.id),
        "name": s.name,
        "type": s.school_type,
        "capacity": s.capacity,
        "enrolled": s.enrolled,
        "teachers": s.teachers,
        "quality_rating": s.quality_rating,
        "tuition": s.tuition,
        "programs": s.programs,
        "graduation_rate": s.graduation_rate,
        "is_operational": s.is_operational,
    } for s in result.scalars().all()]


@router.get("/enrollments")
async def active_enrollments(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Enrollment).where(Enrollment.is_active == True).limit(limit)  # noqa: E712
    )
    return [{
        "id": str(e.id),
        "citizen_id": str(e.citizen_id),
        "school_id": str(e.school_id),
        "program": e.program,
        "progress": e.progress,
        "gpa": e.gpa,
        "is_graduated": e.is_graduated,
    } for e in result.scalars().all()]


@router.get("/skills/{citizen_id}")
async def citizen_skills(citizen_id: str, db: AsyncSession = Depends(get_db)):
    import uuid
    result = await db.execute(
        select(CitizenSkill).where(CitizenSkill.citizen_id == uuid.UUID(citizen_id))
    )
    return [{
        "skill": s.skill_name,
        "proficiency": s.proficiency,
        "source": s.source,
    } for s in result.scalars().all()]

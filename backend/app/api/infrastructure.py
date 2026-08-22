"""Phase 6 API: Infrastructure & Utilities endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.city import District
from backend.app.models.infrastructure import UtilityGrid, InfraProject
from backend.app.infrastructure.infrastructure_engine import InfrastructureEngine, BUILD_PRESETS
from backend.app.infrastructure.config import list_config
from backend.app.infrastructure.impact_strategies import IMPACT_STRATEGIES

router = APIRouter(prefix="/api/infrastructure", tags=["infrastructure"])


class TriggerProjectRequest(BaseModel):
    project_type: str
    district_id: uuid.UUID | None = None
    x: float | None = None
    y: float | None = None
    target_x: float | None = None
    target_y: float | None = None


@router.get("/project-types")
async def list_project_types():
    return [{"type": t, "name": preset["name"]} for t, preset in BUILD_PRESETS.items()]


@router.get("/config")
async def get_infrastructure_config():
    """Single source of truth for Build Mode: icon, cost, service radius, capacity —
    the 3D view's infra drawer is built from this instead of hardcoding it in HTML."""
    return list_config()


@router.post("/trigger")
async def trigger_project(req: TriggerProjectRequest, db: AsyncSession = Depends(get_db)):
    if req.project_type not in BUILD_PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown project_type: {req.project_type}")

    engine = InfrastructureEngine(db)
    project = await engine.trigger_project(
        project_type=req.project_type,
        district_id=req.district_id,
        x=req.x,
        y=req.y,
        target_x=req.target_x,
        target_y=req.target_y,
    )
    await db.commit()

    return {
        "id": str(project.id),
        "name": project.name,
        "type": project.project_type,
        "district_id": str(project.district_id) if project.district_id else None,
        "x": project.x,
        "y": project.y,
        "target_x": project.target_x,
        "target_y": project.target_y,
        "budget": project.budget,
    }


class PreviewImpactRequest(BaseModel):
    project_type: str
    x: float
    y: float
    target_x: float | None = None
    target_y: float | None = None


@router.post("/preview-impact")
async def preview_impact(req: PreviewImpactRequest, db: AsyncSession = Depends(get_db)):
    """Read-only 'what if' — dispatches to the per-type impact strategy in
    impact_strategies.py and returns its calculated metrics, before anything is
    committed. No project is created here. This is what both the click-to-lock-in
    preview AND the continuous live-hover preview call."""
    if req.project_type not in BUILD_PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown project_type: {req.project_type}")

    strategy = IMPACT_STRATEGIES.get(req.project_type)
    if not strategy:
        return {
            "beneficiaries": [], "total_beneficiaries": 0, "businesses": [],
            "summary": "No impact model for this project type yet.",
        }

    if req.project_type in ("bridge_build", "road_build") and (req.target_x is None or req.target_y is None):
        raise HTTPException(status_code=400, detail="target_x/target_y required for this project type")

    try:
        result = await strategy(db, req.x, req.y, target_x=req.target_x, target_y=req.target_y, project_type=req.project_type)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    return result.to_dict()


@router.get("/stats")
async def infra_stats(db: AsyncSession = Depends(get_db)):
    grids = await db.execute(select(sqlfunc.count()).select_from(UtilityGrid))
    operational = await db.execute(
        select(sqlfunc.count()).select_from(UtilityGrid).where(UtilityGrid.is_operational.is_(True))
    )
    avg_health = await db.execute(select(sqlfunc.avg(UtilityGrid.health)).select_from(UtilityGrid))
    avg_reliability = await db.execute(select(sqlfunc.avg(UtilityGrid.reliability)).select_from(UtilityGrid))
    active_projects = await db.execute(
        select(sqlfunc.count()).select_from(InfraProject).where(InfraProject.is_active.is_(True))
    )
    completed_projects = await db.execute(
        select(sqlfunc.count()).select_from(InfraProject).where(InfraProject.is_completed.is_(True))
    )

    return {
        "total_grids": grids.scalar() or 0,
        "operational_grids": operational.scalar() or 0,
        "avg_health": round(avg_health.scalar() or 0, 3),
        "avg_reliability": round(avg_reliability.scalar() or 0, 3),
        "active_projects": active_projects.scalar() or 0,
        "completed_projects": completed_projects.scalar() or 0,
    }


@router.get("/grids")
async def list_grids(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UtilityGrid).order_by(UtilityGrid.utility_type))
    return [{
        "id": str(g.id),
        "utility_type": g.utility_type,
        "capacity": g.capacity,
        "current_load": g.current_load,
        "load_pct": round(g.current_load / max(1, g.capacity), 3),
        "reliability": round(g.reliability, 3),
        "coverage_pct": round(g.coverage_pct, 3),
        "health": round(g.health, 3),
        "is_operational": g.is_operational,
        "price_per_unit": g.price_per_unit,
    } for g in result.scalars().all()]


@router.get("/projects")
async def list_projects(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InfraProject).order_by(InfraProject.is_active.desc(), InfraProject.progress.desc()).limit(limit)
    )
    projects = result.scalars().all()

    districts_result = await db.execute(select(District))
    district_by_id = {d.id: d for d in districts_result.scalars().all()}

    out = []
    for p in projects:
        d = district_by_id.get(p.district_id) if p.district_id else None
        out.append({
            "id": str(p.id),
            "name": p.name,
            "type": p.project_type,
            "budget": p.budget,
            "spent": round(p.spent, 2),
            "progress": round(p.progress, 3),
            "is_active": p.is_active,
            "is_completed": p.is_completed,
            "district_name": d.name if d else None,
            "x": p.x if p.x is not None else (d.center_x if d else None),
            "y": p.y if p.y is not None else (d.center_y if d else None),
            "target_x": p.target_x,
            "target_y": p.target_y,
            "radius": d.radius if d else None,
        })
    return out

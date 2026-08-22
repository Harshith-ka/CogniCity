"""API routes for government AI and policies."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.government.government_ai import GovernmentAI

router = APIRouter(prefix="/government", tags=["government"])


@router.get("/policies")
async def list_policies(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    gov = GovernmentAI(db)
    return await gov.get_all_policies(active_only)


@router.get("/budgets")
async def department_budgets(db: AsyncSession = Depends(get_db)):
    gov = GovernmentAI(db)
    return await gov.get_department_budgets()


@router.get("/decisions")
async def recent_decisions(db: AsyncSession = Depends(get_db)):
    gov = GovernmentAI(db)
    return gov.decision_history[-50:]


@router.post("/run-cycle")
async def force_government_cycle(db: AsyncSession = Depends(get_db)):
    from datetime import datetime

    from backend.app.analytics.metrics import compute_city_metrics

    metrics_obj = await compute_city_metrics(db)
    metrics = metrics_obj.model_dump()

    gov = GovernmentAI(db)
    decisions = await gov.run_government_cycle(metrics, datetime.utcnow())
    return {"decisions": decisions, "count": len(decisions)}

"""Phase 4 API: AI City Advisor endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services.city_advisor import CityAdvisor
from backend.app.services.llm_service import get_llm_service

router = APIRouter(prefix="/api/ai-advisor", tags=["ai_advisor"])


class ScenarioRequest(BaseModel):
    scenario: str


class QuestionRequest(BaseModel):
    question: str


async def _get_current_metrics(db: AsyncSession) -> dict:
    from backend.app.analytics.metrics import compute_city_metrics
    metrics = await compute_city_metrics(db)
    return metrics.model_dump()


async def _get_history(db: AsyncSession) -> list[dict]:
    from backend.app.analytics.history import MetricsHistoryTracker
    tracker = MetricsHistoryTracker(db)
    return await tracker.get_history(limit=50)


@router.get("/status")
async def advisor_status():
    llm = get_llm_service()
    return {
        "available": llm.is_available,
        "provider": llm.provider,
        "model": llm.model,
    }


@router.get("/analyze")
async def analyze_city(db: AsyncSession = Depends(get_db)):
    advisor = CityAdvisor(db)
    metrics = await _get_current_metrics(db)
    history = await _get_history(db)
    analysis = await advisor.analyze_city_state(metrics, history)
    return analysis or {"error": "Analysis failed"}


@router.post("/scenario")
async def scenario_analysis(
    req: ScenarioRequest, db: AsyncSession = Depends(get_db)
):
    advisor = CityAdvisor(db)
    metrics = await _get_current_metrics(db)
    result = await advisor.scenario_analysis(metrics, req.scenario)
    return result or {"error": "Scenario analysis failed"}


@router.get("/report")
async def city_report(db: AsyncSession = Depends(get_db)):
    advisor = CityAdvisor(db)
    metrics = await _get_current_metrics(db)
    history = await _get_history(db)
    report = await advisor.generate_city_report(metrics, history)
    return {"report": report or "Report generation failed"}


@router.post("/ask")
async def ask_advisor(
    req: QuestionRequest, db: AsyncSession = Depends(get_db)
):
    advisor = CityAdvisor(db)
    metrics = await _get_current_metrics(db)
    answer = await advisor.ask_advisor(req.question, metrics)
    return {"answer": answer or "Could not generate an answer"}

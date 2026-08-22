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
    """Free-text scenario — LLM estimate only, no grounded formula exists for
    arbitrary natural language. Kept for anything outside the grounded presets below."""
    advisor = CityAdvisor(db)
    metrics = await _get_current_metrics(db)
    result = await advisor.scenario_analysis(metrics, req.scenario)
    return result or {"error": "Scenario analysis failed"}


@router.get("/whatif/presets")
async def whatif_presets():
    from backend.app.services.whatif_scenarios import WHATIF_PRESETS
    return WHATIF_PRESETS


class WhatIfRunRequest(BaseModel):
    key: str
    params: dict = {}


@router.post("/whatif/run")
async def whatif_run(req: WhatIfRunRequest, db: AsyncSession = Depends(get_db)):
    """Grounded what-if scenario — every number comes from the simulation's own live
    formulas (or, for infrastructure, the same impact model the 3D Build Mode preview
    uses), not an LLM guess. The LLM only phrases the plain-language summary of numbers
    already computed here."""
    from backend.app.services.whatif_scenarios import run_preset_scenario
    try:
        result = await run_preset_scenario(db, req.key, req.params)
    except ValueError as err:
        return {"error": str(err)}
    return result.to_dict()


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

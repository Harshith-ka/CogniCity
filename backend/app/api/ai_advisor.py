"""Phase 4 API: AI City Advisor endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
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


@router.get("/scorecard")
async def advisor_scorecard(db: AsyncSession = Depends(get_db)):
    """Backs the mobile app's AI Advisor overview card — replaces what used to be a
    static mock object (healthIndex/economicStability/safetyScore/carbonScore all
    hardcoded) with real, DB-derived numbers. Each score is an explicit, documented
    formula over real simulation data, not a fabricated figure:

      healthIndex        = avg citizen health (0-1 scale) as a %
      economicStability   = 70% weight on employment rate, 30% on avg happiness —
                             a simple blend since there's no single "economy" field
      safetyScore         = crime clearance rate, discounted by unsolved case volume
                             relative to population (more unsolved crime per capita
                             pulls the score down even if the clearance rate is fine)
      carbonScore         = inverted air_quality_index (lower AQI = better air = higher
                             score); "no_data" until the environment module has seeded
                             at least one EnvironmentState row, same as /environment/stats
    """
    from backend.app.analytics.metrics import compute_city_metrics
    from backend.app.crime.crime_engine import CrimeEngine
    from backend.app.models.environment import EnvironmentState

    metrics = await compute_city_metrics(db)
    health_index = round(metrics.avg_health * 100, 1) if metrics.population else 0.0
    economic_stability = round(
        (1 - metrics.unemployment_rate) * 70 + metrics.avg_happiness * 30, 1
    ) if metrics.population else 0.0

    crime_engine = CrimeEngine(db)
    crime_stats = await crime_engine.get_stats()
    total_crimes = crime_stats.get("total", 0)
    unsolved = crime_stats.get("unsolved", 0)
    if total_crimes == 0:
        safety_score = 92.0  # no recorded crime yet — optimistic default, not a real signal either way
    else:
        clearance_rate = crime_stats.get("solved", 0) / total_crimes
        unsolved_per_1000_pop = (unsolved / metrics.population * 1000) if metrics.population else 0
        safety_score = round(max(0.0, min(100.0, clearance_rate * 100 - unsolved_per_1000_pop * 2)), 1)

    env_result = await db.execute(
        select(EnvironmentState).where(EnvironmentState.is_current.is_(True)).limit(1)
    )
    env_state = env_result.scalar_one_or_none()
    carbon_score = round(max(0.0, min(100.0, 100 - env_state.air_quality_index)), 1) if env_state else None

    advisor = CityAdvisor(db)
    history = await _get_history(db)
    analysis = await advisor.analyze_city_state(metrics.model_dump(), history) or {}

    top_issues = analysis.get("top_issues", [])
    return {
        "healthIndex": health_index,
        "economicStability": economic_stability,
        "safetyScore": safety_score,
        "carbonScore": carbon_score,  # null until environment module has data
        "summary": analysis.get("overall_assessment", "No analysis available yet."),
        "riskLevel": analysis.get("risk_level", "moderate"),
        "criticalRisks": [i["issue"] for i in top_issues if i.get("severity") in ("high", "critical")],
        # Every field here comes straight from the grounded analysis above (real
        # metrics run through either the LLM or the rule-based fallback in
        # CityAdvisor._rule_based_analysis) — no cost/ROI estimate is invented because
        # neither path actually produces one.
        "recommendedPolicies": [
            {
                "issue": i.get("issue", ""),
                "severity": i.get("severity", "medium"),
                "recommendation": i.get("recommendation", ""),
                "expectedImpact": i.get("expected_impact", ""),
            }
            for i in top_issues
        ],
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

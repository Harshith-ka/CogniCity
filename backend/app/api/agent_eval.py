"""API Router for AI Agent Evaluation & Sandbox Testing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.agent_eval.models import (
    AgentTestRequest,
    EvaluationScorecard,
    CohortDistribution,
)
from backend.app.agent_eval.eval_engine import AgentEvaluationEngine
from backend.app.agent_eval.population_sampler import PopulationSampler
from backend.app.agent_eval.schema_resolver import DOMAIN_PRESETS, DomainPreset, DynamicSchemaConfig
from backend.app.agent_eval.correlated_generator import CorrelatedPopulationGenerator

router = APIRouter(prefix="/api/eval", tags=["agent-evaluation"])


@router.post("/run-test", response_model=EvaluationScorecard)
async def run_agent_evaluation(
    req: AgentTestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Executes a pre-deployment test of an AI agent against isolated in-memory synthetic citizens."""
    engine = AgentEvaluationEngine(db)
    scorecard = await engine.run_evaluation(req)
    return scorecard


@router.get("/reports")
async def list_evaluation_reports():
    """Lists recent evaluation scorecards."""
    return AgentEvaluationEngine.list_reports()


@router.get("/reports/{test_id}", response_model=EvaluationScorecard)
async def get_evaluation_report(test_id: str):
    """Retrieves a specific evaluation scorecard and demographic breakdown."""
    report = AgentEvaluationEngine.get_report(test_id)
    if not report:
        raise HTTPException(status_code=404, detail="Evaluation report not found")
    return report


@router.get("/schema-presets")
async def list_schema_presets():
    """Lists standard domain schemas (Cardiology, Credit, Housing, E-Commerce)."""
    return [
        {
            "id": preset.value,
            "name": preset.name.replace("_", " ").title(),
            "feature_count": len(features),
            "features": [f.model_dump() for f in features],
        }
        for preset, features in DOMAIN_PRESETS.items()
    ]


@router.post("/correlated-sample")
async def generate_correlated_sample(
    domain: DomainPreset = DomainPreset.CARDIOLOGY_UCI,
    sample_size: int = 10,
    adversarial_intensity: float = 0.2,
):
    """Generates a sample of multi-layer correlated synthetic records for inspection."""
    cfg = DynamicSchemaConfig(domain=domain)
    generator = CorrelatedPopulationGenerator(cfg)
    return generator.generate_cohort(sample_size=min(sample_size, 50), adversarial_intensity=adversarial_intensity)


@router.get("/cohort-distributions")
async def list_cohort_distributions():
    """Lists available demographic and adversarial population distributions."""
    return [
        {"id": c.value, "name": c.name.replace("_", " ").title()}
        for c in CohortDistribution
    ]


@router.post("/preview-cohort")
async def preview_synthetic_cohort(
    cohort_type: CohortDistribution = CohortDistribution.BALANCED_GENERAL,
    sample_size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Generates a small preview sample of synthetic citizen profiles without running a full test."""
    sampler = PopulationSampler(db)
    cohort = await sampler.sample_cohort(cohort_type, sample_size=min(sample_size, 50))
    return cohort

"""Unit tests for Universal AI Agent Testing & Behavioral Evaluation Sandbox."""

import asyncio
from backend.app.agent_eval.models import (
    AgentTestRequest,
    AgentProtocol,
    CohortDistribution,
    InteractionMode,
)
from backend.app.agent_eval.population_sampler import PopulationSampler
from backend.app.agent_eval.eval_engine import AgentEvaluationEngine


def test_population_sampler():
    async def _run():
        sampler = PopulationSampler(db=None)
        cohort = await sampler.sample_cohort(
            cohort_type=CohortDistribution.BALANCED_GENERAL,
            sample_size=100,
            adversarial_intensity=0.2,
        )
        assert len(cohort) == 100
        assert all(c.id for c in cohort)
        assert all(c.annual_income > 0 for c in cohort)

    asyncio.run(_run())


def test_adversarial_cohort_generation():
    async def _run():
        sampler = PopulationSampler(db=None)
        cohort = await sampler.sample_cohort(
            cohort_type=CohortDistribution.SENIOR_POPULATION,
            sample_size=50,
            adversarial_intensity=0.5,
        )
        assert len(cohort) == 50
        assert all(c.age >= 60 for c in cohort)

    asyncio.run(_run())


def test_end_to_end_agent_evaluation():
    async def _run():
        engine = AgentEvaluationEngine(db=None)
        req = AgentTestRequest(
            agent_name="Test Underwriter Bot v1",
            protocol=AgentProtocol.MOCK_BENCHMARK,
            cohort_distribution=CohortDistribution.BALANCED_GENERAL,
            sample_size=120,
            adversarial_intensity=0.25,
            interaction_mode=InteractionMode.ONE_SHOT,
        )

        scorecard = await engine.run_evaluation(req)

        assert scorecard.test_id is not None
        assert scorecard.agent_name == "Test Underwriter Bot v1"
        assert scorecard.population_size == 120
        assert 0.0 <= scorecard.overall_adoption_rate <= 100.0
        assert 0.0 <= scorecard.avg_trust_index <= 1.0
        assert 0.0 <= scorecard.fairness_index <= 1.0
        assert len(scorecard.demographic_fairness) > 0
        assert len(scorecard.sample_interactions) > 0

    asyncio.run(_run())

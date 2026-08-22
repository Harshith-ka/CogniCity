"""Unit tests for Multi-Layer Correlated Population Generator and Longitudinal Simulator."""

import asyncio
from backend.app.agent_eval.schema_resolver import (
    DynamicSchemaConfig,
    DomainPreset,
)
from backend.app.agent_eval.correlated_generator import CorrelatedPopulationGenerator
from backend.app.agent_eval.longitudinal_simulator import LongitudinalSimulator
from backend.app.agent_eval.models import AgentTestRequest, AgentProtocol
from backend.app.agent_eval.eval_engine import AgentEvaluationEngine


def test_correlated_population_cardiology():
    cfg = DynamicSchemaConfig(domain=DomainPreset.CARDIOLOGY_UCI)
    generator = CorrelatedPopulationGenerator(cfg)
    cohort = generator.generate_cohort(sample_size=150, adversarial_intensity=0.1)

    assert len(cohort) == 150
    for person in cohort:
        assert "trestbps" in person
        assert "chol" in person
        assert "thalach" in person
        assert "oldpeak" in person
        assert 90 <= person["trestbps"] <= 220
        assert 120 <= person["chol"] <= 460
        assert 70 <= person["thalach"] <= 220


def test_correlated_population_credit():
    cfg = DynamicSchemaConfig(domain=DomainPreset.CREDIT_LENDING)
    generator = CorrelatedPopulationGenerator(cfg)
    cohort = generator.generate_cohort(sample_size=100)

    assert len(cohort) == 100
    for person in cohort:
        assert "annual_income" in person
        assert "dti_ratio" in person
        assert "credit_score" in person
        assert 350 <= person["credit_score"] <= 850
        assert 0.05 <= person["dti_ratio"] <= 0.90


def test_longitudinal_drift_simulation():
    cfg = DynamicSchemaConfig(domain=DomainPreset.CARDIOLOGY_UCI)
    generator = CorrelatedPopulationGenerator(cfg)
    population = generator.generate_cohort(sample_size=100)

    simulator = LongitudinalSimulator()
    result = simulator.simulate_longitudinal_trajectory(
        population=population,
        horizon_days=90,
        intervention_frequency_days=30,
        model_efficacy_factor=0.8,
    )

    assert result.horizon_days == 90
    assert len(result.timeline_snapshots) == 4  # Day 0, 30, 60, 90
    assert result.timeline_snapshots[0].day == 0
    assert result.timeline_snapshots[-1].day == 90
    assert 0.0 <= result.relative_risk_reduction_pct <= 100.0


def test_end_to_end_correlated_evaluation():
    async def _run():
        engine = AgentEvaluationEngine(db=None)
        req = AgentTestRequest(
            agent_name="CardioTest Model",
            domain_preset="cardiology_uci",
            protocol=AgentProtocol.MOCK_BENCHMARK,
            sample_size=100,
            simulation_horizon_days=90,
        )

        scorecard = await engine.run_evaluation(req)
        assert scorecard.test_id is not None
        assert scorecard.domain == "cardiology_uci"
        assert len(scorecard.schema_features) > 0
        assert scorecard.longitudinal_summary is not None
        assert len(scorecard.longitudinal_summary["timeline_snapshots"]) > 0

    asyncio.run(_run())

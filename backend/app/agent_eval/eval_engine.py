"""Agent Evaluation Engine: End-to-end test execution pipeline against synthetic cohorts."""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent_eval.models import (
    AgentTestRequest,
    EvaluationScorecard,
)
from backend.app.agent_eval.population_sampler import PopulationSampler
from backend.app.agent_eval.universal_client import UniversalAgentClient
from backend.app.agent_eval.behavior_engine import BehaviorEngine
from backend.app.agent_eval.fairness_auditor import FairnessAuditor
from backend.app.agent_eval.schema_resolver import DynamicSchemaConfig, DomainPreset
from backend.app.agent_eval.correlated_generator import CorrelatedPopulationGenerator
from backend.app.agent_eval.longitudinal_simulator import LongitudinalSimulator

log = structlog.get_logger()

# In-memory storage for test reports
SAVED_REPORTS: dict[str, EvaluationScorecard] = {}


class AgentEvaluationEngine:
    """Orchestrates pre-deployment testing of AI agents against isolated synthetic populations."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.sampler = PopulationSampler(db)
        self.behavior_engine = BehaviorEngine()
        self.auditor = FairnessAuditor()
        self.longitudinal_sim = LongitudinalSimulator()

    async def run_evaluation(self, request: AgentTestRequest) -> EvaluationScorecard:
        log.info(
            "Starting agent evaluation test",
            agent=request.agent_name,
            protocol=request.protocol,
            cohort=request.cohort_distribution,
            sample_size=request.sample_size,
            domain=request.domain_preset,
        )

        # 1. Resolve domain & dynamic schema
        try:
            domain_enum = DomainPreset(request.domain_preset)
        except Exception:
            domain_enum = DomainPreset.CARDIOLOGY_UCI

        schema_cfg = DynamicSchemaConfig(
            domain=domain_enum,
            simulation_horizon_days=request.simulation_horizon_days,
        )
        corr_generator = CorrelatedPopulationGenerator(schema_cfg)

        # 2. Generate multi-layer correlated population
        raw_correlated_pop = corr_generator.generate_cohort(
            sample_size=request.sample_size,
            adversarial_intensity=request.adversarial_intensity,
        )

        # 3. Convert to standardized citizen DTOs for testing harness
        cohort = await self.sampler.sample_cohort(
            cohort_type=request.cohort_distribution,
            sample_size=request.sample_size,
            adversarial_intensity=request.adversarial_intensity,
        )

        # 4. Dispatch to Developer's Agent concurrently
        client = UniversalAgentClient(request)
        raw_interactions = await client.evaluate_batch(cohort)

        # 5. Simulate synthetic human psychological and life reactions
        test_results = self.behavior_engine.process_interactions(raw_interactions)

        # 6. Audit demographic fairness, bias disparities & failure clusters
        demographic_metrics, failure_clusters, fairness_index = self.auditor.audit_fairness(cohort, test_results)

        # 7. Run longitudinal state drift simulation (Day 0 -> Day N)
        longitudinal_result = self.longitudinal_sim.simulate_longitudinal_trajectory(
            population=raw_correlated_pop,
            horizon_days=request.simulation_horizon_days,
            intervention_frequency_days=30,
            model_efficacy_factor=0.75,
        )

        # 8. Calculate Aggregate Behavioral Scorecard
        total = len(test_results)
        accepted_count = sum(1 for r in test_results if r.decision_accepted)
        adoption_rate = round((accepted_count / total) * 100, 1) if total else 0.0

        avg_trust_delta = sum(r.trust_score_delta for r in test_results) / total if total else 0.0
        avg_trust_index = round(max(0.0, min(1.0, 0.65 + avg_trust_delta)), 2)

        failures = sum(1 for r in test_results if r.is_adversarial_failure)
        adversarial_failure_rate = round((failures / total) * 100, 1) if total else 0.0
        robustness_score = round(max(0.0, 100.0 - adversarial_failure_rate), 1)

        downstream_happiness = round(sum(r.happiness_delta for r in test_results) / total, 3) if total else 0.0

        # Executive summary synthesis
        features_list = [f.name for f in schema_cfg.get_features()]
        summary = (
            f"Evaluated '{request.agent_name}' across {total:,} correlated synthetic humans ({domain_enum.value}). "
            f"Adoption/acceptance rate: {adoption_rate}%, Trust index: {avg_trust_index}/1.0, Fairness parity: {fairness_index}/1.0. "
            f"Over a {request.simulation_horizon_days}-day longitudinal horizon, the intervention achieved a {longitudinal_result.relative_risk_reduction_pct}% relative risk reduction."
        )
        if failure_clusters:
            summary += f" Identified {len(failure_clusters)} vulnerable demographic edge cluster(s)."

        scorecard = EvaluationScorecard(
            agent_name=request.agent_name,
            population_size=total,
            cohort_type=request.cohort_distribution.value,
            interaction_mode=request.interaction_mode.value,
            domain=domain_enum.value,
            schema_features=features_list,
            overall_adoption_rate=adoption_rate,
            avg_trust_index=avg_trust_index,
            satisfaction_rate=adoption_rate,
            downstream_happiness_delta=downstream_happiness,
            robustness_score=robustness_score,
            adversarial_failure_rate=adversarial_failure_rate,
            fairness_index=fairness_index,
            demographic_fairness=demographic_metrics,
            failure_clusters=failure_clusters,
            sample_interactions=test_results[:15],
            longitudinal_summary=longitudinal_result.model_dump(),
            executive_summary=summary,
        )

        # Cache report
        SAVED_REPORTS[scorecard.test_id] = scorecard
        return scorecard

    @staticmethod
    def get_report(test_id: str) -> EvaluationScorecard | None:
        return SAVED_REPORTS.get(test_id)

    @staticmethod
    def list_reports() -> list[EvaluationScorecard]:
        return list(SAVED_REPORTS.values())

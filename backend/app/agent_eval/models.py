"""Data models and schemas for Universal AI Agent Testing & Evaluation Sandbox."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class AgentProtocol(StrEnum):
    REST_WEBHOOK = "rest_webhook"
    OPENAI_CHAT = "openai_chat"
    MOCK_BENCHMARK = "mock_benchmark"
    UPLOADED_MODEL = "uploaded_model"  # a real .onnx file, run locally — see model_store.py


class InteractionMode(StrEnum):
    ONE_SHOT = "one_shot"          # Single classification / decision / prediction
    CONVERSATIONAL = "conversational"  # Multi-turn interactive dialogue
    LONGITUDINAL = "longitudinal"    # Multi-tick life simulation impact


class CohortDistribution(StrEnum):
    BALANCED_GENERAL = "balanced_general"
    SENIOR_POPULATION = "senior_population"
    LOW_INCOME_HIGH_DEBT = "low_income_high_debt"
    YOUTH_TECH_SAVVY = "youth_tech_savvy"
    HIGH_STRESS_CHRONIC = "high_stress_chronic"
    ADVERSARIAL_EDGE_CASES = "adversarial_edge_cases"


class CitizenProfileDTO(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    occupation: str
    education: str
    district: str
    annual_income: float
    savings: float
    monthly_expenses: float
    credit_score_estimate: int
    health_index: float
    stress_level: float
    happiness: float
    tech_savviness: str
    chronic_conditions: list[str] = Field(default_factory=list)
    recent_activity: str = "daily_routine"


class AgentTestRequest(BaseModel):
    agent_name: str = "Candidate AI Agent"
    agent_description: str = "Decision / prediction model under evaluation"
    domain_preset: str = "cardiology_uci"
    protocol: AgentProtocol = AgentProtocol.MOCK_BENCHMARK
    endpoint_url: str | None = None
    api_key: str | None = None
    model_id: str | None = None  # set when protocol == UPLOADED_MODEL, from POST /upload-model
    interaction_mode: InteractionMode = InteractionMode.ONE_SHOT
    prompt_template: str | None = None
    cohort_distribution: CohortDistribution = CohortDistribution.BALANCED_GENERAL
    sample_size: int = Field(default=500, ge=10, le=25000)
    adversarial_intensity: float = Field(default=0.2, ge=0.0, le=1.0)
    simulation_horizon_days: int = Field(default=90, ge=7, le=365)


class CitizenTestResult(BaseModel):
    citizen_id: str
    citizen_name: str
    demographics_summary: str
    agent_raw_input: dict[str, Any]
    agent_raw_output: dict[str, Any]
    decision_accepted: bool
    trust_score_delta: float
    happiness_delta: float
    is_adversarial_failure: bool
    failure_reason: str | None = None


class DemographicFairnessMetric(BaseModel):
    demographic_group: str
    sample_count: int
    acceptance_rate: float
    avg_trust_score: float
    disparity_ratio: float  # Compared to baseline average
    status: str  # "fair", "disparity_detected", "underrepresented"


class FailureCluster(BaseModel):
    cluster_name: str
    affected_percentage: float
    sample_size: int
    common_traits: list[str]
    root_cause: str
    suggested_fix: str


class EvaluationScorecard(BaseModel):
    test_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    population_size: int
    cohort_type: str
    interaction_mode: str
    domain: str = "cardiology_uci"
    schema_features: list[str] = Field(default_factory=list)
    
    # Core Behavioral Metrics
    overall_adoption_rate: float  # %
    avg_trust_index: float        # 0.0 - 1.0
    satisfaction_rate: float      # %
    downstream_happiness_delta: float
    
    # Reliability & Safety
    robustness_score: float       # 0 - 100%
    adversarial_failure_rate: float # %
    fairness_index: float         # 0.0 - 1.0 (1.0 = perfect parity)
    
    # Detailed Breakdowns
    demographic_fairness: list[DemographicFairnessMetric]
    failure_clusters: list[FailureCluster]
    sample_interactions: list[CitizenTestResult]
    longitudinal_summary: dict[str, Any] | None = None
    executive_summary: str

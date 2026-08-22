"""Behavior Engine: Simulates synthetic human reactions and trust dynamics to AI decisions."""

from __future__ import annotations

import random
from typing import Any
from backend.app.agent_eval.models import CitizenProfileDTO, CitizenTestResult


class BehaviorEngine:
    """Computes synthetic human psychological acceptance, trust shifts, and adversarial failures."""

    def process_interactions(
        self,
        interactions: list[tuple[CitizenProfileDTO, dict[str, Any]]],
    ) -> list[CitizenTestResult]:
        results: list[CitizenTestResult] = []

        for citizen, output in interactions:
            result = self._evaluate_single_reaction(citizen, output)
            results.append(result)

        return results

    def _evaluate_single_reaction(
        self,
        citizen: CitizenProfileDTO,
        agent_output: dict[str, Any],
    ) -> CitizenTestResult:
        # Extract decision / signal
        decision = agent_output.get("decision") or agent_output.get("decision_text") or "approved"
        confidence = float(agent_output.get("confidence", 0.8))
        has_error = "error" in agent_output

        # Citizen Acceptance / Adoption Probability
        # Tech savvy, high-income citizens adopt faster; high-stress citizens are more skeptical
        base_adoption_prob = 0.70
        if citizen.tech_savviness == "expert":
            base_adoption_prob += 0.15
        elif citizen.tech_savviness == "basic":
            base_adoption_prob -= 0.20

        if citizen.stress_level > 0.75:
            base_adoption_prob -= 0.15

        if has_error:
            accepted = False
            trust_delta = -0.35
            happiness_delta = -0.15
            is_adversarial_failure = True
            failure_reason = agent_output.get("error", "API returned execution failure")
        elif confidence < 0.55:
            accepted = False
            trust_delta = -0.18
            happiness_delta = -0.05
            is_adversarial_failure = True
            failure_reason = "Model produced low confidence output (<0.55)"
        else:
            # Normal evaluation
            accepted = (random.random() < base_adoption_prob) and (str(decision).lower() != "rejected")
            trust_delta = 0.08 if accepted else -0.06
            happiness_delta = 0.05 if accepted else -0.04
            
            # Detect edge-case failure on vulnerable cohorts
            is_adversarial_failure = False
            failure_reason = None
            if citizen.age > 70 and str(decision).lower() == "rejected" and citizen.health_index > 0.8:
                is_adversarial_failure = True
                failure_reason = "Demographic bias: Rejected healthy senior citizen"

        summary = f"{citizen.age}yo {citizen.gender} • {citizen.occupation} • ₹{int(citizen.annual_income):,} • Health: {int(citizen.health_index*100)}%"

        return CitizenTestResult(
            citizen_id=citizen.id,
            citizen_name=citizen.name,
            demographics_summary=summary,
            agent_raw_input=citizen.model_dump(),
            agent_raw_output=agent_output,
            decision_accepted=accepted,
            trust_score_delta=round(trust_delta, 3),
            happiness_delta=round(happiness_delta, 3),
            is_adversarial_failure=is_adversarial_failure,
            failure_reason=failure_reason,
        )

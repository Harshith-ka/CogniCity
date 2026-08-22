"""Longitudinal Simulator: Simulates synthetic human state evolution and intervention efficacy over time."""

from __future__ import annotations

import random
from typing import Any
from pydantic import BaseModel, Field


class LongitudinalSnapshot(BaseModel):
    day: int
    avg_systolic_bp: float
    avg_cholesterol: float
    avg_stress_level: float
    active_compliance_rate: float
    high_risk_population_pct: float


class LongitudinalSimulationResult(BaseModel):
    horizon_days: int
    intervention_frequency_days: int
    initial_population_size: int
    baseline_high_risk_pct: float
    final_high_risk_pct: float
    relative_risk_reduction_pct: float
    average_adherence_decay: float
    timeline_snapshots: list[LongitudinalSnapshot] = Field(default_factory=list)
    behavioral_takeaway: str


class LongitudinalSimulator:
    """Evolves synthetic citizen states across simulation horizons with closed-loop agent interventions."""

    def simulate_longitudinal_trajectory(
        self,
        population: list[dict[str, Any]],
        horizon_days: int = 90,
        intervention_frequency_days: int = 30,
        model_efficacy_factor: float = 0.75,
    ) -> LongitudinalSimulationResult:
        pop_clones = [dict(p) for p in population]
        snapshots: list[LongitudinalSnapshot] = []

        # Record initial baseline
        initial_high_risk = self._compute_high_risk_pct(pop_clones)
        snapshots.append(self._record_snapshot(0, pop_clones, 100.0))

        current_compliance = 0.85
        num_rounds = max(1, horizon_days // intervention_frequency_days)

        for step in range(1, num_rounds + 1):
            day = step * intervention_frequency_days
            
            # Natural adherence decay over time (human fatigue)
            current_compliance = max(0.25, current_compliance * random.uniform(0.85, 0.94))

            # Update each citizen's state
            for person in pop_clones:
                indiv_compliance = person.get("_compliance_propensity", 0.6) * current_compliance
                is_adherent = random.random() < indiv_compliance

                # Health state drift
                if "trestbps" in person:
                    if is_adherent:
                        # Beneficial effect of intervention
                        person["trestbps"] = max(95, person["trestbps"] - random.uniform(4.0, 10.0) * model_efficacy_factor)
                        if "chol" in person:
                            person["chol"] = max(130, person["chol"] - random.uniform(5.0, 14.0) * model_efficacy_factor)
                    else:
                        # Non-adherent: gradual progression with stress
                        stress = person.get("_stress_level", 0.5)
                        person["trestbps"] = min(205, person["trestbps"] + (stress * 3.5))

                # Financial state drift
                if "credit_score" in person and "dti_ratio" in person:
                    if is_adherent:
                        person["dti_ratio"] = max(0.1, person["dti_ratio"] - 0.04 * model_efficacy_factor)
                        person["credit_score"] = min(850, person["credit_score"] + int(12 * model_efficacy_factor))
                    else:
                        person["dti_ratio"] = min(0.9, person["dti_ratio"] + 0.02)

            snapshots.append(self._record_snapshot(day, pop_clones, current_compliance * 100))

        final_high_risk = self._compute_high_risk_pct(pop_clones)
        rrr = round(max(0.0, ((initial_high_risk - final_high_risk) / max(0.01, initial_high_risk)) * 100), 1)

        takeaway = (
            f"Over {horizon_days} simulation days, the AI intervention achieved a {rrr}% relative risk reduction. "
            f"Adherence naturally decayed to {round(current_compliance * 100, 1)}% by day {horizon_days}, "
            f"demonstrating that real-world intervention efficacy is constrained by behavioral fatigue."
        )

        return LongitudinalSimulationResult(
            horizon_days=horizon_days,
            intervention_frequency_days=intervention_frequency_days,
            initial_population_size=len(population),
            baseline_high_risk_pct=round(initial_high_risk, 1),
            final_high_risk_pct=round(final_high_risk, 1),
            relative_risk_reduction_pct=rrr,
            average_adherence_decay=round((1.0 - current_compliance) * 100, 1),
            timeline_snapshots=snapshots,
            behavioral_takeaway=takeaway,
        )

    def _record_snapshot(self, day: int, population: list[dict[str, Any]], compliance_rate: float) -> LongitudinalSnapshot:
        bps = [p["trestbps"] for p in population if "trestbps" in p]
        chols = [p["chol"] for p in population if "chol" in p]
        stresses = [p.get("_stress_level", 0.5) for p in population]

        avg_bp = sum(bps) / len(bps) if bps else 125.0
        avg_chol = sum(chols) / len(chols) if chols else 200.0
        avg_stress = sum(stresses) / len(stresses) if stresses else 0.5
        high_risk_pct = self._compute_high_risk_pct(population)

        return LongitudinalSnapshot(
            day=day,
            avg_systolic_bp=round(avg_bp, 1),
            avg_cholesterol=round(avg_chol, 1),
            avg_stress_level=round(avg_stress, 2),
            active_compliance_rate=round(compliance_rate, 1),
            high_risk_population_pct=round(high_risk_pct, 1),
        )

    def _compute_high_risk_pct(self, population: list[dict[str, Any]]) -> float:
        if not population:
            return 0.0
        count = 0
        for p in population:
            if "trestbps" in p and (p["trestbps"] > 140 or p.get("chol", 200) > 240):
                count += 1
            elif "credit_score" in p and (p["credit_score"] < 580 or p.get("dti_ratio", 0.4) > 0.55):
                count += 1
        return (count / len(population)) * 100.0

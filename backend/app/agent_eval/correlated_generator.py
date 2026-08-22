"""Multi-Layer Correlated Synthetic Population Generator.

Generates realistic correlated human cohorts matching arbitrary developer schemas using
a 4-layer causal Bayesian covariance graph:
  Layer 1 (Demographics) -> Layer 2 (Lifestyle) -> Layer 3 (Domain Biomarkers/Finances) -> Layer 4 (Psychology & Compliance).
"""

from __future__ import annotations

import math
import random
from typing import Any
from backend.app.agent_eval.schema_resolver import (
    DynamicSchemaConfig,
    DomainPreset,
    FeatureDefinition,
    FeatureType,
)


class CorrelatedPopulationGenerator:
    """Generates statistically coherent synthetic human cohorts preserving cross-feature correlations."""

    def __init__(self, config: DynamicSchemaConfig | None = None):
        self.config = config or DynamicSchemaConfig()

    def generate_cohort(
        self,
        sample_size: int = 500,
        adversarial_intensity: float = 0.2,
    ) -> list[dict[str, Any]]:
        """Generates sample_size realistic synthetic humans mapped to the target schema."""
        cohort: list[dict[str, Any]] = []

        for i in range(sample_size):
            person = self._generate_single_correlated_person(i, adversarial_intensity)
            cohort.append(person)

        return cohort

    def _generate_single_correlated_person(
        self,
        index: int,
        adversarial_intensity: float = 0.2,
    ) -> dict[str, Any]:
        # ─────────────────────────────────────────────────────────────
        # LAYER 1: DEMOGRAPHICS
        # ─────────────────────────────────────────────────────────────
        age = int(random.gauss(46, 15))
        age = max(18, min(85, age))
        sex = 1 if random.random() < 0.52 else 0  # 1 = Male, 0 = Female
        income = random.choice([250000, 450000, 750000, 1200000, 2200000, 4500000])

        # ─────────────────────────────────────────────────────────────
        # LAYER 2: LIFESTYLE & ENVIRONMENTAL STRESSORS
        # ─────────────────────────────────────────────────────────────
        # Older and higher-income individuals have varying stress and exercise habits
        work_hours = max(30, min(80, int(random.gauss(45, 10))))
        smoking = random.random() < (0.28 if sex == 1 else 0.14)
        alcohol = random.random() < 0.35
        exercise_days_per_week = max(0, min(7, int(random.gauss(2.5 - (age / 70) + (1 if work_hours < 45 else -0.5), 1.5))))
        stress_level = max(0.1, min(1.0, (work_hours / 70) * 0.6 + random.uniform(0.1, 0.4)))
        bmi = max(18.5, min(42.0, random.gauss(25.5 + (0.08 * age) - (0.6 * exercise_days_per_week), 4.2)))

        # ─────────────────────────────────────────────────────────────
        # LAYER 3: BIOLOGICAL & FINANCIAL BIOMARKERS (DOMAIN METRICS)
        # ─────────────────────────────────────────────────────────────
        # 1. Cardiology (UCI Heart Disease feature dependencies)
        # BP increases with age, BMI, stress, and smoking
        trestbps = int(105 + (0.45 * age) + (0.8 * (bmi - 22)) + (12 * stress_level) + (6 if smoking else 0) + random.gauss(0, 10))
        trestbps = max(90, min(210, trestbps))

        # Cholesterol correlates with age, BMI, and diet
        chol = int(150 + (1.2 * age) + (1.5 * (bmi - 20)) + (25 if smoking else 0) + random.gauss(0, 25))
        chol = max(120, min(450, chol))

        # Max Heart Rate (thalach) follows standard physiological formula 208 - 0.7*age + fitness boost
        thalach = int(208 - (0.72 * age) + (3.5 * exercise_days_per_week) - (8 * (bmi / 30)) + random.gauss(0, 12))
        thalach = max(70, min(210, thalach))

        # ST depression (oldpeak) increases with high BP, age, and stress
        is_cardio_compromised = (trestbps > 145 and chol > 240) or age > 62
        oldpeak = round(max(0.0, min(6.2, random.expovariate(1.6) + (1.2 if is_cardio_compromised else 0.0))), 1)
        exang = 1 if (is_cardio_compromised and random.random() < 0.45) else 0
        cp = random.choice([0, 1, 2, 3]) if is_cardio_compromised else (0 if random.random() < 0.7 else 1)
        fbs = 1 if (bmi > 28 and random.random() < 0.35) else 0
        restecg = random.choice([0, 1, 2]) if (trestbps > 150 or age > 65) else 0
        slope = 2 if oldpeak < 1.0 else (1 if oldpeak < 2.5 else 0)
        ca = min(3, max(0, int((age / 30) + (1 if smoking else 0) - (1 if exercise_days_per_week > 3 else 0))))
        thal = 2 if not is_cardio_compromised else (3 if random.random() < 0.6 else 1)

        # 2. Credit & Lending features
        dti_ratio = round(max(0.08, min(0.85, (0.45 - (income / 10000000) * 0.2) + (stress_level * 0.15) + random.gauss(0, 0.08))), 2)
        credit_score = int(780 - (dti_ratio * 250) + (income / 50000) + random.gauss(0, 40))
        credit_score = max(350, min(850, credit_score))
        liquid_savings = round(income * random.uniform(0.1, 1.5) * (credit_score / 700), -3)
        employment_years = max(0, min(40, int(age - 22 - random.randint(0, 5))))
        existing_loans_count = max(0, min(8, int(dti_ratio * 6 + random.randint(0, 2))))
        home_ownership = "OWN" if (age > 45 and income > 1200000) else ("MORTGAGE" if income > 600000 else "RENT")
        loan_amount_requested = round(income * random.uniform(0.5, 3.5), -4)

        # ─────────────────────────────────────────────────────────────
        # LAYER 4: PSYCHOLOGY & COMPLIANCE
        # ─────────────────────────────────────────────────────────────
        compliance_propensity = max(0.1, min(1.0, 0.75 - (stress_level * 0.3) + (0.1 if exercise_days_per_week > 2 else -0.15)))
        trust_propensity = max(0.2, min(1.0, 0.65 + (0.15 if age < 40 else -0.1)))

        # Inject Adversarial Edge Cases if triggered
        if random.random() < adversarial_intensity:
            if random.random() < 0.5:
                # Paradoxical healthy-senior or extreme rare profile
                age = random.choice([79, 83, 88])
                trestbps = 112
                chol = 160
                thalach = 168
                oldpeak = 0.0
            else:
                # Young extreme risk profile
                age = 23
                trestbps = 185
                chol = 390
                bmi = 38.5
                oldpeak = 3.8

        # Master feature dictionary
        master_features: dict[str, Any] = {
            "id": f"syn_{index + 1:05d}",
            # Demographics & Lifestyle
            "age": age,
            "sex": sex,
            "bmi": round(bmi, 1),
            "work_hours": work_hours,
            "smoking": int(smoking),
            "exercise_days_per_week": exercise_days_per_week,
            "stress_level": round(stress_level, 2),
            "compliance_propensity": round(compliance_propensity, 2),
            "trust_propensity": round(trust_propensity, 2),
            # Cardiology UCI features
            "cp": cp,
            "trestbps": trestbps,
            "chol": chol,
            "fbs": fbs,
            "restecg": restecg,
            "thalach": thalach,
            "exang": exang,
            "oldpeak": oldpeak,
            "slope": slope,
            "ca": ca,
            "thal": thal,
            # Credit & Lending features
            "annual_income": income,
            "dti_ratio": dti_ratio,
            "credit_score": credit_score,
            "liquid_savings": liquid_savings,
            "employment_years": employment_years,
            "existing_loans_count": existing_loans_count,
            "home_ownership": home_ownership,
            "loan_amount_requested": loan_amount_requested,
            # Housing features
            "buyer_budget": income * 5,
            "downpayment_capacity": liquid_savings * 0.8,
            "preferred_sqft": int(900 + (income / 10000) + random.randint(0, 500)),
            "family_size": random.randint(1, 6),
            "commute_tolerance_km": random.randint(5, 35),
            "preferred_district": random.choice(["Downtown Central", "Tech Corridor", "Residential North"]),
        }

        # Filter and extract ONLY the features requested in the schema
        target_features = self.config.get_features()
        if not target_features:
            return master_features

        output_record: dict[str, Any] = {"id": master_features["id"]}
        for f in target_features:
            if f.name in master_features:
                output_record[f.name] = master_features[f.name]
            else:
                # Custom feature fallback
                if f.feature_type == FeatureType.NUMERIC:
                    output_record[f.name] = round(random.uniform(f.min_value or 0.0, f.max_value or 100.0), 2)
                elif f.feature_type == FeatureType.CATEGORICAL:
                    output_record[f.name] = random.choice(f.categories or ["A", "B", "C"])
                elif f.feature_type == FeatureType.BOOLEAN:
                    output_record[f.name] = random.choice([0, 1])

        # Always preserve core behavior props for the digital twin engine
        output_record["_compliance_propensity"] = master_features["compliance_propensity"]
        output_record["_stress_level"] = master_features["stress_level"]
        output_record["_age"] = master_features["age"]
        return output_record

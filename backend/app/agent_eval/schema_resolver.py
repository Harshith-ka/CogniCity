"""Dynamic Schema Resolver: Parses arbitrary developer feature schemas and maps to causal generators."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class FeatureType(StrEnum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


class FeatureDefinition(BaseModel):
    name: str
    feature_type: FeatureType = FeatureType.NUMERIC
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    categories: list[str] | None = None
    description: str | None = None


class DomainPreset(StrEnum):
    CUSTOM = "custom"
    CARDIOLOGY_UCI = "cardiology_uci"
    CREDIT_LENDING = "credit_lending"
    REAL_ESTATE_HOUSING = "real_estate_housing"
    ECOMMERCE_RECSYS = "ecommerce_recsys"


# Standard Benchmark Schemas
DOMAIN_PRESETS: dict[DomainPreset, list[FeatureDefinition]] = {
    DomainPreset.CARDIOLOGY_UCI: [
        FeatureDefinition(name="age", feature_type=FeatureType.NUMERIC, unit="years", min_value=18, max_value=85),
        FeatureDefinition(name="sex", feature_type=FeatureType.CATEGORICAL, categories=["0", "1"], description="0=Female, 1=Male"),
        FeatureDefinition(name="cp", feature_type=FeatureType.CATEGORICAL, categories=["0", "1", "2", "3"], description="Chest pain type (0-3)"),
        FeatureDefinition(name="trestbps", feature_type=FeatureType.NUMERIC, unit="mm Hg", min_value=90, max_value=200, description="Resting blood pressure"),
        FeatureDefinition(name="chol", feature_type=FeatureType.NUMERIC, unit="mg/dl", min_value=120, max_value=420, description="Serum cholesterol"),
        FeatureDefinition(name="fbs", feature_type=FeatureType.BOOLEAN, description="Fasting blood sugar > 120 mg/dl"),
        FeatureDefinition(name="restecg", feature_type=FeatureType.CATEGORICAL, categories=["0", "1", "2"], description="Resting ECG results"),
        FeatureDefinition(name="thalach", feature_type=FeatureType.NUMERIC, unit="bpm", min_value=70, max_value=210, description="Max heart rate achieved"),
        FeatureDefinition(name="exang", feature_type=FeatureType.BOOLEAN, description="Exercise induced angina"),
        FeatureDefinition(name="oldpeak", feature_type=FeatureType.NUMERIC, min_value=0.0, max_value=6.2, description="ST depression induced by exercise"),
        FeatureDefinition(name="slope", feature_type=FeatureType.CATEGORICAL, categories=["0", "1", "2"], description="Slope of peak exercise ST segment"),
        FeatureDefinition(name="ca", feature_type=FeatureType.CATEGORICAL, categories=["0", "1", "2", "3"], description="Major vessels colored by flourosopy"),
        FeatureDefinition(name="thal", feature_type=FeatureType.CATEGORICAL, categories=["1", "2", "3"], description="Thalassemia"),
    ],
    DomainPreset.CREDIT_LENDING: [
        FeatureDefinition(name="annual_income", feature_type=FeatureType.NUMERIC, unit="INR", min_value=150000, max_value=10000000),
        FeatureDefinition(name="dti_ratio", feature_type=FeatureType.NUMERIC, min_value=0.05, max_value=0.85, description="Debt-to-income ratio"),
        FeatureDefinition(name="credit_score", feature_type=FeatureType.NUMERIC, min_value=350, max_value=850),
        FeatureDefinition(name="employment_years", feature_type=FeatureType.NUMERIC, unit="years", min_value=0, max_value=40),
        FeatureDefinition(name="liquid_savings", feature_type=FeatureType.NUMERIC, unit="INR", min_value=0, max_value=5000000),
        FeatureDefinition(name="existing_loans_count", feature_type=FeatureType.NUMERIC, min_value=0, max_value=8),
        FeatureDefinition(name="home_ownership", feature_type=FeatureType.CATEGORICAL, categories=["OWN", "MORTGAGE", "RENT"]),
        FeatureDefinition(name="loan_amount_requested", feature_type=FeatureType.NUMERIC, unit="INR", min_value=50000, max_value=5000000),
    ],
    DomainPreset.REAL_ESTATE_HOUSING: [
        FeatureDefinition(name="buyer_budget", feature_type=FeatureType.NUMERIC, unit="INR", min_value=2500000, max_value=50000000),
        FeatureDefinition(name="downpayment_capacity", feature_type=FeatureType.NUMERIC, unit="INR", min_value=500000, max_value=15000000),
        FeatureDefinition(name="preferred_sqft", feature_type=FeatureType.NUMERIC, unit="sqft", min_value=500, max_value=4500),
        FeatureDefinition(name="family_size", feature_type=FeatureType.NUMERIC, min_value=1, max_value=8),
        FeatureDefinition(name="commute_tolerance_km", feature_type=FeatureType.NUMERIC, unit="km", min_value=2, max_value=45),
        FeatureDefinition(name="preferred_district", feature_type=FeatureType.CATEGORICAL, categories=["Downtown Central", "Tech Corridor", "Suburban North", "Greenfield"]),
    ],
}


class DynamicSchemaConfig(BaseModel):
    domain: DomainPreset = DomainPreset.CARDIOLOGY_UCI
    custom_features: list[FeatureDefinition] = Field(default_factory=list)
    simulation_horizon_days: int = Field(default=90, ge=7, le=365)
    intervention_frequency_days: int = Field(default=30, ge=7, le=90)

    def get_features(self) -> list[FeatureDefinition]:
        if self.domain != DomainPreset.CUSTOM and self.domain in DOMAIN_PRESETS:
            return DOMAIN_PRESETS[self.domain]
        return self.custom_features

"""Subscription plan catalog — Phase 3 of the multi-tenant platform plan.

A code-defined catalog, same pattern as feature_modules.py's FEATURE_MODULES and the
Twin Platform's EnvironmentRegistry: these are platform-wide reference data, not
per-organization rows, so a DB table would be unwarranted complexity. An
Organization's `plan_key` (already an existing string column, see models/auth.py)
just needs to match one of the keys here.
"""

PLANS = [
    {
        "key": "researcher",
        "name": "Researcher",
        "monthly_price_inr": 999,
        "included_credits": 2000,
        "agent_quota": 1000,
        "model_tier": "simplified",
        "description": "Individual researchers running occasional experiments.",
    },
    {
        "key": "startup",
        "name": "Startup",
        "monthly_price_inr": 4999,
        "included_credits": 15000,
        "agent_quota": 10000,
        "model_tier": "advanced",
        "description": "Small teams running regular simulations across multiple environments.",
    },
    {
        "key": "enterprise",
        "name": "Enterprise",
        "monthly_price_inr": 25000,
        "included_credits": 100000,
        "agent_quota": 100000,
        "model_tier": "advanced",
        "description": "Full-scale multi-agent deployments across the entire environment catalog.",
    },
    {
        "key": "government",
        "name": "Government",
        "monthly_price_inr": None,  # custom pricing — negotiated, not self-serve
        "included_credits": 500000,
        "agent_quota": 500000,
        "model_tier": "advanced",
        "description": "Municipal and government programs. Custom pricing and onboarding.",
    },
]

PLAN_BY_KEY = {p["key"]: p for p in PLANS}

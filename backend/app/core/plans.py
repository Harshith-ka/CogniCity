"""Subscription plan catalog — Phase 3 of the multi-tenant platform plan.

A code-defined catalog, same pattern as feature_modules.py's FEATURE_MODULES and the
Twin Platform's EnvironmentRegistry: these are platform-wide reference data, not
per-organization rows, so a DB table would be unwarranted complexity. An
Organization's `plan_key` (already an existing string column, see models/auth.py)
just needs to match one of the keys here.
"""

# Environment keys are from the Twin Platform's EnvironmentRegistry (city,
# hospital_ward, airport_terminal, factory_line, university_campus, shopping_mall).
# Module keys are from feature_modules.py's FEATURE_MODULES. Empty list == unrestricted
# (all of them) — same convention Organization.allowed_environments/allowed_modules
# already use everywhere else. Only Enterprise and Government get the unrestricted
# empty list; every other tier is an explicit, deliberately increasing subset.
PLANS = [
    {
        "key": "trial",
        "name": "Free Trial",
        "monthly_price_inr": 0,
        "included_credits": 100,
        "agent_quota": 200,
        "model_tier": "simplified",
        "max_simulation_runs": 3,  # the only plan this applies to — every paid tier is None (unlimited)
        "allowed_environments": ["shopping_mall"],
        "allowed_modules": ["agent_eval", "twin_platform"],  # sandbox + marketplace only, no city-feature tabs
        "description": "Self-signup default. Try the platform with up to 3 simulation runs before subscribing.",
    },
    {
        "key": "researcher",
        "name": "Researcher",
        "monthly_price_inr": 999,
        "included_credits": 2000,
        "agent_quota": 1000,
        "model_tier": "simplified",
        "max_simulation_runs": None,
        "allowed_environments": ["shopping_mall", "hospital_ward", "university_campus"],
        "allowed_modules": ["agent_eval", "twin_platform", "traffic", "weather", "healthcare", "education", "crime", "ai_advisor"],
        "description": "Individual researchers running occasional experiments.",
    },
    {
        "key": "startup",
        "name": "Startup",
        "monthly_price_inr": 4999,
        "included_credits": 15000,
        "agent_quota": 10000,
        "model_tier": "advanced",
        "max_simulation_runs": None,
        "allowed_environments": ["shopping_mall", "hospital_ward", "university_campus", "airport_terminal", "factory_line"],
        "allowed_modules": [
            "agent_eval", "twin_platform", "traffic", "weather", "healthcare", "education", "crime", "ai_advisor",
            "communication", "relationships", "disasters", "pandemic", "social_media", "graph",
            "housing", "news", "culture", "environment", "demographics", "infrastructure", "tourism",
        ],  # everything except government/elections — reserved for Enterprise/Government tiers
        "description": "Small teams running regular simulations across multiple environments.",
    },
    {
        "key": "enterprise",
        "name": "Enterprise",
        "monthly_price_inr": 25000,
        "included_credits": 100000,
        "agent_quota": 100000,
        "model_tier": "advanced",
        "max_simulation_runs": None,
        "allowed_environments": [],  # unrestricted — every environment, including the flagship city
        "allowed_modules": [],       # unrestricted — every feature tab
        "description": "Full-scale multi-agent deployments across the entire environment catalog.",
    },
    {
        "key": "government",
        "name": "Government",
        "monthly_price_inr": None,  # custom pricing — negotiated, not self-serve
        "included_credits": 500000,
        "agent_quota": 500000,
        "model_tier": "advanced",
        "max_simulation_runs": None,
        "allowed_environments": [],  # unrestricted
        "allowed_modules": [],       # unrestricted — includes government/elections, which matter most here
        "description": "Municipal and government programs. Custom pricing and onboarding.",
    },
]

PLAN_BY_KEY = {p["key"]: p for p in PLANS}

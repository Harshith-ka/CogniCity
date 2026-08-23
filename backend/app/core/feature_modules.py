"""Catalog of gateable city-simulation feature modules — the "tabs" an organization's
plan can be scoped to (Traffic, Disasters, AI Advisor, ...). Deliberately excludes the
foundational routes (citizens, economy, core city state, simulation control) — those
stay available to every org, the same way every pricing tier still needs a working
city underneath it. Keys match the router aliases wired up in main.py, which is what
`require_feature()` checks against.
"""

FEATURE_MODULES = [
    # Platform-level capabilities, not city subsystems — gated the same way, but these
    # two sit above the per-environment/per-run checks: agent_eval gates the whole
    # sandbox, twin_platform gates the marketplace catalog itself (browsing AND
    # running), independent of *which* environments an org's allowed_environments
    # then further narrows it to.
    {"key": "agent_eval", "label": "Agent Sandbox", "icon": "🧪"},
    {"key": "twin_platform", "label": "Environment Marketplace", "icon": "🏪"},
    {"key": "traffic", "label": "Traffic", "icon": "🚗"},
    {"key": "government", "label": "Government", "icon": "🏛"},
    {"key": "relationships", "label": "Social", "icon": "🤝"},
    {"key": "communication", "label": "Communications", "icon": "💬"},
    {"key": "disasters", "label": "Disasters", "icon": "🌋"},
    {"key": "pandemic", "label": "Pandemic", "icon": "🦠"},
    {"key": "elections", "label": "Elections", "icon": "🗳"},
    {"key": "social_media", "label": "Social Media", "icon": "📱"},
    {"key": "ai_advisor", "label": "AI Advisor", "icon": "🤖"},
    {"key": "graph", "label": "Knowledge Graph", "icon": "🔗"},
    {"key": "weather", "label": "Weather", "icon": "🌤"},
    {"key": "crime", "label": "Crime", "icon": "🚔"},
    {"key": "healthcare", "label": "Healthcare", "icon": "🏥"},
    {"key": "education", "label": "Education", "icon": "🎓"},
    {"key": "housing", "label": "Housing", "icon": "🏠"},
    {"key": "news", "label": "News", "icon": "📰"},
    {"key": "culture", "label": "Culture", "icon": "🎭"},
    {"key": "environment", "label": "Environment", "icon": "🌳"},
    {"key": "demographics", "label": "Demographics", "icon": "🧑‍🤝‍🧑"},
    {"key": "infrastructure", "label": "Infrastructure", "icon": "⚡"},
    {"key": "tourism", "label": "Tourism", "icon": "✈️"},
]

FEATURE_MODULE_KEYS = {m["key"] for m in FEATURE_MODULES}

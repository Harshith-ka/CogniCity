"""
News & Media Engine: AI news outlets detect city events and generate articles.
Each outlet has political bias, credibility, and sensationalism traits that
color their coverage. Articles influence citizen happiness, stress, and opinions.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.news import NewsOutlet, NewsArticle
from backend.app.services.llm_service import get_llm_service

log = structlog.get_logger()

HEADLINE_TEMPLATES = {
    "disaster": [
        "{type} strikes {district} — {casualties} affected",
        "City reels from devastating {type}",
        "Emergency services overwhelmed as {type} hits",
    ],
    "crime": [
        "Crime wave hits {district}: {count} incidents reported",
        "Police respond to surge in {type} cases",
        "{district} residents demand action on rising crime",
    ],
    "economy": [
        "City GDP {direction} to {amount} — economists {reaction}",
        "Unemployment {direction} to {rate}",
        "Business boom in {district} as new ventures open",
    ],
    "health": [
        "Hospital occupancy reaches {rate} — health officials concerned",
        "{condition} cases on the rise across the city",
        "Mental health crisis: {count} citizens seeking treatment",
    ],
    "politics": [
        "{candidate} leads polls ahead of city election",
        "Election enters {phase} phase — voter turnout projected at {rate}",
        "Policy debate heats up over {topic}",
    ],
    "weather": [
        "{condition} warning issued for the city",
        "Temperature hits {temp}°C — citizens urged to take precautions",
        "{season} weather brings {effect} to daily life",
    ],
    "community": [
        "Community spirit thrives in {district}",
        "Citizens rate happiness at {rate} — {direction} from last month",
        "New education program launches in {district}",
    ],
    "housing": [
        "Housing market update: average rent now {amount}",
        "{count} citizens face eviction as rents rise",
        "New properties available in {district}",
    ],
}

OUTLET_PRESETS = [
    {"name": "City Herald",       "type": "newspaper", "bias": -0.2, "credibility": 0.85, "reach": 0.6, "sensationalism": 0.2},
    {"name": "Metro News 24",     "type": "tv",        "bias": 0.1,  "credibility": 0.75, "reach": 0.8, "sensationalism": 0.4},
    {"name": "The Independent Eye","type": "online",   "bias": -0.4, "credibility": 0.7,  "reach": 0.5, "sensationalism": 0.3},
    {"name": "Liberty Report",    "type": "online",    "bias": 0.5,  "credibility": 0.55, "reach": 0.4, "sensationalism": 0.6},
    {"name": "Community Radio",   "type": "radio",     "bias": 0.0,  "credibility": 0.8,  "reach": 0.3, "sensationalism": 0.1},
    {"name": "Daily Buzz Blog",   "type": "blog",      "bias": 0.2,  "credibility": 0.4,  "reach": 0.3, "sensationalism": 0.8},
]


class NewsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_tick(
        self,
        sim_time: datetime,
        city_context: dict,
    ) -> dict:
        articles_generated = 0

        if random.random() > 0.15:
            return {"articles_generated": 0}

        outlets_result = await self.db.execute(
            select(NewsOutlet).where(NewsOutlet.is_active == True)  # noqa: E712
        )
        outlets = list(outlets_result.scalars().all())
        if not outlets:
            return {"articles_generated": 0}

        outlet = random.choice(outlets)
        category, headline, summary, sentiment = self._generate_article(outlet, city_context)

        impact_happiness = sentiment * 0.01 * (1 - outlet.sensationalism * 0.5)
        impact_stress = -sentiment * 0.01 * (1 + outlet.sensationalism * 0.3)
        impact_opinion = outlet.political_bias * 0.005

        article = NewsArticle(
            outlet_id=outlet.id,
            headline=headline,
            summary=summary,
            category=category,
            sentiment=round(sentiment, 2),
            views=int(100 * outlet.reach * random.uniform(0.5, 2.0)),
            impact_on_happiness=round(impact_happiness, 4),
            impact_on_stress=round(impact_stress, 4),
            impact_on_opinion=round(impact_opinion, 4),
            is_breaking=random.random() < 0.1,
            tags=[category, outlet.outlet_type],
            sim_timestamp=sim_time,
        )

        if city_context.get("active_disasters", 0) > 0:
            article.source_event_type = "disaster"
            article.is_breaking = True
        elif city_context.get("crimes_generated", 0) > 2:
            article.source_event_type = "crime"
        elif city_context.get("active_elections", 0) > 0:
            article.source_event_type = "election"

        self.db.add(article)
        articles_generated += 1

        llm = get_llm_service()
        if llm.is_available and random.random() < 0.3:
            llm_article = await self._generate_llm_article(llm, outlet, city_context, sim_time)
            if llm_article:
                self.db.add(llm_article)
                articles_generated += 1

        await self.db.flush()

        return {"articles_generated": articles_generated}

    def _generate_article(self, outlet: NewsOutlet, context: dict) -> tuple[str, str, str, float]:
        category_weights = {"community": 0.25, "economy": 0.2, "weather": 0.15, "health": 0.1, "crime": 0.1, "housing": 0.1, "politics": 0.05, "disaster": 0.05}

        if context.get("active_disasters", 0) > 0:
            category_weights["disaster"] = 0.5
        if context.get("crimes_generated", 0) > 2:
            category_weights["crime"] = 0.3
        if context.get("active_elections", 0) > 0:
            category_weights["politics"] = 0.3
        if context.get("active_pandemics", 0) > 0:
            category_weights["health"] = 0.35

        cats = list(category_weights.keys())
        probs = list(category_weights.values())
        total = sum(probs)
        probs = [p / total for p in probs]
        category = random.choices(cats, probs)[0]

        templates = HEADLINE_TEMPLATES.get(category, HEADLINE_TEMPLATES["community"])
        template = random.choice(templates)

        placeholders = {
            "district": random.choice(["Downtown", "Riverside", "Uptown", "Midtown", "Harbor", "Old Town", "Tech Park", "Green Valley"]),
            "type": category,
            "casualties": str(random.randint(5, 200)),
            "count": str(random.randint(3, 50)),
            "amount": f"${random.randint(100, 500)}M",
            "rate": f"{random.randint(20, 85)}%",
            "direction": random.choice(["rises", "falls", "holds steady"]),
            "reaction": random.choice(["optimistic", "cautious", "concerned"]),
            "condition": random.choice(["Flu", "Anxiety", "Stress disorder", "Chronic pain"]),
            "candidate": random.choice(["Mayor Chen", "Councilor Park", "Dr. Rivera"]),
            "phase": random.choice(["campaigning", "debate", "voting"]),
            "topic": random.choice(["healthcare", "housing", "education", "crime"]),
            "temp": str(random.randint(-5, 40)),
            "season": random.choice(["Summer", "Winter", "Autumn", "Spring"]),
            "effect": random.choice(["disruptions", "relief", "challenges"]),
        }

        headline = template
        for key, val in placeholders.items():
            headline = headline.replace(f"{{{key}}}", val)

        bias_word = "progressive" if outlet.political_bias < -0.2 else ("conservative" if outlet.political_bias > 0.2 else "balanced")
        sensational = " Sources say this could be the worst in decades." if outlet.sensationalism > 0.5 and random.random() < 0.4 else ""
        summary = f"A {bias_word} perspective on recent {category} developments in the city.{sensational}"

        sentiment = random.uniform(-0.5, 0.5)
        if category in ("disaster", "crime"):
            sentiment -= 0.3
        elif category == "community":
            sentiment += 0.2
        sentiment += outlet.political_bias * 0.1

        return category, headline, summary, round(max(-1, min(1, sentiment)), 2)

    async def _generate_llm_article(
        self, llm, outlet: NewsOutlet, context: dict, sim_time: datetime
    ) -> NewsArticle | None:
        bias_desc = "left-leaning" if outlet.political_bias < -0.2 else ("right-leaning" if outlet.political_bias > 0.2 else "centrist")
        style = "sensationalist" if outlet.sensationalism > 0.5 else "measured"

        prompt = (
            f"Write a short news headline and 1-sentence summary for a city newspaper.\n"
            f"Outlet: {outlet.name} ({bias_desc}, {style} tone)\n"
            f"City context: disasters={context.get('active_disasters', 0)}, "
            f"crimes={context.get('crimes_generated', 0)}, "
            f"elections={context.get('active_elections', 0)}\n"
            f"Respond as JSON: {{\"headline\": \"...\", \"summary\": \"...\", \"category\": \"...\", \"sentiment\": 0.0}}"
        )
        result = await llm.generate_json(prompt)
        if not result:
            return None

        return NewsArticle(
            outlet_id=outlet.id,
            headline=result.get("headline", "Breaking News")[:300],
            summary=result.get("summary", "")[:500],
            category=result.get("category", "community")[:50],
            sentiment=max(-1, min(1, result.get("sentiment", 0))),
            views=int(100 * outlet.reach * random.uniform(0.5, 2.0)),
            is_breaking=random.random() < 0.15,
            tags=[result.get("category", "community"), "llm_generated"],
            sim_timestamp=sim_time,
        )

    async def seed_outlets(self) -> int:
        existing = await self.db.scalar(select(sqlfunc.count(NewsOutlet.id)))
        if existing and existing > 0:
            return 0

        for preset in OUTLET_PRESETS:
            outlet = NewsOutlet(
                name=preset["name"],
                outlet_type=preset["type"],
                political_bias=preset["bias"],
                credibility=preset["credibility"],
                reach=preset["reach"],
                sensationalism=preset["sensationalism"],
            )
            self.db.add(outlet)
        await self.db.flush()
        return len(OUTLET_PRESETS)

    async def get_recent_articles(self, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(NewsArticle).order_by(NewsArticle.sim_timestamp.desc()).limit(limit)
        )
        articles = list(result.scalars().all())
        outlet_ids = {a.outlet_id for a in articles}
        outlets_result = await self.db.execute(
            select(NewsOutlet).where(NewsOutlet.id.in_(outlet_ids))
        )
        outlet_map = {o.id: o for o in outlets_result.scalars().all()}

        return [{
            "id": str(a.id),
            "headline": a.headline,
            "summary": a.summary,
            "category": a.category,
            "sentiment": a.sentiment,
            "outlet": outlet_map[a.outlet_id].name if a.outlet_id in outlet_map else "Unknown",
            "outlet_type": outlet_map[a.outlet_id].outlet_type if a.outlet_id in outlet_map else "",
            "views": a.views,
            "is_breaking": a.is_breaking,
            "tags": a.tags,
            "sim_timestamp": str(a.sim_timestamp),
        } for a in articles]

    async def get_stats(self) -> dict:
        total_articles = await self.db.scalar(select(sqlfunc.count(NewsArticle.id))) or 0
        outlets_count = await self.db.scalar(select(sqlfunc.count(NewsOutlet.id))) or 0
        total_views = await self.db.scalar(select(sqlfunc.sum(NewsArticle.views))) or 0
        breaking = await self.db.scalar(
            select(sqlfunc.count(NewsArticle.id)).where(NewsArticle.is_breaking == True)  # noqa: E712
        ) or 0

        by_cat_result = await self.db.execute(
            select(NewsArticle.category, sqlfunc.count(NewsArticle.id))
            .group_by(NewsArticle.category)
        )
        by_category = {row[0]: row[1] for row in by_cat_result}

        return {
            "total_articles": total_articles,
            "outlets": outlets_count,
            "total_views": total_views,
            "breaking_news": breaking,
            "by_category": by_category,
        }

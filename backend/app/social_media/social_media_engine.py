"""
Advanced Social Media Simulation: Trending topics, virality mechanics,
misinformation spread, opinion influence, and sentiment tracking.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.social_media import (
    TrendingTopic, TopicCategory, OpinionShift,
)
from backend.app.models.communication import SocialMediaPost

log = structlog.get_logger()

TOPIC_TEMPLATES = {
    TopicCategory.NEWS: [
        ("CityNews", "Latest city developments"),
        ("BreakingAlert", "Urgent news update"),
        ("LocalUpdate", "Neighborhood developments"),
    ],
    TopicCategory.ENTERTAINMENT: [
        ("CityVibes", "Entertainment and culture"),
        ("NightlifeScene", "Nightlife updates"),
        ("ArtDistrict", "Art and creativity"),
    ],
    TopicCategory.POLITICS: [
        ("CityPolitics", "Political discussions"),
        ("TaxReform", "Tax policy debates"),
        ("MayorWatch", "Government oversight"),
    ],
    TopicCategory.ECONOMY: [
        ("JobMarket", "Employment opportunities"),
        ("CostOfLiving", "Affordability discussions"),
        ("StartupCity", "Business and innovation"),
    ],
    TopicCategory.HEALTH: [
        ("StayHealthy", "Health and wellness"),
        ("HospitalWatch", "Healthcare system updates"),
        ("MentalHealth", "Wellness awareness"),
    ],
    TopicCategory.DISASTER: [
        ("DisasterAlert", "Emergency information"),
        ("StaySafe", "Safety advisories"),
        ("RebuildTogether", "Recovery efforts"),
    ],
    TopicCategory.SPORTS: [
        ("GameDay", "Sports events"),
        ("CityChampions", "Local team victories"),
        ("FitCity", "Fitness and sports"),
    ],
    TopicCategory.COMMUNITY: [
        ("NeighborHelp", "Community support"),
        ("VolunteerCity", "Volunteering efforts"),
        ("CityPride", "Community pride"),
    ],
}

POST_TEMPLATES = {
    TopicCategory.NEWS: [
        "Just heard about the latest developments in the city! #{hashtag}",
        "Can't believe what's happening downtown. #{hashtag}",
        "Big changes coming to our neighborhood. #{hashtag}",
    ],
    TopicCategory.ENTERTAINMENT: [
        "Great show at the city center tonight! #{hashtag}",
        "The art scene here is thriving! #{hashtag}",
        "Amazing cultural event this weekend. #{hashtag}",
    ],
    TopicCategory.POLITICS: [
        "What do you all think about the new policy? #{hashtag}",
        "City council needs to hear from us. #{hashtag}",
        "Democracy in action today! #{hashtag}",
    ],
    TopicCategory.ECONOMY: [
        "New business opening on Main Street! #{hashtag}",
        "Job market looking interesting lately. #{hashtag}",
        "Prices are changing... #{hashtag}",
    ],
    TopicCategory.HEALTH: [
        "Remember to take care of yourselves! #{hashtag}",
        "Health tip of the day. #{hashtag}",
        "Wellness matters, people! #{hashtag}",
    ],
    TopicCategory.DISASTER: [
        "Stay safe everyone! #{hashtag}",
        "Emergency update for all residents. #{hashtag}",
        "Let's help each other through this. #{hashtag}",
    ],
    TopicCategory.SPORTS: [
        "What a game today! #{hashtag}",
        "Local team making us proud! #{hashtag}",
        "Great weather for outdoor sports! #{hashtag}",
    ],
    TopicCategory.COMMUNITY: [
        "Love this community! #{hashtag}",
        "Neighbors helping neighbors. #{hashtag}",
        "City pride at its finest! #{hashtag}",
    ],
}

MISINFORMATION_TEMPLATES = [
    "URGENT: Unverified reports say {topic}. Share to spread awareness!",
    "I heard from a friend that {topic}. Can anyone confirm?",
    "Sources close to city hall suggest {topic}. Developing story...",
]

MISINFO_TOPICS = [
    "water supply might be contaminated",
    "a major employer is leaving the city",
    "there's a secret construction project",
    "tax rates are going to double",
    "the hospital is closing its emergency room",
    "a celebrity is moving to our neighborhood",
]


class SocialMediaEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_tick(self, sim_time: datetime, city_context: dict | None = None) -> dict:
        stats = {
            "new_posts": 0,
            "trending_topics": 0,
            "opinion_shifts": 0,
            "misinformation_events": 0,
        }

        await self._generate_organic_posts(sim_time, city_context)
        stats["new_posts"] = await self._count_recent_posts()

        await self._update_trending_topics(sim_time)
        stats["trending_topics"] = await self._count_trending()

        await self._process_virality(sim_time)

        if random.random() < 0.02:
            await self._generate_misinformation(sim_time)
            stats["misinformation_events"] += 1

        await self._process_opinion_influence(sim_time)

        await self._decay_topics()

        await self.db.flush()
        return stats

    async def _generate_organic_posts(self, sim_time: datetime, context: dict | None = None) -> None:
        citizens_result = await self.db.execute(
            select(Citizen)
            .where(Citizen.is_alive == True)  # noqa: E712
            .order_by(func.random())
            .limit(10)
        )
        active_citizens = list(citizens_result.scalars().all())

        for citizen in active_citizens:
            personality = citizen.personality_traits or {}
            post_chance = 0.2 + personality.get("extraversion", 0.5) * 0.3
            if random.random() > post_chance:
                continue

            category = self._pick_category_for_citizen(citizen, context)
            templates = POST_TEMPLATES.get(category, POST_TEMPLATES[TopicCategory.COMMUNITY])
            topic_options = TOPIC_TEMPLATES.get(category, TOPIC_TEMPLATES[TopicCategory.COMMUNITY])
            hashtag, topic = random.choice(topic_options)

            content = random.choice(templates).replace("{hashtag}", hashtag)

            sentiment = "neutral"
            if citizen.happiness > 0.7:
                sentiment = "positive"
            elif citizen.happiness < 0.3:
                sentiment = "negative"

            reach = int(5 + personality.get("extraversion", 0.5) * 20 + random.randint(0, 10))

            post = SocialMediaPost(
                author_id=citizen.id,
                content=content,
                sentiment=sentiment,
                likes=random.randint(0, reach // 2),
                shares=random.randint(0, reach // 5),
                reach=reach,
                tags=[hashtag],
                sim_timestamp=sim_time,
            )
            self.db.add(post)

            existing_topic = await self.db.execute(
                select(TrendingTopic).where(TrendingTopic.hashtag == hashtag)
            )
            topic_record = existing_topic.scalar_one_or_none()
            if topic_record:
                topic_record.mention_count += 1
                topic_record.last_seen = sim_time
                sentiment_val = {"positive": 0.3, "neutral": 0.0, "negative": -0.3}.get(sentiment, 0)
                topic_record.sentiment_score = (
                    topic_record.sentiment_score * 0.9 + sentiment_val * 0.1
                )
            else:
                topic_record = TrendingTopic(
                    hashtag=hashtag,
                    topic=topic,
                    category=category,
                    mention_count=1,
                    sentiment_score=0.0,
                    first_seen=sim_time,
                    last_seen=sim_time,
                )
                self.db.add(topic_record)

    def _pick_category_for_citizen(self, citizen: Citizen, context: dict | None = None) -> TopicCategory:
        context = context or {}

        if context.get("active_disasters"):
            if random.random() < 0.4:
                return TopicCategory.DISASTER

        if context.get("active_pandemics"):
            if random.random() < 0.3:
                return TopicCategory.HEALTH

        if context.get("active_elections"):
            if random.random() < 0.3:
                return TopicCategory.POLITICS

        personality = citizen.personality_traits or {}
        weights = {
            TopicCategory.NEWS: 0.15,
            TopicCategory.ENTERTAINMENT: 0.15 + personality.get("openness", 0.5) * 0.1,
            TopicCategory.POLITICS: 0.1 + (1 - personality.get("agreeableness", 0.5)) * 0.1,
            TopicCategory.ECONOMY: 0.15,
            TopicCategory.HEALTH: 0.1 + (1 - citizen.health) * 0.15,
            TopicCategory.SPORTS: 0.1 + personality.get("extraversion", 0.5) * 0.1,
            TopicCategory.COMMUNITY: 0.15 + personality.get("agreeableness", 0.5) * 0.1,
        }

        categories = list(weights.keys())
        probs = list(weights.values())
        return random.choices(categories, weights=probs, k=1)[0]

    async def _update_trending_topics(self, sim_time: datetime) -> None:
        result = await self.db.execute(
            select(TrendingTopic).order_by(TrendingTopic.mention_count.desc())
        )
        topics = list(result.scalars().all())

        for i, topic in enumerate(topics):
            if i < 5 and topic.mention_count >= 3:
                topic.is_trending = True
                topic.virality = min(1.0, topic.mention_count / 50.0)
                if topic.mention_count > topic.peak_mentions:
                    topic.peak_mentions = topic.mention_count
            else:
                topic.is_trending = False

    async def _process_virality(self, sim_time: datetime) -> None:
        result = await self.db.execute(
            select(TrendingTopic).where(TrendingTopic.is_trending == True)  # noqa: E712
        )
        trending = list(result.scalars().all())

        for topic in trending:
            viral_boost = int(topic.virality * random.uniform(1, 5))
            topic.mention_count += viral_boost

    async def _generate_misinformation(self, sim_time: datetime) -> None:
        misinfo_topic = random.choice(MISINFO_TOPICS)
        template = random.choice(MISINFORMATION_TEMPLATES)
        content = template.replace("{topic}", misinfo_topic)

        citizens_result = await self.db.execute(
            select(Citizen)
            .where(Citizen.is_alive == True)  # noqa: E712
            .order_by(func.random())
            .limit(1)
        )
        author = citizens_result.scalar_one_or_none()
        if not author:
            return

        hashtag = "Rumor" + misinfo_topic.split()[0].title()

        post = SocialMediaPost(
            author_id=author.id,
            content=content,
            sentiment="negative",
            likes=0,
            shares=random.randint(2, 10),
            reach=random.randint(20, 50),
            tags=[hashtag, "unverified"],
            sim_timestamp=sim_time,
        )
        self.db.add(post)

        topic = TrendingTopic(
            hashtag=hashtag,
            topic=misinfo_topic,
            category=TopicCategory.NEWS,
            mention_count=random.randint(5, 15),
            sentiment_score=-0.5,
            virality=random.uniform(0.3, 0.7),
            is_misinformation=True,
            first_seen=sim_time,
            last_seen=sim_time,
        )
        self.db.add(topic)

        log.info("misinformation_generated", topic=misinfo_topic)

    async def _process_opinion_influence(self, sim_time: datetime) -> None:
        result = await self.db.execute(
            select(TrendingTopic).where(
                TrendingTopic.is_trending == True,  # noqa: E712
                TrendingTopic.category == TopicCategory.POLITICS,
            )
        )
        political_topics = list(result.scalars().all())

        if not political_topics:
            return

        citizens_result = await self.db.execute(
            select(Citizen)
            .where(Citizen.is_alive == True)  # noqa: E712
            .order_by(func.random())
            .limit(5)
        )
        influenced = list(citizens_result.scalars().all())

        for citizen in influenced:
            personality = citizen.personality_traits or {}
            susceptibility = (
                (1.0 - personality.get("conscientiousness", 0.5)) * 0.4
                + personality.get("agreeableness", 0.5) * 0.3
                + personality.get("openness", 0.5) * 0.3
            )

            if random.random() > susceptibility * 0.3:
                continue

            topic = random.choice(political_topics)
            old_opinion = citizen.political_opinion or 0.5
            shift = topic.sentiment_score * susceptibility * 0.05
            new_opinion = max(0.0, min(1.0, old_opinion + shift))
            citizen.political_opinion = new_opinion

            if abs(new_opinion - old_opinion) > 0.01:
                opinion_record = OpinionShift(
                    citizen_id=citizen.id,
                    topic=topic.topic,
                    old_opinion=round(old_opinion, 4),
                    new_opinion=round(new_opinion, 4),
                    influence_source=f"trending:#{topic.hashtag}",
                    sim_timestamp=sim_time,
                )
                self.db.add(opinion_record)

    async def _decay_topics(self) -> None:
        result = await self.db.execute(select(TrendingTopic))
        topics = list(result.scalars().all())

        for topic in topics:
            topic.mention_count = max(0, int(topic.mention_count * 0.95))
            topic.virality = max(0.0, topic.virality * 0.98)

            if topic.mention_count <= 0 and not topic.is_trending:
                await self.db.delete(topic)

    async def _count_recent_posts(self) -> int:
        result = await self.db.execute(select(func.count(SocialMediaPost.id)))
        return result.scalar() or 0

    async def _count_trending(self) -> int:
        result = await self.db.execute(
            select(func.count(TrendingTopic.id)).where(
                TrendingTopic.is_trending == True  # noqa: E712
            )
        )
        return result.scalar() or 0

    async def trigger_topic_from_event(
        self, hashtag: str, topic: str, category: TopicCategory,
        sentiment: float = 0.0, initial_mentions: int = 20,
    ) -> TrendingTopic:
        now = datetime.utcnow()
        trending = TrendingTopic(
            hashtag=hashtag,
            topic=topic,
            category=category,
            mention_count=initial_mentions,
            sentiment_score=sentiment,
            virality=0.5,
            is_trending=True,
            first_seen=now,
            last_seen=now,
        )
        self.db.add(trending)
        await self.db.flush()
        log.info("topic_triggered", hashtag=hashtag, category=category.value)
        return trending

    async def get_trending(self) -> list[dict]:
        result = await self.db.execute(
            select(TrendingTopic)
            .where(TrendingTopic.is_trending == True)  # noqa: E712
            .order_by(TrendingTopic.mention_count.desc())
        )
        topics = list(result.scalars().all())
        return [
            {
                "hashtag": t.hashtag,
                "topic": t.topic,
                "category": t.category.value,
                "mentions": t.mention_count,
                "sentiment": round(t.sentiment_score, 3),
                "virality": round(t.virality, 3),
                "is_misinformation": t.is_misinformation,
                "peak_mentions": t.peak_mentions,
            }
            for t in topics
        ]

    async def get_opinion_shifts(self, limit: int = 50) -> list[dict]:
        result = await self.db.execute(
            select(OpinionShift)
            .order_by(OpinionShift.created_at.desc())
            .limit(limit)
        )
        shifts = list(result.scalars().all())
        return [
            {
                "citizen_id": str(s.citizen_id),
                "topic": s.topic,
                "old_opinion": s.old_opinion,
                "new_opinion": s.new_opinion,
                "influence_source": s.influence_source,
            }
            for s in shifts
        ]

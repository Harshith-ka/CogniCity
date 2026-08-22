"""
Communication Engine: Manages multi-agent conversations, gossip propagation,
social media, and emergency alerts between citizens.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.communication import (
    Conversation, Message, SocialMediaComment, SocialMediaPost,
    ChannelType, MessageSentiment,
)
from backend.app.models.social_media import TrendingTopic

log = structlog.get_logger()

TRENDING_OPENERS = [
    "Have you seen what's going on with #{hashtag}? {topic}",
    "Everyone's talking about #{hashtag} right now.",
    "Did you catch the news about {topic}?",
    "I can't stop thinking about #{hashtag} — {topic}",
    "So apparently {topic}. Wild, right?",
]
TRENDING_REACTIONS = [
    "Yeah, I saw that. Kind of worried about it honestly.",
    "I know, it's all anyone's posting about.",
    "Hopefully it blows over soon.",
    "Right? I have so many thoughts on that.",
    "I'm trying not to think about it too much.",
]
TRENDING_POST_TEMPLATES = [
    "Can't stop thinking about {topic}. #{hashtag}",
    "Everyone's talking about #{hashtag} today. {topic}",
    "My take on the {topic} situation: we'll get through this. #{hashtag}",
    "Just saw the news — {topic}. #{hashtag}",
    "Is it just me or is #{hashtag} all anyone can talk about?",
]
COMMENT_TEMPLATES = {
    "positive": [
        "Love this!", "So true.", "This made my day.", "Couldn't agree more.",
        "Same here!", "This is great news.",
    ],
    "neutral": [
        "Interesting.", "Good to know.", "Noted.", "Huh, didn't know that.",
        "Thanks for sharing.",
    ],
    "negative": [
        "Not great news honestly.", "This is concerning.", "Hope it gets better soon.",
        "I'm worried about this.", "Ugh, not again.",
    ],
}

CONVERSATION_TOPICS = {
    "casual": [
        "How's the weather today?",
        "Did you watch the game last night?",
        "Have you tried that new restaurant downtown?",
        "I heard they're building a new park nearby.",
        "The traffic was terrible this morning.",
        "My kids are doing well in school.",
        "I'm thinking of taking a vacation soon.",
        "The neighborhood has changed a lot lately.",
    ],
    "work": [
        "The project deadline is coming up.",
        "Did you see the quarterly results?",
        "We need to hire more staff.",
        "The new policy changes are interesting.",
        "I'm thinking of asking for a raise.",
        "The office renovation looks great.",
        "Our team meeting went well today.",
    ],
    "gossip": [
        "Did you hear about {name}?",
        "Apparently, {name} is looking for a new job.",
        "I heard {name} got promoted.",
        "{name} was seen at the hospital yesterday.",
        "People are saying {name} started a new business.",
        "{name} seems really stressed lately.",
        "I think {name} is moving to a new district.",
    ],
    "crisis": [
        "Have you heard about the emergency?",
        "We need to stay safe.",
        "The authorities are handling the situation.",
        "I hope everyone is okay.",
        "We should check on our neighbors.",
        "The news is reporting serious damage.",
    ],
    "economy": [
        "Prices keep going up.",
        "The job market is tough right now.",
        "I'm worried about my savings.",
        "Business has been slow lately.",
        "The new tax policy is unfair.",
        "I'm thinking of investing in something.",
    ],
}

SOCIAL_MEDIA_TEMPLATES = [
    "Having a great day at {location}! #citylife",
    "Just started my new job as a {occupation}. Excited! #newbeginnings",
    "The traffic in {district} is unbearable today. #commute",
    "Beautiful sunset over the city tonight. #cityviews",
    "Concerned about the recent {event} in our area. Stay safe everyone.",
    "Just had an amazing meal at {location}. Highly recommend!",
    "Working hard today. {mood} #worklife",
    "Missing my friends. Need to plan a get-together soon. #social",
    "The city really needs better public transport. #infrastructure",
    "Grateful for another good day. Happiness is {happiness}% today.",
]


class CommunicationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_conversation(
        self,
        participant_ids: list[uuid.UUID],
        channel: ChannelType,
        topic_category: str = "casual",
        sim_time: datetime | None = None,
        location: str | None = None,
    ) -> Conversation:
        topics = CONVERSATION_TOPICS.get(topic_category, CONVERSATION_TOPICS["casual"])
        topic = random.choice(topics)

        conv = Conversation(
            channel=channel,
            topic=topic,
            location=location,
            participant_ids=[str(pid) for pid in participant_ids],
            started_at=sim_time or datetime.utcnow(),
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        sim_time: datetime,
        sentiment: MessageSentiment = MessageSentiment.NEUTRAL,
        importance: float = 0.3,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            sentiment=sentiment,
            importance=importance,
            sim_timestamp=sim_time,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def get_hot_topic(self) -> TrendingTopic | None:
        """Current #1 trending topic, if any, for citizens to reference in dialogue."""
        result = await self.db.execute(
            select(TrendingTopic)
            .where(TrendingTopic.is_trending == True)  # noqa: E712
            .order_by(desc(TrendingTopic.mention_count))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def generate_conversation(
        self,
        citizens: list[Citizen],
        sim_time: datetime,
        topic_category: str = "casual",
        hot_topic: TrendingTopic | None = None,
    ) -> Conversation | None:
        """Generate a natural conversation between 2-4 citizens. If hot_topic is given,
        the conversation opens with citizens discussing it instead of a generic line."""
        if len(citizens) < 2:
            return None

        participants = random.sample(citizens, min(len(citizens), random.randint(2, 4)))
        participant_ids = [c.id for c in participants]

        channel = random.choice([
            ChannelType.FACE_TO_FACE,
            ChannelType.PHONE_CALL,
            ChannelType.TEXT_MESSAGE,
        ])

        conv = await self.start_conversation(
            participant_ids=participant_ids,
            channel=channel,
            topic_category=topic_category,
            sim_time=sim_time,
        )

        topics = CONVERSATION_TOPICS.get(topic_category, CONVERSATION_TOPICS["casual"])
        num_messages = random.randint(2, 6)

        if hot_topic:
            conv.topic = f"#{hot_topic.hashtag}: {hot_topic.topic}"

        for i in range(num_messages):
            speaker = random.choice(participants)
            other = random.choice([c for c in participants if c.id != speaker.id])

            if hot_topic and i < 2:
                bank = TRENDING_OPENERS if i == 0 else TRENDING_REACTIONS
                content = random.choice(bank).format(hashtag=hot_topic.hashtag, topic=hot_topic.topic)
            else:
                template = random.choice(topics)
                content = template.replace("{name}", other.name)

            sentiment = self._compute_sentiment(speaker)

            await self.send_message(
                conversation_id=conv.id,
                sender_id=speaker.id,
                content=content,
                sim_time=sim_time,
                sentiment=sentiment,
            )

        conv.is_active = False
        conv.ended_at = sim_time
        await self.db.flush()

        log.debug(
            "conversation_generated",
            participants=len(participants),
            messages=num_messages,
            channel=channel.value,
            hot_topic=hot_topic.hashtag if hot_topic else None,
        )
        return conv

    async def propagate_gossip(
        self,
        source_citizen: Citizen,
        about_citizen: Citizen,
        gossip_content: str,
        sim_time: datetime,
        spread_probability: float = 0.3,
    ) -> list[Conversation]:
        """Spread gossip from one citizen to nearby citizens."""
        result = await self.db.execute(
            select(Citizen)
            .where(
                Citizen.is_alive == True,  # noqa: E712
                Citizen.id != source_citizen.id,
                Citizen.id != about_citizen.id,
            )
            .limit(20)
        )
        potential_targets = list(result.scalars().all())

        conversations = []
        for target in potential_targets:
            if random.random() < spread_probability:
                conv = await self.start_conversation(
                    participant_ids=[source_citizen.id, target.id],
                    channel=ChannelType.GOSSIP,
                    topic_category="gossip",
                    sim_time=sim_time,
                )

                content = gossip_content.replace("{name}", about_citizen.name)
                await self.send_message(
                    conversation_id=conv.id,
                    sender_id=source_citizen.id,
                    content=content,
                    sim_time=sim_time,
                    sentiment=MessageSentiment.NEUTRAL,
                    importance=0.4,
                )

                response_templates = [
                    f"Oh really? I didn't know that about {about_citizen.name}.",
                    f"That's interesting. I'll keep that in mind.",
                    f"I had a feeling something was going on with {about_citizen.name}.",
                    f"Thanks for telling me. I hope they're okay.",
                ]
                await self.send_message(
                    conversation_id=conv.id,
                    sender_id=target.id,
                    content=random.choice(response_templates),
                    sim_time=sim_time,
                    sentiment=MessageSentiment.NEUTRAL,
                )

                conv.is_active = False
                conv.ended_at = sim_time
                conversations.append(conv)

        await self.db.flush()
        return conversations

    async def broadcast_emergency_alert(
        self,
        message: str,
        sim_time: datetime,
    ) -> Conversation:
        """Broadcast an emergency alert to all citizens."""
        result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True).limit(500)  # noqa: E712
        )
        citizens = list(result.scalars().all())
        citizen_ids = [c.id for c in citizens]

        conv = Conversation(
            channel=ChannelType.EMERGENCY_ALERT,
            topic=message,
            participant_ids=[str(cid) for cid in citizen_ids],
            started_at=sim_time,
            ended_at=sim_time,
            is_active=False,
        )
        self.db.add(conv)
        await self.db.flush()

        alert_msg = Message(
            conversation_id=conv.id,
            sender_id=citizen_ids[0] if citizen_ids else uuid.uuid4(),
            content=f"[EMERGENCY ALERT] {message}",
            sentiment=MessageSentiment.NEGATIVE,
            importance=1.0,
            sim_timestamp=sim_time,
        )
        self.db.add(alert_msg)

        for citizen in citizens:
            citizen.stress = min(1.0, citizen.stress + 0.15)

        await self.db.flush()
        log.info("emergency_alert_broadcast", message=message, recipients=len(citizens))
        return conv

    async def generate_social_media_post(
        self,
        citizen: Citizen,
        sim_time: datetime,
        context: dict | None = None,
        hot_topic: TrendingTopic | None = None,
    ) -> SocialMediaPost:
        """Generate a social media post for a citizen. If hot_topic is given, the post
        is often about that topic instead of a generic template."""
        ctx = context or {}

        if hot_topic and random.random() < 0.6:
            template = random.choice(TRENDING_POST_TEMPLATES)
            content = template.format(hashtag=hot_topic.hashtag, topic=hot_topic.topic)
            tags = [hot_topic.hashtag]
        else:
            template = random.choice(SOCIAL_MEDIA_TEMPLATES)
            content = template.format(
                location=ctx.get("location", "the city"),
                occupation=citizen.occupation,
                district=ctx.get("district", "Downtown"),
                event=ctx.get("event", "events"),
                mood="Feeling great!" if citizen.happiness > 0.6 else "Feeling a bit down.",
                happiness=int(citizen.happiness * 100),
            )
            tags = ctx.get("tags", ["citylife"])

        sentiment = self._compute_sentiment(citizen)

        post = SocialMediaPost(
            author_id=citizen.id,
            content=content,
            sentiment=sentiment,
            likes=random.randint(0, 50),
            shares=random.randint(0, 10),
            reach=random.randint(10, 200),
            tags=tags,
            sim_timestamp=sim_time,
        )
        self.db.add(post)

        if hot_topic:
            hot_topic.mention_count += 1
            hot_topic.last_seen = sim_time

        await self.db.flush()
        return post

    async def generate_comments(
        self,
        citizens: list[Citizen],
        sim_time: datetime,
        max_posts: int = 5,
        comment_probability: float = 0.25,
    ) -> int:
        """Have citizens react with short comments under recent popular posts."""
        if not citizens:
            return 0

        result = await self.db.execute(
            select(SocialMediaPost).order_by(desc(SocialMediaPost.sim_timestamp)).limit(max_posts)
        )
        posts = list(result.scalars().all())

        created = 0
        for post in posts:
            if random.random() > comment_probability:
                continue
            commenter = random.choice(citizens)
            if commenter.id == post.author_id:
                continue

            sentiment = self._compute_sentiment(commenter)
            bank = COMMENT_TEMPLATES.get(sentiment.value, COMMENT_TEMPLATES["neutral"])
            comment = SocialMediaComment(
                post_id=post.id,
                author_id=commenter.id,
                content=random.choice(bank),
                sentiment=sentiment,
                likes=random.randint(0, 15),
                sim_timestamp=sim_time,
            )
            self.db.add(comment)
            post.likes += 1
            created += 1

        if created:
            await self.db.flush()
        return created

    async def process_tick_conversations(
        self,
        citizens: list[Citizen],
        sim_time: datetime,
        conversation_probability: float = 0.05,
        social_media_probability: float = 0.02,
    ) -> dict:
        """Process conversations for a simulation tick."""
        stats = {"conversations": 0, "social_posts": 0, "gossip_chains": 0, "comments": 0}

        hot_topic = await self.get_hot_topic()

        if len(citizens) >= 2 and random.random() < conversation_probability * len(citizens):
            num_convos = max(1, int(len(citizens) * conversation_probability))
            for _ in range(min(num_convos, 10)):
                topic = random.choice(["casual", "work", "economy"])
                use_hot_topic = hot_topic if random.random() < 0.4 else None
                conv = await self.generate_conversation(citizens, sim_time, topic, hot_topic=use_hot_topic)
                if conv:
                    stats["conversations"] += 1

        for citizen in citizens:
            if random.random() < social_media_probability:
                use_hot_topic = hot_topic if random.random() < 0.35 else None
                await self.generate_social_media_post(citizen, sim_time, hot_topic=use_hot_topic)
                stats["social_posts"] += 1

        if random.random() < 0.01 and len(citizens) >= 3:
            source = random.choice(citizens)
            about = random.choice([c for c in citizens if c.id != source.id])
            gossip_templates = CONVERSATION_TOPICS["gossip"]
            gossip_content = random.choice(gossip_templates)
            chains = await self.propagate_gossip(source, about, gossip_content, sim_time, 0.15)
            stats["gossip_chains"] = len(chains)

        stats["comments"] = await self.generate_comments(citizens, sim_time)

        return stats

    async def get_recent_conversations(self, limit: int = 20) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation).order_by(desc(Conversation.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def get_citizen_conversations(
        self, citizen_id: uuid.UUID, limit: int = 10
    ) -> list[dict]:
        result = await self.db.execute(
            select(Conversation)
            .order_by(desc(Conversation.created_at))
            .limit(limit * 3)
        )
        conversations = list(result.scalars().all())

        citizen_convos = []
        cid_str = str(citizen_id)
        for conv in conversations:
            if cid_str in conv.participant_ids:
                msgs_result = await self.db.execute(
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                    .order_by(Message.sim_timestamp)
                )
                messages = list(msgs_result.scalars().all())

                citizen_convos.append({
                    "id": str(conv.id),
                    "channel": conv.channel.value,
                    "topic": conv.topic,
                    "participants": conv.participant_ids,
                    "messages": [
                        {
                            "sender_id": str(m.sender_id),
                            "content": m.content,
                            "sentiment": m.sentiment.value,
                            "timestamp": m.sim_timestamp.isoformat(),
                        }
                        for m in messages
                    ],
                })
                if len(citizen_convos) >= limit:
                    break

        return citizen_convos

    async def get_social_feed(self, limit: int = 30, include_comments: bool = True) -> list[dict]:
        result = await self.db.execute(
            select(SocialMediaPost)
            .order_by(desc(SocialMediaPost.sim_timestamp))
            .limit(limit)
        )
        posts = list(result.scalars().all())

        comments_by_post: dict[uuid.UUID, list[SocialMediaComment]] = {}
        if include_comments and posts:
            post_ids = [p.id for p in posts]
            comments_result = await self.db.execute(
                select(SocialMediaComment)
                .where(SocialMediaComment.post_id.in_(post_ids))
                .order_by(SocialMediaComment.sim_timestamp)
            )
            for c in comments_result.scalars().all():
                comments_by_post.setdefault(c.post_id, []).append(c)

        return [
            {
                "id": str(p.id),
                "author_id": str(p.author_id),
                "content": p.content,
                "sentiment": p.sentiment.value,
                "likes": p.likes,
                "shares": p.shares,
                "tags": p.tags,
                "timestamp": p.sim_timestamp.isoformat(),
                "comments": [
                    {
                        "id": str(c.id),
                        "author_id": str(c.author_id),
                        "content": c.content,
                        "sentiment": c.sentiment.value,
                        "likes": c.likes,
                        "timestamp": c.sim_timestamp.isoformat(),
                    }
                    for c in comments_by_post.get(p.id, [])
                ],
            }
            for p in posts
        ]

    def _compute_sentiment(self, citizen: Citizen) -> MessageSentiment:
        mood_score = citizen.happiness - citizen.stress
        if mood_score > 0.2:
            return MessageSentiment.POSITIVE
        elif mood_score < -0.2:
            return MessageSentiment.NEGATIVE
        return MessageSentiment.NEUTRAL

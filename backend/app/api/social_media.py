"""Phase 3 API: Advanced social media simulation endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.social_media.social_media_engine import SocialMediaEngine
from backend.app.models.social_media import TopicCategory

router = APIRouter(prefix="/api/social-media", tags=["social_media"])


class TriggerTopicRequest(BaseModel):
    hashtag: str
    topic: str
    category: str = "news"
    sentiment: float = 0.0
    initial_mentions: int = 20


@router.get("/trending")
async def get_trending(db: AsyncSession = Depends(get_db)):
    engine = SocialMediaEngine(db)
    return await engine.get_trending()


@router.get("/opinion-shifts")
async def get_opinion_shifts(
    limit: int = 50, db: AsyncSession = Depends(get_db)
):
    engine = SocialMediaEngine(db)
    return await engine.get_opinion_shifts(limit=limit)


@router.post("/trigger-topic")
async def trigger_topic(
    req: TriggerTopicRequest, db: AsyncSession = Depends(get_db)
):
    try:
        category = TopicCategory(req.category)
    except ValueError:
        category = TopicCategory.NEWS

    engine = SocialMediaEngine(db)
    topic = await engine.trigger_topic_from_event(
        hashtag=req.hashtag,
        topic=req.topic,
        category=category,
        sentiment=req.sentiment,
        initial_mentions=req.initial_mentions,
    )
    await db.commit()
    return {
        "hashtag": topic.hashtag,
        "topic": topic.topic,
        "category": topic.category.value,
        "mentions": topic.mention_count,
    }


@router.get("/categories")
async def get_categories():
    return [c.value for c in TopicCategory]

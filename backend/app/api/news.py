"""Phase 5 API: News & Media endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.news.news_engine import NewsEngine
from backend.app.models.news import NewsOutlet

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/stats")
async def news_stats(db: AsyncSession = Depends(get_db)):
    engine = NewsEngine(db)
    return await engine.get_stats()


@router.get("/articles")
async def recent_articles(limit: int = 20, db: AsyncSession = Depends(get_db)):
    engine = NewsEngine(db)
    return await engine.get_recent_articles(limit=limit)


@router.get("/outlets")
async def list_outlets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsOutlet))
    return [{
        "id": str(o.id),
        "name": o.name,
        "type": o.outlet_type,
        "political_bias": o.political_bias,
        "credibility": o.credibility,
        "reach": o.reach,
        "sensationalism": o.sensationalism,
        "is_active": o.is_active,
    } for o in result.scalars().all()]

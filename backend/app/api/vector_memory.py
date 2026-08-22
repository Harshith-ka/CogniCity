"""Phase 4 API: Vector memory search endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.memory.vector_store import get_vector_store

router = APIRouter(prefix="/api/vector-memory", tags=["vector_memory"])


class SearchRequest(BaseModel):
    query: str
    citizen_id: str | None = None
    limit: int = 10
    min_score: float = 0.5


class ContextSearchRequest(BaseModel):
    citizen_id: str
    current_activity: str
    current_location: str | None = None
    emotional_state: str | None = None
    limit: int = 5


@router.get("/status")
async def vector_store_status():
    store = get_vector_store()
    stats = await store.get_stats()
    return stats


@router.post("/search")
async def search_memories(req: SearchRequest):
    store = get_vector_store()
    import uuid as uuid_mod
    citizen_uuid = uuid_mod.UUID(req.citizen_id) if req.citizen_id else None
    results = await store.search_similar(
        query=req.query,
        citizen_id=citizen_uuid,
        limit=req.limit,
        min_score=req.min_score,
    )
    return {"results": results, "count": len(results)}


@router.post("/context-search")
async def context_search(req: ContextSearchRequest):
    store = get_vector_store()
    import uuid as uuid_mod
    results = await store.search_by_context(
        citizen_id=uuid_mod.UUID(req.citizen_id),
        current_activity=req.current_activity,
        current_location=req.current_location,
        emotional_state=req.emotional_state,
        limit=req.limit,
    )
    return {"results": results, "count": len(results)}


@router.get("/citizen/{citizen_id}/summary")
async def citizen_memory_summary(citizen_id: str, topic: str = "recent events"):
    store = get_vector_store()
    import uuid as uuid_mod
    summary = await store.get_citizen_memory_summary(
        citizen_id=uuid_mod.UUID(citizen_id),
        topic=topic,
    )
    return {"summary": summary}

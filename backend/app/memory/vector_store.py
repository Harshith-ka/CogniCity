"""
Qdrant Vector Memory Store: Semantic memory search using vector embeddings.
Citizens store memory embeddings and retrieve contextually relevant memories
using vector similarity instead of just recency/importance.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog

from backend.app.core.config import settings
from backend.app.services.llm_service import get_llm_service

log = structlog.get_logger()

_qdrant_client = None
COLLECTION_NAME = "citizen_memories"

PROVIDER_EMBEDDING_DIMS = {
    "openai": 1536,
    "anthropic": 1536,
    "ollama": 768,
}


def _get_embedding_dim() -> int:
    if settings.embedding_dim > 0:
        return settings.embedding_dim
    return PROVIDER_EMBEDDING_DIMS.get(settings.llm_provider, 768)


def _get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            _ensure_collection(_qdrant_client)
        except Exception as e:
            log.warning("qdrant_unavailable", error=str(e))
    return _qdrant_client


def _ensure_collection(client) -> None:
    from qdrant_client.models import Distance, VectorParams

    dim = _get_embedding_dim()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=dim,
                distance=Distance.COSINE,
            ),
        )
        log.info("qdrant_collection_created", name=COLLECTION_NAME, dim=dim)
    else:
        info = client.get_collection(COLLECTION_NAME)
        existing_dim = info.config.params.vectors.size
        if existing_dim != dim:
            log.warning(
                "qdrant_dim_mismatch",
                existing=existing_dim, expected=dim,
                hint="Delete collection to recreate with correct dimension",
            )


class VectorMemoryStore:
    def __init__(self):
        self.llm = get_llm_service()

    @property
    def is_available(self) -> bool:
        return _get_qdrant_client() is not None and self.llm.is_available

    async def store_memory(
        self,
        citizen_id: uuid.UUID,
        memory_id: uuid.UUID,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        sim_time: datetime | None = None,
        location: str | None = None,
    ) -> bool:
        client = _get_qdrant_client()
        if not client:
            return False

        embedding = await self.llm.get_embedding(content)
        if not embedding:
            return False

        from qdrant_client.models import PointStruct

        point = PointStruct(
            id=str(memory_id),
            vector=embedding,
            payload={
                "citizen_id": str(citizen_id),
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "emotional_valence": emotional_valence,
                "sim_time": sim_time.isoformat() if sim_time else None,
                "location": location,
            },
        )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point],
        )
        return True

    async def search_similar(
        self,
        query: str,
        citizen_id: uuid.UUID | None = None,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[dict]:
        client = _get_qdrant_client()
        if not client:
            return []

        embedding = await self.llm.get_embedding(query)
        if not embedding:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_filter = None
        if citizen_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="citizen_id",
                        match=MatchValue(value=str(citizen_id)),
                    )
                ]
            )

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=min_score,
        )

        return [
            {
                "id": hit.id,
                "score": round(hit.score, 4),
                "content": hit.payload.get("content", ""),
                "memory_type": hit.payload.get("memory_type", ""),
                "importance": hit.payload.get("importance", 0),
                "emotional_valence": hit.payload.get("emotional_valence", 0),
                "sim_time": hit.payload.get("sim_time"),
                "location": hit.payload.get("location"),
            }
            for hit in results
        ]

    async def search_by_context(
        self,
        citizen_id: uuid.UUID,
        current_activity: str,
        current_location: str | None = None,
        emotional_state: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        parts = [f"Currently doing: {current_activity}"]
        if current_location:
            parts.append(f"at {current_location}")
        if emotional_state:
            parts.append(f"feeling {emotional_state}")
        query = ". ".join(parts)

        return await self.search_similar(
            query=query,
            citizen_id=citizen_id,
            limit=limit,
            min_score=0.4,
        )

    async def get_citizen_memory_summary(
        self,
        citizen_id: uuid.UUID,
        topic: str,
        limit: int = 5,
    ) -> str:
        memories = await self.search_similar(
            query=topic,
            citizen_id=citizen_id,
            limit=limit,
        )
        if not memories:
            return "No relevant memories found."

        parts = []
        for m in memories:
            relevance = f"(relevance: {m['score']:.0%})"
            parts.append(f"- {m['content']} {relevance}")

        return "\n".join(parts)

    async def bulk_store(
        self,
        memories: list[dict],
    ) -> int:
        client = _get_qdrant_client()
        if not client:
            return 0

        contents = [m["content"] for m in memories]
        embeddings = await self.llm.get_embeddings_batch(contents)
        if not embeddings:
            return 0

        from qdrant_client.models import PointStruct

        points = []
        for mem, emb in zip(memories, embeddings):
            point = PointStruct(
                id=str(mem.get("memory_id", uuid.uuid4())),
                vector=emb,
                payload={
                    "citizen_id": str(mem["citizen_id"]),
                    "content": mem["content"],
                    "memory_type": mem.get("memory_type", "episodic"),
                    "importance": mem.get("importance", 0.5),
                    "emotional_valence": mem.get("emotional_valence", 0.0),
                    "sim_time": mem.get("sim_time"),
                    "location": mem.get("location"),
                },
            )
            points.append(point)

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        return len(points)

    async def delete_citizen_memories(self, citizen_id: uuid.UUID) -> bool:
        client = _get_qdrant_client()
        if not client:
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="citizen_id",
                        match=MatchValue(value=str(citizen_id)),
                    )
                ]
            ),
        )
        return True

    async def get_stats(self) -> dict:
        client = _get_qdrant_client()
        if not client:
            return {"available": False}

        try:
            info = client.get_collection(COLLECTION_NAME)
            return {
                "available": True,
                "collection": COLLECTION_NAME,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


_store: VectorMemoryStore | None = None


def get_vector_store() -> VectorMemoryStore:
    global _store
    if _store is None:
        _store = VectorMemoryStore()
    return _store

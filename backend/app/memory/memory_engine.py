"""
Memory Engine: Manages episodic, semantic, relationship, and emotional memory for citizens.
Uses PostgreSQL for persistent storage and Qdrant for vector similarity search.
"""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.memory import EpisodicMemory, EmotionalState, MemoryType

log = structlog.get_logger()


class MemoryEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_memory(
        self,
        citizen_id: uuid.UUID,
        content: str,
        memory_type: MemoryType,
        sim_time: datetime,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        location: str | None = None,
        involved_citizens: list[str] | None = None,
    ) -> EpisodicMemory:
        memory = EpisodicMemory(
            citizen_id=citizen_id,
            content=content,
            memory_type=memory_type,
            summary=content[:200],
            importance=importance,
            emotional_valence=emotional_valence,
            location=location,
            involved_citizens=involved_citizens or [],
            sim_timestamp=sim_time,
        )
        self.db.add(memory)
        await self.db.flush()
        return memory

    async def recall_recent(
        self,
        citizen_id: uuid.UUID,
        limit: int = 10,
        memory_type: MemoryType | None = None,
    ) -> list[EpisodicMemory]:
        query = (
            select(EpisodicMemory)
            .where(EpisodicMemory.citizen_id == citizen_id)
            .order_by(desc(EpisodicMemory.sim_timestamp))
            .limit(limit)
        )
        if memory_type:
            query = query.where(EpisodicMemory.memory_type == memory_type)

        result = await self.db.execute(query)
        memories = list(result.scalars().all())

        for mem in memories:
            mem.access_count += 1
            mem.last_accessed = datetime.utcnow()

        return memories

    async def recall_important(
        self,
        citizen_id: uuid.UUID,
        min_importance: float = 0.7,
        limit: int = 5,
    ) -> list[EpisodicMemory]:
        query = (
            select(EpisodicMemory)
            .where(
                EpisodicMemory.citizen_id == citizen_id,
                EpisodicMemory.importance >= min_importance,
            )
            .order_by(desc(EpisodicMemory.importance))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_emotional_state(
        self,
        citizen_id: uuid.UUID,
        sim_time: datetime,
        fear: float = 0.0,
        anger: float = 0.0,
        joy: float = 0.5,
        sadness: float = 0.0,
        trust: float = 0.5,
        surprise: float = 0.0,
        stress: float = 0.3,
        confidence: float = 0.6,
        trigger: str | None = None,
    ) -> EmotionalState:
        state = EmotionalState(
            citizen_id=citizen_id,
            fear=fear,
            anger=anger,
            joy=joy,
            sadness=sadness,
            trust=trust,
            surprise=surprise,
            stress=stress,
            confidence=confidence,
            trigger=trigger,
            sim_timestamp=sim_time,
        )
        self.db.add(state)
        await self.db.flush()
        return state

    async def get_current_emotional_state(
        self, citizen_id: uuid.UUID
    ) -> EmotionalState | None:
        query = (
            select(EmotionalState)
            .where(EmotionalState.citizen_id == citizen_id)
            .order_by(desc(EmotionalState.sim_timestamp))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def build_context_summary(
        self, citizen_id: uuid.UUID, max_memories: int = 15
    ) -> str:
        recent = await self.recall_recent(citizen_id, limit=max_memories)
        important = await self.recall_important(citizen_id, limit=5)
        emotional = await self.get_current_emotional_state(citizen_id)

        seen_ids = set()
        all_memories = []
        for m in important + recent:
            if m.id not in seen_ids:
                seen_ids.add(m.id)
                all_memories.append(m)

        parts = []
        if all_memories:
            parts.append("Recent experiences:")
            for m in all_memories[:max_memories]:
                parts.append(f"  - [{m.memory_type.value}] {m.summary}")

        if emotional:
            parts.append(
                f"Current emotions: joy={emotional.joy:.1f}, stress={emotional.stress:.1f}, "
                f"fear={emotional.fear:.1f}, anger={emotional.anger:.1f}, "
                f"confidence={emotional.confidence:.1f}"
            )

        return "\n".join(parts)

"""
Relationship Engine: Manages social networks — friendships, family, colleagues,
trust scores, and relationship evolution.

Uses PostgreSQL for persistence (with optional Neo4j integration for graph queries).
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.relationship import Relationship, RelationshipType

log = structlog.get_logger()


class RelationshipEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_relationship(
        self,
        citizen_a_id: uuid.UUID,
        citizen_b_id: uuid.UUID,
        rel_type: RelationshipType,
        trust: float = 0.5,
        closeness: float = 0.3,
    ) -> Relationship:
        existing = await self.get_relationship(citizen_a_id, citizen_b_id)
        if existing:
            existing.relationship_type = rel_type
            existing.trust_score = trust
            existing.closeness = closeness
            await self.db.flush()
            return existing

        rel = Relationship(
            citizen_a_id=citizen_a_id,
            citizen_b_id=citizen_b_id,
            relationship_type=rel_type,
            trust_score=trust,
            closeness=closeness,
        )
        self.db.add(rel)
        await self.db.flush()
        return rel

    async def get_relationship(
        self,
        citizen_a_id: uuid.UUID,
        citizen_b_id: uuid.UUID,
    ) -> Relationship | None:
        result = await self.db.execute(
            select(Relationship).where(
                or_(
                    and_(
                        Relationship.citizen_a_id == citizen_a_id,
                        Relationship.citizen_b_id == citizen_b_id,
                    ),
                    and_(
                        Relationship.citizen_a_id == citizen_b_id,
                        Relationship.citizen_b_id == citizen_a_id,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_citizen_relationships(
        self, citizen_id: uuid.UUID
    ) -> list[Relationship]:
        result = await self.db.execute(
            select(Relationship).where(
                or_(
                    Relationship.citizen_a_id == citizen_id,
                    Relationship.citizen_b_id == citizen_id,
                )
            )
        )
        return list(result.scalars().all())

    async def get_friends(self, citizen_id: uuid.UUID) -> list[uuid.UUID]:
        rels = await self.get_citizen_relationships(citizen_id)
        friends = []
        for r in rels:
            if r.relationship_type in (RelationshipType.FRIEND, RelationshipType.FAMILY, RelationshipType.ROMANTIC):
                other_id = r.citizen_b_id if r.citizen_a_id == citizen_id else r.citizen_a_id
                friends.append(other_id)
        return friends

    async def record_interaction(
        self,
        citizen_a_id: uuid.UUID,
        citizen_b_id: uuid.UUID,
        positive: bool,
        sim_time: datetime,
    ) -> Relationship:
        rel = await self.get_relationship(citizen_a_id, citizen_b_id)

        if not rel:
            rel = await self.create_relationship(
                citizen_a_id,
                citizen_b_id,
                RelationshipType.ACQUAINTANCE,
            )

        rel.interaction_count += 1
        rel.last_interaction = sim_time

        if positive:
            rel.trust_score = min(1.0, rel.trust_score + 0.05)
            rel.closeness = min(1.0, rel.closeness + 0.03)
        else:
            rel.trust_score = max(0.0, rel.trust_score - 0.08)
            rel.closeness = max(0.0, rel.closeness - 0.02)

        if rel.closeness > 0.7 and rel.relationship_type == RelationshipType.ACQUAINTANCE:
            rel.relationship_type = RelationshipType.FRIEND
        elif rel.trust_score < 0.2 and rel.relationship_type != RelationshipType.FAMILY:
            rel.relationship_type = RelationshipType.RIVAL

        await self.db.flush()
        return rel

    async def seed_relationships(
        self,
        citizens: list[Citizen],
        avg_connections: int = 5,
    ) -> int:
        """Generate initial social connections between citizens."""
        created = 0

        for citizen in citizens:
            num_connections = max(1, random.randint(avg_connections - 2, avg_connections + 3))
            potential = [c for c in citizens if c.id != citizen.id]
            connections = random.sample(potential, min(num_connections, len(potential)))

            for other in connections:
                existing = await self.get_relationship(citizen.id, other.id)
                if existing:
                    continue

                rel_type = random.choices(
                    [
                        RelationshipType.FRIEND,
                        RelationshipType.COLLEAGUE,
                        RelationshipType.NEIGHBOR,
                        RelationshipType.ACQUAINTANCE,
                        RelationshipType.FAMILY,
                    ],
                    weights=[0.3, 0.25, 0.2, 0.15, 0.1],
                )[0]

                trust = round(random.uniform(0.3, 0.9), 2)
                closeness = round(random.uniform(0.1, 0.8), 2)

                if rel_type == RelationshipType.FAMILY:
                    trust = max(trust, 0.6)
                    closeness = max(closeness, 0.5)

                await self.create_relationship(
                    citizen.id, other.id, rel_type, trust, closeness
                )
                created += 1

        await self.db.flush()
        log.info("relationships_seeded", created=created)
        return created

    async def get_social_network_stats(self) -> dict:
        result = await self.db.execute(select(Relationship))
        rels = list(result.scalars().all())

        by_type: dict[str, int] = {}
        total_trust = 0.0
        total_closeness = 0.0

        for r in rels:
            rtype = r.relationship_type.value
            by_type[rtype] = by_type.get(rtype, 0) + 1
            total_trust += r.trust_score
            total_closeness += r.closeness

        count = max(len(rels), 1)
        return {
            "total_relationships": len(rels),
            "by_type": by_type,
            "avg_trust": round(total_trust / count, 4),
            "avg_closeness": round(total_closeness / count, 4),
        }

    async def get_citizen_social_graph(self, citizen_id: uuid.UUID) -> dict:
        rels = await self.get_citizen_relationships(citizen_id)
        nodes = [{"id": str(citizen_id), "label": "self"}]
        edges = []

        for r in rels:
            other_id = r.citizen_b_id if r.citizen_a_id == citizen_id else r.citizen_a_id

            other_result = await self.db.execute(
                select(Citizen).where(Citizen.id == other_id)
            )
            other = other_result.scalar_one_or_none()
            name = other.name if other else str(other_id)[:8]

            nodes.append({
                "id": str(other_id),
                "label": name,
            })
            edges.append({
                "from": str(citizen_id),
                "to": str(other_id),
                "type": r.relationship_type.value,
                "trust": r.trust_score,
                "closeness": r.closeness,
                "interactions": r.interaction_count,
            })

        return {"nodes": nodes, "edges": edges}

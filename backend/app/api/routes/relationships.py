"""API routes for social relationships."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.communication.relationship_engine import RelationshipEngine
from backend.app.core.database import get_db

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/stats")
async def relationship_stats(db: AsyncSession = Depends(get_db)):
    engine = RelationshipEngine(db)
    return await engine.get_social_network_stats()


@router.get("/citizens/{citizen_id}")
async def citizen_relationships(
    citizen_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    engine = RelationshipEngine(db)
    rels = await engine.get_citizen_relationships(citizen_id)
    return [
        {
            "id": str(r.id),
            "other_id": str(r.citizen_b_id if r.citizen_a_id == citizen_id else r.citizen_a_id),
            "type": r.relationship_type.value,
            "trust": r.trust_score,
            "closeness": r.closeness,
            "interactions": r.interaction_count,
        }
        for r in rels
    ]


@router.get("/citizens/{citizen_id}/graph")
async def citizen_social_graph(
    citizen_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    engine = RelationshipEngine(db)
    return await engine.get_citizen_social_graph(citizen_id)


@router.post("/seed")
async def seed_relationships(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.app.models.citizen import Citizen

    result = await db.execute(
        select(Citizen).where(Citizen.is_alive == True).limit(200)  # noqa: E712
    )
    citizens = list(result.scalars().all())

    engine = RelationshipEngine(db)
    count = await engine.seed_relationships(citizens)
    return {"relationships_created": count}

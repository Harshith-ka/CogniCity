"""API routes for communication, conversations, and social media."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.communication.communication_engine import CommunicationEngine
from backend.app.core.database import get_db

router = APIRouter(prefix="/communication", tags=["communication"])


class BroadcastRequest(BaseModel):
    message: str


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    engine = CommunicationEngine(db)
    convos = await engine.get_recent_conversations(limit)
    return [
        {
            "id": str(c.id),
            "channel": c.channel.value,
            "topic": c.topic,
            "participants": c.participant_ids,
            "location": c.location,
            "is_active": c.is_active,
            "started_at": c.started_at.isoformat() if c.started_at else None,
        }
        for c in convos
    ]


@router.get("/citizens/{citizen_id}/conversations")
async def get_citizen_conversations(
    citizen_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    engine = CommunicationEngine(db)
    return await engine.get_citizen_conversations(citizen_id, limit)


@router.get("/social-feed")
async def get_social_feed(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    engine = CommunicationEngine(db)
    return await engine.get_social_feed(limit)


@router.post("/emergency-alert")
async def broadcast_emergency(
    req: BroadcastRequest,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime

    engine = CommunicationEngine(db)
    conv = await engine.broadcast_emergency_alert(req.message, datetime.utcnow())
    return {
        "id": str(conv.id),
        "message": req.message,
        "recipients": len(conv.participant_ids),
    }

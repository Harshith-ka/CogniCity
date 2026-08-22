"""API routes for economy."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.economy.economy_engine import EconomyEngine
from backend.app.models.economy import Business, Transaction

router = APIRouter(prefix="/economy", tags=["economy"])


@router.get("/businesses")
async def list_businesses(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Business)
    if active_only:
        query = query.where(Business.is_open == True)  # noqa: E712

    result = await db.execute(query)
    businesses = list(result.scalars().all())
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "type": b.business_type.value,
            "balance": round(b.balance, 2),
            "revenue": round(b.revenue, 2),
            "max_employees": b.max_employees,
            "is_open": b.is_open,
        }
        for b in businesses
    ]


@router.get("/transactions")
async def list_transactions(
    citizen_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction).order_by(Transaction.created_at.desc()).limit(limit)
    if citizen_id:
        query = query.where(Transaction.citizen_id == citizen_id)

    result = await db.execute(query)
    txs = list(result.scalars().all())
    return [
        {
            "id": str(t.id),
            "citizen_id": str(t.citizen_id),
            "type": t.transaction_type.value,
            "amount": t.amount,
            "description": t.description,
            "sim_timestamp": t.sim_timestamp.isoformat() if t.sim_timestamp else None,
        }
        for t in txs
    ]


@router.get("/stats")
async def economy_stats(db: AsyncSession = Depends(get_db)):
    engine = EconomyEngine(db)
    return await engine.get_economy_stats()

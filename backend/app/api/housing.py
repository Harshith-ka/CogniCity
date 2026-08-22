"""Phase 5 API: Housing & Real Estate endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.housing.housing_engine import HousingEngine
from backend.app.models.housing import Property, PropertyTransaction

router = APIRouter(prefix="/api/housing", tags=["housing"])


@router.get("/stats")
async def housing_stats(db: AsyncSession = Depends(get_db)):
    engine = HousingEngine(db)
    return await engine.get_stats()


@router.get("/properties")
async def list_properties(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Property).order_by(Property.market_value.desc()).limit(limit)
    )
    return [{
        "id": str(p.id),
        "name": p.name,
        "type": p.property_type,
        "market_value": p.market_value,
        "monthly_rent": p.monthly_rent,
        "size_sqm": p.size_sqm,
        "quality": p.quality,
        "condition": p.condition,
        "is_occupied": p.is_occupied,
        "is_for_rent": p.is_for_rent,
        "is_for_sale": p.is_for_sale,
    } for p in result.scalars().all()]


@router.get("/transactions")
async def recent_transactions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PropertyTransaction).order_by(PropertyTransaction.sim_timestamp.desc()).limit(limit)
    )
    return [{
        "id": str(t.id),
        "property_id": str(t.property_id),
        "type": t.transaction_type,
        "amount": t.amount,
        "sim_timestamp": str(t.sim_timestamp),
    } for t in result.scalars().all()]

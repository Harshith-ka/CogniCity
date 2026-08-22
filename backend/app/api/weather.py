"""Phase 5 API: Weather endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.weather import WeatherState

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current")
async def current_weather(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherState).where(WeatherState.is_current == True).limit(1)  # noqa: E712
    )
    w = result.scalar_one_or_none()
    if not w:
        return {"condition": "clear", "temperature_c": 22, "season": "summer"}
    return {
        "condition": w.condition,
        "temperature_c": w.temperature_c,
        "humidity": w.humidity,
        "wind_speed_kmh": w.wind_speed_kmh,
        "visibility_km": w.visibility_km,
        "air_quality_index": w.air_quality_index,
        "uv_index": w.uv_index,
        "precipitation_mm": w.precipitation_mm,
        "season": w.season,
        "happiness_modifier": w.happiness_modifier,
        "health_modifier": w.health_modifier,
        "traffic_modifier": w.traffic_modifier,
        "crime_modifier": w.crime_modifier,
    }


@router.get("/history")
async def weather_history(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherState).order_by(WeatherState.sim_timestamp.desc()).limit(limit)
    )
    return [{
        "condition": w.condition,
        "temperature_c": w.temperature_c,
        "humidity": w.humidity,
        "season": w.season,
        "sim_timestamp": str(w.sim_timestamp),
    } for w in result.scalars().all()]

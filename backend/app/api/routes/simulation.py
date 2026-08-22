"""API routes for simulation control."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.engine.simulation import SimulationEngine
from backend.app.schemas.simulation import SimulationControl, SimulationState, TickResult

router = APIRouter(prefix="/simulation", tags=["simulation"])

_engine: SimulationEngine | None = None


def get_simulation_engine() -> SimulationEngine:
    if _engine is None:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    return _engine


def set_simulation_engine(engine: SimulationEngine) -> None:
    global _engine
    _engine = engine


@router.get("/status", response_model=SimulationState)
async def get_status(engine: SimulationEngine = Depends(get_simulation_engine)):
    metrics = await engine.get_metrics()
    return SimulationState(
        status=engine.status,
        current_tick=engine.current_tick,
        sim_time=engine.sim_time,
        population=metrics.get("population", 0),
        total_gdp=metrics.get("total_gdp", 0),
        avg_happiness=metrics.get("avg_happiness", 0),
        avg_health=metrics.get("avg_health", 0),
        unemployment_rate=metrics.get("unemployment_rate", 0),
    )


@router.post("/control")
async def control_simulation(
    cmd: SimulationControl,
    engine: SimulationEngine = Depends(get_simulation_engine),
):
    match cmd.action:
        case "start":
            await engine.start()
            return {"status": "started"}
        case "stop":
            await engine.stop()
            return {"status": "stopped"}
        case "pause":
            await engine.pause()
            return {"status": "paused"}
        case "resume":
            await engine.resume()
            return {"status": "resumed"}
        case "step":
            steps = cmd.steps or 1
            results = await engine.step(steps)
            return {"status": "stepped", "results": [r.model_dump() for r in results]}
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown action: {cmd.action}")


@router.get("/ticks", response_model=list[TickResult])
async def get_recent_ticks(
    count: int = 50,
    engine: SimulationEngine = Depends(get_simulation_engine),
):
    return engine.get_recent_ticks(count)

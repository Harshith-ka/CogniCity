"""Phase 3 API: Election system endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.elections.election_engine import ElectionEngine

router = APIRouter(prefix="/api/elections", tags=["elections"])


class StartElectionRequest(BaseModel):
    name: str = "City Mayor Election"
    candidate_count: int = 4


@router.get("/")
async def get_elections(db: AsyncSession = Depends(get_db)):
    engine = ElectionEngine(db)
    return await engine.get_elections()


@router.post("/start")
async def start_election(
    req: StartElectionRequest, db: AsyncSession = Depends(get_db)
):
    engine = ElectionEngine(db)
    from datetime import datetime
    election = await engine.start_election(
        name=req.name,
        sim_time=datetime.utcnow(),
        candidate_count=req.candidate_count,
    )
    await db.commit()
    return {
        "id": str(election.id),
        "name": election.name,
        "phase": election.phase.value,
        "total_voters": election.total_voters,
    }

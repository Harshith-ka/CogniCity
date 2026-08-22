"""Phase 4 API: Neo4j graph query endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.services.graph_service import get_graph_service

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/status")
async def graph_status():
    svc = get_graph_service()
    stats = await svc.get_graph_stats()
    return stats


@router.post("/sync")
async def sync_graph(db: AsyncSession = Depends(get_db)):
    svc = get_graph_service()
    if not svc.is_available:
        return {"error": "Neo4j not available"}
    await svc.setup_constraints()
    result = await svc.sync_all_from_postgres(db)
    return result


@router.get("/shortest-path/{citizen_a_id}/{citizen_b_id}")
async def shortest_path(citizen_a_id: str, citizen_b_id: str):
    svc = get_graph_service()
    import uuid
    result = await svc.find_shortest_path(
        uuid.UUID(citizen_a_id), uuid.UUID(citizen_b_id)
    )
    if result is None:
        return {"error": "No path found"}
    return result


@router.get("/influencers")
async def influencers(limit: int = 10):
    svc = get_graph_service()
    return await svc.find_influencers(limit=limit)


@router.get("/influence-path/{source_id}/{target_id}")
async def influence_path(source_id: str, target_id: str):
    svc = get_graph_service()
    import uuid
    result = await svc.find_influence_path(
        uuid.UUID(source_id), uuid.UUID(target_id)
    )
    if result is None:
        return {"error": "No influence path found"}
    return result


@router.get("/communities")
async def communities(min_size: int = 3):
    svc = get_graph_service()
    return await svc.find_communities(min_size=min_size)


@router.get("/neighborhood/{citizen_id}")
async def neighborhood(citizen_id: str, depth: int = 2):
    svc = get_graph_service()
    import uuid
    return await svc.get_citizen_neighborhood(uuid.UUID(citizen_id), depth=depth)


@router.get("/district-connections")
async def district_connections():
    svc = get_graph_service()
    return await svc.get_district_connections()

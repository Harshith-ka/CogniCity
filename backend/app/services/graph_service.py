"""
Neo4j Graph Service: Advanced relationship graph queries —
community detection, influence paths, shortest social distance,
cluster analysis. Syncs PostgreSQL relationships to Neo4j.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from backend.app.core.config import settings

log = structlog.get_logger()

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        try:
            from neo4j import AsyncGraphDatabase
            _driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        except Exception as e:
            log.warning("neo4j_unavailable", error=str(e))
    return _driver


class GraphService:
    @property
    def is_available(self) -> bool:
        return _get_driver() is not None

    async def setup_constraints(self) -> None:
        driver = _get_driver()
        if not driver:
            return
        async with driver.session() as session:
            await session.run(
                "CREATE CONSTRAINT citizen_id IF NOT EXISTS "
                "FOR (c:Citizen) REQUIRE c.citizen_id IS UNIQUE"
            )
            log.info("neo4j_constraints_created")

    async def sync_citizen(
        self,
        citizen_id: uuid.UUID,
        name: str,
        age: int,
        occupation: str,
        district: str | None = None,
        personality: dict | None = None,
    ) -> None:
        driver = _get_driver()
        if not driver:
            return
        async with driver.session() as session:
            await session.run(
                """
                MERGE (c:Citizen {citizen_id: $cid})
                SET c.name = $name,
                    c.age = $age,
                    c.occupation = $occupation,
                    c.district = $district,
                    c.openness = $openness,
                    c.conscientiousness = $conscientiousness,
                    c.extraversion = $extraversion,
                    c.agreeableness = $agreeableness,
                    c.neuroticism = $neuroticism
                """,
                cid=str(citizen_id),
                name=name,
                age=age,
                occupation=occupation,
                district=district or "",
                openness=(personality or {}).get("openness", 0.5),
                conscientiousness=(personality or {}).get("conscientiousness", 0.5),
                extraversion=(personality or {}).get("extraversion", 0.5),
                agreeableness=(personality or {}).get("agreeableness", 0.5),
                neuroticism=(personality or {}).get("neuroticism", 0.5),
            )

    async def sync_relationship(
        self,
        citizen_a_id: uuid.UUID,
        citizen_b_id: uuid.UUID,
        rel_type: str,
        trust: float,
        closeness: float,
        interactions: int,
    ) -> None:
        driver = _get_driver()
        if not driver:
            return
        async with driver.session() as session:
            await session.run(
                """
                MATCH (a:Citizen {citizen_id: $a_id})
                MATCH (b:Citizen {citizen_id: $b_id})
                MERGE (a)-[r:KNOWS]->(b)
                SET r.type = $rel_type,
                    r.trust = $trust,
                    r.closeness = $closeness,
                    r.interactions = $interactions,
                    r.weight = $closeness * $trust
                """,
                a_id=str(citizen_a_id),
                b_id=str(citizen_b_id),
                rel_type=rel_type,
                trust=trust,
                closeness=closeness,
                interactions=interactions,
            )

    async def sync_all_from_postgres(self, db) -> dict:
        from sqlalchemy import select
        from backend.app.models.citizen import Citizen
        from backend.app.models.relationship import Relationship
        from backend.app.models.city import District, Location

        driver = _get_driver()
        if not driver:
            return {"synced_citizens": 0, "synced_relationships": 0}

        citizens_result = await db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        citizens = list(citizens_result.scalars().all())

        location_districts: dict[str, str] = {}
        loc_result = await db.execute(
            select(Location, District).join(District, Location.district_id == District.id)
        )
        for loc, dist in loc_result.all():
            location_districts[str(loc.id)] = dist.name

        for citizen in citizens:
            district_name = location_districts.get(str(citizen.home_location_id), "")
            await self.sync_citizen(
                citizen_id=citizen.id,
                name=citizen.name,
                age=citizen.age,
                occupation=citizen.occupation or "unemployed",
                district=district_name,
                personality=citizen.personality_traits,
            )

        rels_result = await db.execute(select(Relationship))
        relationships = list(rels_result.scalars().all())

        for rel in relationships:
            await self.sync_relationship(
                citizen_a_id=rel.citizen_a_id,
                citizen_b_id=rel.citizen_b_id,
                rel_type=rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type),
                trust=rel.trust_score,
                closeness=rel.closeness,
                interactions=rel.interaction_count,
            )

        stats = {
            "synced_citizens": len(citizens),
            "synced_relationships": len(relationships),
        }
        log.info("neo4j_sync_complete", **stats)
        return stats

    async def find_shortest_path(
        self, citizen_a_id: uuid.UUID, citizen_b_id: uuid.UUID
    ) -> dict | None:
        driver = _get_driver()
        if not driver:
            return None
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH path = shortestPath(
                    (a:Citizen {citizen_id: $a_id})-[:KNOWS*..10]-(b:Citizen {citizen_id: $b_id})
                )
                RETURN [n IN nodes(path) | {id: n.citizen_id, name: n.name}] AS path_nodes,
                       length(path) AS distance
                """,
                a_id=str(citizen_a_id),
                b_id=str(citizen_b_id),
            )
            record = await result.single()
            if not record:
                return None
            return {
                "path": record["path_nodes"],
                "distance": record["distance"],
            }

    async def find_communities(self, min_size: int = 3) -> list[dict]:
        driver = _get_driver()
        if not driver:
            return []
        async with driver.session() as session:
            result = await session.run(
                """
                CALL gds.louvain.stream({
                    nodeProjection: 'Citizen',
                    relationshipProjection: {
                        KNOWS: { type: 'KNOWS', properties: 'weight' }
                    },
                    relationshipWeightProperty: 'weight'
                })
                YIELD nodeId, communityId
                WITH communityId, collect(gds.util.asNode(nodeId).name) AS members
                WHERE size(members) >= $min_size
                RETURN communityId, members, size(members) AS size
                ORDER BY size DESC
                """,
                min_size=min_size,
            )
            communities = []
            async for record in result:
                communities.append({
                    "community_id": record["communityId"],
                    "members": record["members"],
                    "size": record["size"],
                })
            return communities

    async def find_influencers(self, limit: int = 10) -> list[dict]:
        driver = _get_driver()
        if not driver:
            return []
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Citizen)-[r:KNOWS]-()
                WITH c, count(r) AS connections,
                     avg(r.trust) AS avg_trust,
                     avg(r.closeness) AS avg_closeness
                RETURN c.citizen_id AS id, c.name AS name,
                       c.occupation AS occupation,
                       connections,
                       round(avg_trust * 1000) / 1000 AS avg_trust,
                       round(avg_closeness * 1000) / 1000 AS avg_closeness,
                       round(connections * avg_trust * avg_closeness * 1000) / 1000 AS influence_score
                ORDER BY influence_score DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            influencers = []
            async for record in result:
                influencers.append(dict(record))
            return influencers

    async def find_influence_path(
        self, source_id: uuid.UUID, target_id: uuid.UUID
    ) -> dict | None:
        driver = _get_driver()
        if not driver:
            return None
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH path = shortestPath(
                    (a:Citizen {citizen_id: $src})-[:KNOWS*..6]-(b:Citizen {citizen_id: $tgt})
                )
                WITH path,
                     [r IN relationships(path) | r.trust * r.closeness] AS weights
                RETURN [n IN nodes(path) | {id: n.citizen_id, name: n.name}] AS nodes,
                       weights,
                       reduce(s = 1.0, w IN weights | s * w) AS total_influence,
                       length(path) AS hops
                """,
                src=str(source_id),
                tgt=str(target_id),
            )
            record = await result.single()
            if not record:
                return None
            return {
                "nodes": record["nodes"],
                "weights": [round(w, 4) for w in record["weights"]],
                "total_influence": round(record["total_influence"], 6),
                "hops": record["hops"],
            }

    async def get_citizen_neighborhood(
        self, citizen_id: uuid.UUID, depth: int = 2
    ) -> dict:
        driver = _get_driver()
        if not driver:
            return {"nodes": [], "edges": []}
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (center:Citizen {citizen_id: $cid})
                CALL apoc.path.subgraphAll(center, {
                    maxLevel: $depth,
                    relationshipFilter: 'KNOWS'
                })
                YIELD nodes, relationships
                RETURN
                    [n IN nodes | {id: n.citizen_id, name: n.name, occupation: n.occupation}] AS nodes,
                    [r IN relationships | {
                        from: startNode(r).citizen_id,
                        to: endNode(r).citizen_id,
                        type: r.type,
                        trust: r.trust,
                        closeness: r.closeness
                    }] AS edges
                """,
                cid=str(citizen_id),
                depth=depth,
            )
            record = await result.single()
            if not record:
                return {"nodes": [], "edges": []}
            return {
                "nodes": record["nodes"],
                "edges": record["edges"],
            }

    async def get_district_connections(self) -> list[dict]:
        driver = _get_driver()
        if not driver:
            return []
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (a:Citizen)-[r:KNOWS]-(b:Citizen)
                WHERE a.district <> '' AND b.district <> '' AND a.district <> b.district
                WITH a.district AS from_district, b.district AS to_district, count(r) AS connections
                RETURN from_district, to_district, connections
                ORDER BY connections DESC
                """
            )
            inter_district = []
            async for record in result:
                inter_district.append(dict(record))
            return inter_district

    async def get_graph_stats(self) -> dict:
        driver = _get_driver()
        if not driver:
            return {"available": False}
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Citizen)
                OPTIONAL MATCH (c)-[r:KNOWS]-()
                WITH count(DISTINCT c) AS nodes,
                     count(r) / 2 AS edges,
                     avg(count(r)) AS avg_degree
                RETURN nodes, edges
                """
            )
            record = await result.single()
            if not record:
                return {"available": True, "nodes": 0, "edges": 0}

            degree_result = await session.run(
                """
                MATCH (c:Citizen)-[r:KNOWS]-()
                WITH c, count(r) AS degree
                RETURN avg(degree) AS avg_degree,
                       max(degree) AS max_degree,
                       min(degree) AS min_degree
                """
            )
            deg_record = await degree_result.single()

            return {
                "available": True,
                "nodes": record["nodes"],
                "edges": record["edges"],
                "avg_degree": round(deg_record["avg_degree"] or 0, 2) if deg_record else 0,
                "max_degree": deg_record["max_degree"] or 0 if deg_record else 0,
                "min_degree": deg_record["min_degree"] or 0 if deg_record else 0,
            }


_graph_service: GraphService | None = None


def get_graph_service() -> GraphService:
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service

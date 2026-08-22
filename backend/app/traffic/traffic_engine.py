"""
Dynamic Traffic Engine: Manages transportation, routing, congestion,
and travel times across the city road network.
"""

from __future__ import annotations

import heapq
import math
import random
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen, TransportPreference
from backend.app.models.city import Location, District
from backend.app.models.traffic import RoadSegment, TransitRoute, TripRecord, VehicleType

log = structlog.get_logger()

SPEED_KMH = {
    VehicleType.PEDESTRIAN: 5.0,
    VehicleType.BIKE: 15.0,
    VehicleType.CAR: 40.0,
    VehicleType.BUS: 25.0,
    VehicleType.METRO: 60.0,
    VehicleType.EMERGENCY: 80.0,
    VehicleType.TRUCK: 30.0,
}

COST_PER_KM = {
    VehicleType.PEDESTRIAN: 0.0,
    VehicleType.BIKE: 0.0,
    VehicleType.CAR: 0.15,
    VehicleType.BUS: 0.05,
    VehicleType.METRO: 0.08,
    VehicleType.EMERGENCY: 0.0,
    VehicleType.TRUCK: 0.25,
}

TRANSPORT_PREF_MAP = {
    TransportPreference.WALKING: VehicleType.PEDESTRIAN,
    TransportPreference.CAR: VehicleType.CAR,
    TransportPreference.METRO: VehicleType.METRO,
    TransportPreference.BUS: VehicleType.BUS,
    TransportPreference.BIKE: VehicleType.BIKE,
}


class TrafficNode:
    """A node in the road network graph."""

    def __init__(self, node_id: str, x: float, y: float, name: str = ""):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.name = name
        self.edges: list[TrafficEdge] = []


class TrafficEdge:
    """An edge in the road network graph."""

    def __init__(
        self,
        from_node: TrafficNode,
        to_node: TrafficNode,
        distance: float,
        speed_limit: float = 50.0,
        lanes: int = 2,
        capacity: int = 100,
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.distance = distance
        self.speed_limit = speed_limit
        self.lanes = lanes
        self.capacity = capacity
        self.current_vehicles = 0

    @property
    def congestion(self) -> float:
        if self.capacity == 0:
            return 1.0
        return min(1.0, self.current_vehicles / self.capacity)

    @property
    def effective_speed(self) -> float:
        congestion_factor = max(0.1, 1.0 - self.congestion * 0.8)
        return self.speed_limit * congestion_factor

    @property
    def travel_time_minutes(self) -> float:
        speed_ms = self.effective_speed * 1000 / 3600
        if speed_ms <= 0:
            return float("inf")
        return (self.distance / speed_ms) / 60.0


class RoadNetwork:
    """Graph-based road network for the city."""

    def __init__(self):
        self.nodes: dict[str, TrafficNode] = {}
        self.edges: list[TrafficEdge] = []

    def add_node(self, node_id: str, x: float, y: float, name: str = "") -> TrafficNode:
        node = TrafficNode(node_id, x, y, name)
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        speed_limit: float = 50.0,
        lanes: int = 2,
        capacity: int = 100,
    ) -> TrafficEdge | None:
        if from_id not in self.nodes or to_id not in self.nodes:
            return None

        from_node = self.nodes[from_id]
        to_node = self.nodes[to_id]
        distance = math.sqrt(
            (from_node.x - to_node.x) ** 2 + (from_node.y - to_node.y) ** 2
        )

        edge = TrafficEdge(from_node, to_node, distance, speed_limit, lanes, capacity)
        self.edges.append(edge)
        from_node.edges.append(edge)

        reverse = TrafficEdge(to_node, from_node, distance, speed_limit, lanes, capacity)
        self.edges.append(reverse)
        to_node.edges.append(reverse)

        return edge

    def find_nearest_node(self, x: float, y: float) -> TrafficNode | None:
        best = None
        best_dist = float("inf")
        for node in self.nodes.values():
            d = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
            if d < best_dist:
                best_dist = d
                best = node
        return best

    def shortest_path(self, start_id: str, end_id: str) -> tuple[list[str], float]:
        """Dijkstra's algorithm using travel time as edge weight."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return [], float("inf")

        if start_id == end_id:
            return [start_id], 0.0

        dist: dict[str, float] = {nid: float("inf") for nid in self.nodes}
        dist[start_id] = 0.0
        prev: dict[str, str | None] = {nid: None for nid in self.nodes}
        pq: list[tuple[float, str]] = [(0.0, start_id)]

        while pq:
            d, u = heapq.heappop(pq)
            if u == end_id:
                break
            if d > dist[u]:
                continue
            for edge in self.nodes[u].edges:
                v = edge.to_node.node_id
                new_dist = dist[u] + edge.travel_time_minutes
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if dist[end_id] == float("inf"):
            return [], float("inf")

        path = []
        current: str | None = end_id
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()

        return path, dist[end_id]


class TrafficEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.network = RoadNetwork()
        self._initialized = False
        self._rush_hour_factor = 1.0

    async def initialize_network(self) -> None:
        """Build the road network from districts and locations."""
        if self._initialized:
            return

        districts_result = await self.db.execute(select(District))
        districts = list(districts_result.scalars().all())

        locations_result = await self.db.execute(select(Location))
        locations = list(locations_result.scalars().all())

        for district in districts:
            self.network.add_node(
                f"district_{district.id}",
                district.center_x,
                district.center_y,
                district.name,
            )

        for loc in locations:
            self.network.add_node(
                f"loc_{loc.id}",
                loc.x,
                loc.y,
                loc.name,
            )

        for d1 in districts:
            for d2 in districts:
                if d1.id == d2.id:
                    continue
                dist = math.sqrt(
                    (d1.center_x - d2.center_x) ** 2 + (d1.center_y - d2.center_y) ** 2
                )
                if dist < 3000:
                    self.network.add_edge(
                        f"district_{d1.id}",
                        f"district_{d2.id}",
                        speed_limit=60.0,
                        lanes=3,
                        capacity=200,
                    )

        for loc in locations:
            if loc.district_id:
                self.network.add_edge(
                    f"loc_{loc.id}",
                    f"district_{loc.district_id}",
                    speed_limit=40.0,
                    lanes=2,
                    capacity=100,
                )

            for other_loc in locations:
                if loc.id == other_loc.id:
                    continue
                if loc.district_id == other_loc.district_id and loc.district_id is not None:
                    dist = math.sqrt((loc.x - other_loc.x) ** 2 + (loc.y - other_loc.y) ** 2)
                    if dist < 1000:
                        self.network.add_edge(
                            f"loc_{loc.id}",
                            f"loc_{other_loc.id}",
                            speed_limit=30.0,
                            capacity=50,
                        )

        self._initialized = True
        log.info(
            "traffic_network_initialized",
            nodes=len(self.network.nodes),
            edges=len(self.network.edges),
        )

    def update_rush_hour(self, hour: int) -> None:
        """Adjust congestion based on time of day."""
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            self._rush_hour_factor = 2.0
        elif 10 <= hour <= 16:
            self._rush_hour_factor = 1.2
        elif 22 <= hour or hour <= 5:
            self._rush_hour_factor = 0.3
        else:
            self._rush_hour_factor = 1.0

    async def calculate_trip(
        self,
        citizen: Citizen,
        origin_loc_id: uuid.UUID | None,
        dest_loc_id: uuid.UUID | None,
        sim_time: datetime,
    ) -> TripRecord | None:
        """Calculate and record a trip for a citizen."""
        if not origin_loc_id or not dest_loc_id:
            return None
        if origin_loc_id == dest_loc_id:
            return None

        await self.initialize_network()

        start_key = f"loc_{origin_loc_id}"
        end_key = f"loc_{dest_loc_id}"

        if start_key not in self.network.nodes:
            start_node = self.network.find_nearest_node(0, 0)
            if start_node:
                start_key = start_node.node_id
            else:
                return None
        if end_key not in self.network.nodes:
            end_node = self.network.find_nearest_node(0, 0)
            if end_node:
                end_key = end_node.node_id
            else:
                return None

        vehicle_type = TRANSPORT_PREF_MAP.get(
            citizen.transport_preference, VehicleType.PEDESTRIAN
        )

        path, base_time = self.network.shortest_path(start_key, end_key)

        if not path:
            start_node_obj = self.network.nodes[start_key]
            end_node_obj = self.network.nodes[end_key]
            direct_distance = math.sqrt(
                (start_node_obj.x - end_node_obj.x) ** 2
                + (start_node_obj.y - end_node_obj.y) ** 2
            )
            speed_kmh = SPEED_KMH.get(vehicle_type, 5.0)
            base_time = (direct_distance / 1000.0) / speed_kmh * 60.0

        speed_kmh = SPEED_KMH.get(vehicle_type, 5.0)
        time_factor = 40.0 / max(speed_kmh, 1.0)
        travel_time = base_time * time_factor * self._rush_hour_factor

        start_n = self.network.nodes[start_key]
        end_n = self.network.nodes[end_key]
        distance = math.sqrt(
            (start_n.x - end_n.x) ** 2 + (start_n.y - end_n.y) ** 2
        )

        cost = (distance / 1000.0) * COST_PER_KM.get(vehicle_type, 0.0)

        for edge in self.network.edges:
            if edge.from_node.node_id in path and edge.to_node.node_id in path:
                edge.current_vehicles += 1

        trip = TripRecord(
            citizen_id=citizen.id,
            vehicle_type=vehicle_type,
            origin_x=start_n.x,
            origin_y=start_n.y,
            dest_x=end_n.x,
            dest_y=end_n.y,
            distance_m=distance,
            duration_minutes=max(1.0, travel_time),
            cost=round(cost, 2),
            congestion_experienced=self._rush_hour_factor - 1.0,
            started_at=sim_time,
        )
        self.db.add(trip)
        await self.db.flush()
        return trip

    async def process_tick(self, hour: int) -> dict:
        """Process traffic state for current tick."""
        self.update_rush_hour(hour)

        for edge in self.network.edges:
            edge.current_vehicles = max(0, edge.current_vehicles - random.randint(0, 3))

        congested_roads = sum(1 for e in self.network.edges if e.congestion > 0.7)
        avg_congestion = (
            sum(e.congestion for e in self.network.edges) / max(len(self.network.edges), 1)
        )

        return {
            "total_roads": len(self.network.edges),
            "congested_roads": congested_roads,
            "avg_congestion": round(avg_congestion, 4),
            "rush_hour_factor": self._rush_hour_factor,
            "total_nodes": len(self.network.nodes),
        }

    async def get_traffic_stats(self) -> dict:
        await self.initialize_network()

        trip_result = await self.db.execute(
            select(TripRecord).order_by(TripRecord.started_at.desc()).limit(100)
        )
        recent_trips = list(trip_result.scalars().all())

        by_vehicle: dict[str, int] = {}
        total_distance = 0.0
        total_duration = 0.0
        total_cost = 0.0

        for trip in recent_trips:
            vtype = trip.vehicle_type.value
            by_vehicle[vtype] = by_vehicle.get(vtype, 0) + 1
            total_distance += trip.distance_m
            total_duration += trip.duration_minutes
            total_cost += trip.cost

        return {
            "total_recent_trips": len(recent_trips),
            "trips_by_vehicle": by_vehicle,
            "avg_distance_m": round(total_distance / max(len(recent_trips), 1), 1),
            "avg_duration_min": round(total_duration / max(len(recent_trips), 1), 1),
            "avg_cost": round(total_cost / max(len(recent_trips), 1), 2),
            "network_nodes": len(self.network.nodes),
            "network_edges": len(self.network.edges),
            "rush_hour_factor": self._rush_hour_factor,
        }

    async def get_congestion_map(self) -> list[dict]:
        """Return congestion levels for visualization."""
        await self.initialize_network()
        segments = []
        for edge in self.network.edges:
            if edge.congestion > 0.1:
                segments.append({
                    "from": [edge.from_node.x, edge.from_node.y],
                    "to": [edge.to_node.x, edge.to_node.y],
                    "congestion": round(edge.congestion, 3),
                    "speed": round(edge.effective_speed, 1),
                    "vehicles": edge.current_vehicles,
                })
        return segments

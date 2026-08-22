"""Single source of truth for infrastructure type properties — construction cost,
service radius, capacity, and display metadata. Both the preview-impact/trigger API
and the 3D Build Mode UI read from this instead of hardcoding these numbers in two
(or more) places that would drift out of sync."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InfrastructureTypeConfig:
    key: str
    name: str
    icon: str
    category: str  # "point" (single click) or "line" (two-click, e.g. road/bridge)
    construction_cost: float
    service_radius: float  # sim-coordinate units; 0 for line-based types
    capacity_field: str  # the metric this type primarily provides, e.g. "beds", "seats"
    capacity_range: tuple[int, int]  # (min, max) — matches the random range used on completion
    color: str  # hex, used for the ghost preview and service-radius ring


INFRASTRUCTURE_CONFIG: dict[str, InfrastructureTypeConfig] = {
    "hospital_build": InfrastructureTypeConfig(
        key="hospital_build", name="Hospital", icon="🏥", category="point",
        construction_cost=600_000, service_radius=550, capacity_field="staff",
        capacity_range=(40, 90), color="#ef4444",
    ),
    "school_build": InfrastructureTypeConfig(
        key="school_build", name="School", icon="🏫", category="point",
        construction_cost=400_000, service_radius=450, capacity_field="teachers",
        capacity_range=(10, 25), color="#f59e0b",
    ),
    "colony_build": InfrastructureTypeConfig(
        key="colony_build", name="Housing Colony", icon="🏘️", category="point",
        construction_cost=800_000, service_radius=350, capacity_field="homes",
        capacity_range=(6, 10), color="#8b5cf6",
    ),
    "fire_station_build": InfrastructureTypeConfig(
        key="fire_station_build", name="Fire Station", icon="🚒", category="point",
        construction_cost=350_000, service_radius=500, capacity_field="firefighters",
        capacity_range=(12, 25), color="#f97316",
    ),
    "police_station_build": InfrastructureTypeConfig(
        key="police_station_build", name="Police Station", icon="🚓", category="point",
        construction_cost=320_000, service_radius=500, capacity_field="officers",
        capacity_range=(10, 22), color="#3b82f6",
    ),
    "road_build": InfrastructureTypeConfig(
        key="road_build", name="Road", icon="🛣️", category="line",
        construction_cost=250_000, service_radius=0, capacity_field="lanes",
        capacity_range=(2, 4), color="#eab308",
    ),
    "bridge_build": InfrastructureTypeConfig(
        key="bridge_build", name="Bridge", icon="🌉", category="line",
        construction_cost=200_000, service_radius=0, capacity_field="lanes",
        capacity_range=(2, 4), color="#22d3ee",
    ),
}


def get_config(key: str) -> InfrastructureTypeConfig | None:
    return INFRASTRUCTURE_CONFIG.get(key)


def list_config() -> list[dict]:
    return [
        {
            "key": c.key, "name": c.name, "icon": c.icon, "category": c.category,
            "construction_cost": c.construction_cost, "service_radius": c.service_radius,
            "capacity_field": c.capacity_field, "capacity_min": c.capacity_range[0],
            "capacity_max": c.capacity_range[1], "color": c.color,
        }
        for c in INFRASTRUCTURE_CONFIG.values()
    ]

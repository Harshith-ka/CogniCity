"""
EnvironmentRegistry: the minimal viable "marketplace" — a catalog of TwinEnvironment
implementations you can list and instantiate by key, instead of having to know which
Python class to import. Deliberately stops there: no packaging format for third-party
code, no sandboxing, no payments. Those are real, separate problems (see the module
docstrings on why they're deferred) — this only solves "browse what's available, run
one by name," which is the part that makes anything above it meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.app.twin_platform.environment import TwinEnvironment


@dataclass
class EnvironmentManifest:
    key: str                 # unique slug, e.g. "hospital_ward"
    name: str                # display name
    category: str            # "Healthcare", "Transportation", "Industrial", ...
    icon: str
    description: str
    default_config: dict
    entity_types: list[str]  # what this environment simulates, for the catalog listing
    scenario_examples: list[str]  # sample "what if" events this environment supports
    factory: Callable[[], TwinEnvironment]  # zero-arg constructor for a fresh instance


class EnvironmentRegistry:
    _manifests: dict[str, EnvironmentManifest] = {}

    @classmethod
    def register(cls, manifest: EnvironmentManifest) -> None:
        cls._manifests[manifest.key] = manifest

    @classmethod
    def list(cls) -> list[EnvironmentManifest]:
        return list(cls._manifests.values())

    @classmethod
    def get(cls, key: str) -> EnvironmentManifest | None:
        return cls._manifests.get(key)

    @classmethod
    async def create(cls, key: str, config: dict | None = None) -> TwinEnvironment:
        manifest = cls.get(key)
        if not manifest:
            raise ValueError(f"Unknown environment: {key!r}. Known: {list(cls._manifests)}")
        env = manifest.factory()
        await env.initialize({**manifest.default_config, **(config or {})})
        return env


def register_all() -> None:
    """Called once at API startup. Explicit over import-time side effects — makes it
    obvious where the catalog comes from instead of depending on which modules
    happened to be imported first."""
    from backend.app.twin_platform.city_twin import CityTwin
    from backend.app.twin_platform.hospital_twin import HospitalWardTwin
    from backend.app.twin_platform.airport_twin import AirportTwin
    from backend.app.twin_platform.factory_twin import FactoryTwin
    from backend.app.twin_platform.university_twin import UniversityTwin
    from backend.app.twin_platform.mall_twin import MallTwin

    EnvironmentRegistry.register(EnvironmentManifest(
        key="city", name="AI Digital Twin City", category="Urban", icon="🏙️",
        description="The full production smart-city simulation — citizens, economy, traffic, disasters, government. Wraps the live running instance over its own API.",
        default_config={}, entity_types=["citizens", "businesses", "hospitals", "schools"],
        scenario_examples=["earthquake", "flood", "fire"],
        factory=CityTwin,
    ))
    EnvironmentRegistry.register(EnvironmentManifest(
        key="hospital_ward", name="Emergency Department Simulator", category="Healthcare", icon="🏥",
        description="Patients, doctors, and beds moving through triage → treatment → discharge.",
        default_config={"doctors": 3, "beds": 6, "initial_agents": 5},
        entity_types=["patients", "doctors", "beds"],
        scenario_examples=["patient_surge", "staff_shortage"],
        factory=HospitalWardTwin,
    ))
    EnvironmentRegistry.register(EnvironmentManifest(
        key="airport_terminal", name="Airport Terminal Simulator", category="Transportation", icon="✈️",
        description="Passengers moving through check-in → security → gate → boarding.",
        default_config={"security_counters": 4, "gates": 6, "initial_agents": 10},
        entity_types=["passengers", "security_counters", "gates"],
        scenario_examples=["security_counter_reduction", "passenger_surge", "flight_delay"],
        factory=AirportTwin,
    ))
    EnvironmentRegistry.register(EnvironmentManifest(
        key="factory_line", name="Production Line Simulator", category="Industrial", icon="🏭",
        description="Raw material flowing through production → quality check → storage → shipment, with machines that can fail.",
        default_config={"machines": 5, "workers": 8, "initial_orders": 20},
        entity_types=["machines", "workers", "orders", "inventory"],
        scenario_examples=["machine_failure", "demand_surge", "supply_delay"],
        factory=FactoryTwin,
    ))
    EnvironmentRegistry.register(EnvironmentManifest(
        key="university_campus", name="University Campus Simulator", category="Education", icon="🎓",
        description="Students progressing through a term — classes, exams, and graduation — against fixed classroom/hostel capacity.",
        default_config={"classrooms": 10, "hostel_beds": 200, "initial_agents": 150},
        entity_types=["students", "professors", "classrooms", "hostel_beds"],
        scenario_examples=["enrollment_surge", "professor_shortage", "exam_period"],
        factory=UniversityTwin,
    ))
    EnvironmentRegistry.register(EnvironmentManifest(
        key="shopping_mall", name="Shopping Mall Simulator", category="Retail", icon="🛍️",
        description="Customers arriving, browsing, and either converting to a purchase or leaving, against parking and checkout capacity.",
        default_config={"parking_spots": 100, "checkout_counters": 8, "initial_agents": 20},
        entity_types=["customers", "stores", "parking_spots", "checkout_counters"],
        scenario_examples=["sale_event", "peak_hour_surge", "store_closure"],
        factory=MallTwin,
    ))

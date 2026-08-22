"""
CityTwin: wraps the *already-running* AI Digital Twin City backend — over its own
REST API, not a second in-process SimulationEngine — as a TwinEnvironment.

Deliberately HTTP-backed rather than a direct engine import: a second SimulationEngine
instance sharing the same database as the live background tick loop would risk exactly
the concurrent-session bugs fixed earlier in this project (see get_metrics() using its
own session, step() short-circuiting while RUNNING). Going through the API is also the
more honest proof — it shows the interface works over a genuinely different backing
implementation than the in-memory HospitalWardTwin, not just two flavors of one thing.
"""

from __future__ import annotations

from typing import Any

import httpx

from backend.app.twin_platform.environment import TwinEnvironment

DISASTER_TYPES = {"earthquake", "flood", "cyclone", "fire", "tornado", "tsunami", "landslide"}


class CityTwin(TwinEnvironment):
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.entities: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = []
        self.rules: dict[str, Any] = {}
        self.workflows: list[str] = ["citizen_perceive_decide_act_reflect"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}

    async def initialize(self, config: dict) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            districts = (await client.get(f"{self.base_url}/api/city/districts")).json()
            status = (await client.get(f"{self.base_url}/api/simulation/status")).json()

        self.locations = [{"name": d["name"], "x": d["center_x"], "y": d["center_y"]} for d in districts]
        self.constraints = {"max_population": config.get("max_population", 10000)}
        self.entities = {"citizens": status.get("population", 0)}

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            current = (await client.get(f"{self.base_url}/api/simulation/status")).json()
            target = current.get("population", 0) + count
            result = (await client.post(
                f"{self.base_url}/api/citizens/grow", json={"target_population": target}
            )).json()
        return [c.get("id", "") for c in result.get("new_citizens", [])] or [f"grew:{result.get('added', 0)}"]

    async def step(self) -> dict:
        # A real tick over ~1000 citizens with LLM-backed decisions can take well over
        # a minute (observed 100s+) — a short timeout here doesn't mean "the city is
        # unresponsive," it just means the request gave up too early. Long timeout,
        # and a caught failure instead of an unhandled 500 either way.
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                result = (await client.post(
                    f"{self.base_url}/api/simulation/control", json={"action": "step", "steps": 1}
                )).json()
            return result
        except httpx.TimeoutException:
            return {"status": "timeout", "detail": "City tick did not complete within 300s — try again or check backend load."}

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        """Minimal, honest implementation — the real per-citizen action API doesn't
        exist yet in this project; this proves the interface point without pretending
        more is built than actually is."""
        return {"agent_id": agent_id, "action": action, "applied": False, "reason": "not yet implemented for CityTwin"}

    async def generate_event(self, event_type: str, **params) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if event_type in DISASTER_TYPES:
                res = await client.post(f"{self.base_url}/api/disasters/trigger", json={
                    "disaster_type": event_type,
                    "epicenter_x": params.get("x"),
                    "epicenter_y": params.get("y"),
                    "intensity": params.get("intensity", 0.7),
                })
            else:
                res = await client.post(f"{self.base_url}/api/events/trigger", json={
                    "event_name": params.get("event_name", event_type),
                    "area_x": params.get("x"),
                    "area_y": params.get("y"),
                    "radius": params.get("radius", 500),
                })
        return res.json()

    async def get_state(self) -> dict:
        await self._refresh()
        return {
            "entities": self.entities,
            "locations": self.locations,
            "constraints": self.constraints,
            "metrics": self.metrics,
        }

    async def evaluate(self) -> dict:
        await self._refresh()
        return self.metrics

    async def _refresh(self) -> None:
        """Pulls the live city's current snapshot over HTTP — this is exactly why
        get_state()/evaluate() had to be async in the interface, not a CityTwin-only
        quirk worked around from outside."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            m = (await client.get(f"{self.base_url}/api/analytics/metrics")).json()
            status = (await client.get(f"{self.base_url}/api/simulation/status")).json()
        self.entities["citizens"] = m.get("population", 0)
        self.metrics = {
            "population": m.get("population", 0),
            "unemployment_rate": m.get("unemployment_rate", 0.0),
            "avg_happiness": m.get("avg_happiness", 0.0),
            "avg_health": m.get("avg_health", 0.0),
            "total_gdp": m.get("total_gdp", 0.0),
            "current_tick": status.get("current_tick", 0),
        }

    async def reset(self) -> None:
        """Deliberately not implemented — this wraps a live, shared production
        simulation. A real reset would mean wiping real running state, which is
        exactly the kind of irreversible action this platform should never take
        silently. A generic reset would need a dedicated, explicit admin endpoint."""
        raise NotImplementedError(
            "CityTwin.reset() is intentionally unsupported — it wraps the live running "
            "city simulation and a reset would destroy real state. Build a dedicated "
            "admin-confirmed endpoint if this is ever actually needed."
        )

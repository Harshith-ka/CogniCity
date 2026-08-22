"""
AirportTwin: passengers move through a fixed sequential pipeline (check-in -> security
-> gate -> boarding) instead of the hospital's severity-priority queue — a genuinely
different workflow shape, gated by two independent resource pools (security counters,
gates) rather than one paired resource like doctor+bed.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from backend.app.twin_platform.environment import TwinEnvironment

STAGES = ["check_in", "security", "gate", "boarding", "departed"]


class AirportTwin(TwinEnvironment):
    def __init__(self):
        self.entities: dict[str, Any] = {"passengers": [], "security_counters": [], "gates": []}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = [{"name": "Check-In Hall"}, {"name": "Security"}, {"name": "Gate Area"}]
        self.rules: dict[str, Any] = {"security_process_ticks": 2, "boarding_process_ticks": 3}
        self.workflows: list[str] = ["check_in_security_gate_boarding"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self._config: dict = {}
        self._tick = 0
        self._departed_total = 0
        self._missed_total = 0

    async def initialize(self, config: dict) -> None:
        self._config = config
        n_counters = config.get("security_counters", 4)
        n_gates = config.get("gates", 6)
        self.entities = {
            "passengers": [],
            "security_counters": [{"id": f"sec_{i}", "busy": False, "passenger_id": None} for i in range(n_counters)],
            "gates": [{"id": f"gate_{i}", "busy": False, "passenger_id": None} for i in range(n_gates)],
        }
        self.constraints = {"security_counters": n_counters, "gates": n_gates}
        self._tick = 0
        self._departed_total = 0
        self._missed_total = 0

        for _ in range(config.get("initial_agents", 0)):
            await self.spawn_agents(1)
        await self.evaluate()

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        ids = []
        for _ in range(count):
            pid = str(uuid.uuid4())
            self.entities["passengers"].append({
                "id": pid, "stage": "check_in", "wait_ticks": 0,
                "boarding_deadline": self._tick + random.randint(15, 30),
                "security_counter_id": None, "gate_id": None, "process_ticks_remaining": 0,
            })
            ids.append(pid)
        return ids

    async def step(self) -> dict:
        self._tick += 1
        advanced, missed = [], []

        for p in self.entities["passengers"]:
            if p["stage"] == "departed":
                continue

            if p["stage"] == "check_in":
                p["stage"] = "security"
                continue

            if p["stage"] == "security":
                if not p["security_counter_id"]:
                    counter = next((c for c in self.entities["security_counters"] if not c["busy"]), None)
                    if not counter:
                        p["wait_ticks"] += 1
                        continue
                    counter["busy"], counter["passenger_id"] = True, p["id"]
                    p["security_counter_id"] = counter["id"]
                    p["process_ticks_remaining"] = self.rules["security_process_ticks"]
                p["process_ticks_remaining"] -= 1
                if p["process_ticks_remaining"] <= 0:
                    for c in self.entities["security_counters"]:
                        if c["id"] == p["security_counter_id"]:
                            c["busy"], c["passenger_id"] = False, None
                    p["stage"] = "gate"
                continue

            if p["stage"] == "gate":
                gate = next((g for g in self.entities["gates"] if not g["busy"]), None)
                if not gate:
                    p["wait_ticks"] += 1
                    if self._tick > p["boarding_deadline"]:
                        p["stage"] = "departed"  # missed flight — leaves the pipeline either way
                        self._missed_total += 1
                        missed.append(p["id"])
                    continue
                gate["busy"], gate["passenger_id"] = True, p["id"]
                p["gate_id"] = gate["id"]
                p["process_ticks_remaining"] = self.rules["boarding_process_ticks"]
                p["stage"] = "boarding"
                continue

            if p["stage"] == "boarding":
                p["process_ticks_remaining"] -= 1
                if p["process_ticks_remaining"] <= 0:
                    for g in self.entities["gates"]:
                        if g["id"] == p["gate_id"]:
                            g["busy"], g["passenger_id"] = False, None
                    p["stage"] = "departed"
                    self._departed_total += 1
                    advanced.append(p["id"])

        await self.evaluate()
        return {"tick": self._tick, "departed": advanced, "missed_flight": missed}

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        passenger = next((p for p in self.entities["passengers"] if p["id"] == agent_id), None)
        if not passenger:
            return {"applied": False, "reason": "unknown agent_id"}
        if action.get("type") == "fast_track" and passenger["stage"] in ("check_in", "security"):
            passenger["boarding_deadline"] += 20
            return {"applied": True}
        return {"applied": False, "reason": f"unsupported action type {action.get('type')!r}"}

    async def generate_event(self, event_type: str, **params) -> dict:
        if event_type == "passenger_surge":
            count = params.get("count", 10)
            ids = await self.spawn_agents(count)
            return {"event": "passenger_surge", "new_passengers": len(ids)}

        if event_type == "security_counter_reduction":
            # This is the exact "what happens if security counters are reduced by 20%"
            # scenario from the original platform proposal.
            pct = params.get("reduction_pct", 20)
            remove = max(1, round(len(self.entities["security_counters"]) * pct / 100))
            freed = [c for c in self.entities["security_counters"] if not c["busy"]][:remove]
            for c in freed:
                self.entities["security_counters"].remove(c)
            self.constraints["security_counters"] = len(self.entities["security_counters"])
            return {"event": "security_counter_reduction", "counters_removed": len(freed), "requested_pct": pct}

        if event_type == "flight_delay":
            extra = params.get("extra_ticks", 10)
            for p in self.entities["passengers"]:
                if p["stage"] != "departed":
                    p["boarding_deadline"] += extra
            return {"event": "flight_delay", "extra_ticks": extra}

        return {"event": event_type, "applied": False, "reason": "unknown event_type"}

    async def get_state(self) -> dict:
        return {"tick": self._tick, "entities": self.entities, "constraints": self.constraints, "metrics": self.metrics}

    async def evaluate(self) -> dict:
        passengers = self.entities["passengers"]
        active = [p for p in passengers if p["stage"] != "departed"]
        waiting = [p for p in active if p["wait_ticks"] > 0]

        self.metrics = {
            "security_utilization": round(sum(1 for c in self.entities["security_counters"] if c["busy"]) / max(1, len(self.entities["security_counters"])), 3),
            "gate_utilization": round(sum(1 for g in self.entities["gates"] if g["busy"]) / max(1, len(self.entities["gates"])), 3),
            "passengers_in_pipeline": len(active),
            "avg_wait_ticks": round(sum(p["wait_ticks"] for p in waiting) / len(waiting), 2) if waiting else 0.0,
            "departed_total": self._departed_total,
            "missed_flights_total": self._missed_total,
        }
        return self.metrics

    async def reset(self) -> None:
        await self.initialize(self._config)

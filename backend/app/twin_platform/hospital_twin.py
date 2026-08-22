"""
HospitalWardTwin: a deliberately tiny, fully self-contained, in-memory TwinEnvironment.

Shares nothing with CityTwin or the City's SQLAlchemy models/engines — no database, no
HTTP, no imports from anywhere else in this project except the environment.py interface
itself. That's the actual point of this file: if a completely independent domain (a
hospital ward instead of a city) can satisfy the exact same TwinEnvironment interface
that CityTwin satisfies, the abstraction genuinely holds. If it can't be expressed
cleanly here, the interface was wrong, not this environment.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from backend.app.twin_platform.environment import TwinEnvironment

WORKFLOW = ["waiting", "treatment", "discharged"]


class HospitalWardTwin(TwinEnvironment):
    def __init__(self):
        self.entities: dict[str, Any] = {"patients": [], "doctors": [], "beds": []}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = [{"name": "Emergency Department"}, {"name": "Ward"}]
        self.rules: dict[str, Any] = {"treatment_ticks_per_severity": 6}
        self.workflows: list[str] = ["arrival_triage_treatment_discharge"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self._config: dict = {}
        self._tick = 0
        self._total_discharged = 0

    async def initialize(self, config: dict) -> None:
        self._config = config
        num_doctors = config.get("doctors", 3)
        num_beds = config.get("beds", 6)

        self.entities = {
            "patients": [],
            "doctors": [{"id": f"doc_{i}", "name": f"Dr. {i}", "busy": False, "patient_id": None} for i in range(num_doctors)],
            "beds": [{"id": f"bed_{i}", "occupied": False, "patient_id": None} for i in range(num_beds)],
        }
        self.constraints = {"beds": num_beds, "doctors": num_doctors}
        self._tick = 0
        self._total_discharged = 0

        for _ in range(config.get("initial_agents", 0)):
            await self.spawn_agents(1)
        await self.evaluate()

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        new_ids = []
        for _ in range(count):
            pid = str(uuid.uuid4())
            self.entities["patients"].append({
                "id": pid,
                "severity": round(random.uniform(0.1, 1.0), 2),
                "status": "waiting",
                "arrival_tick": self._tick,
                "wait_ticks": 0,
                "treatment_ticks_remaining": 0,
                "doctor_id": None,
                "bed_id": None,
            })
            new_ids.append(pid)
        return new_ids

    async def step(self) -> dict:
        self._tick += 1
        admitted, discharged = [], []

        # Progress anyone already in treatment
        for p in self.entities["patients"]:
            if p["status"] == "treatment":
                p["treatment_ticks_remaining"] -= 1
                if p["treatment_ticks_remaining"] <= 0:
                    p["status"] = "discharged"
                    for d in self.entities["doctors"]:
                        if d["id"] == p["doctor_id"]:
                            d["busy"], d["patient_id"] = False, None
                    for b in self.entities["beds"]:
                        if b["id"] == p["bed_id"]:
                            b["occupied"], b["patient_id"] = False, None
                    discharged.append(p["id"])
                    self._total_discharged += 1

        # Admit waiting patients, most severe first, while a doctor+bed pair is free
        waiting = sorted(
            (p for p in self.entities["patients"] if p["status"] == "waiting"),
            key=lambda p: -p["severity"],
        )
        for p in waiting:
            free_doctor = next((d for d in self.entities["doctors"] if not d["busy"]), None)
            free_bed = next((b for b in self.entities["beds"] if not b["occupied"]), None)
            if not free_doctor or not free_bed:
                p["wait_ticks"] += 1
                continue
            free_doctor["busy"], free_doctor["patient_id"] = True, p["id"]
            free_bed["occupied"], free_bed["patient_id"] = True, p["id"]
            p["status"] = "treatment"
            p["doctor_id"], p["bed_id"] = free_doctor["id"], free_bed["id"]
            p["treatment_ticks_remaining"] = max(1, round(p["severity"] * self.rules["treatment_ticks_per_severity"]))
            admitted.append(p["id"])

        await self.evaluate()
        return {"tick": self._tick, "admitted": admitted, "discharged": discharged}

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        """The hook an external triage AI plugs into — reprioritize or force-discharge
        a specific patient, distinct from the ward's own autonomous admission logic."""
        patient = next((p for p in self.entities["patients"] if p["id"] == agent_id), None)
        if not patient:
            return {"applied": False, "reason": "unknown agent_id"}

        if action.get("type") == "prioritize" and patient["status"] == "waiting":
            patient["severity"] = min(1.0, patient["severity"] + action.get("amount", 0.3))
            return {"applied": True, "new_severity": patient["severity"]}

        if action.get("type") == "discharge" and patient["status"] == "treatment":
            patient["status"] = "discharged"
            patient["treatment_ticks_remaining"] = 0
            for d in self.entities["doctors"]:
                if d["id"] == patient["doctor_id"]:
                    d["busy"], d["patient_id"] = False, None
            for b in self.entities["beds"]:
                if b["id"] == patient["bed_id"]:
                    b["occupied"], b["patient_id"] = False, None
            self._total_discharged += 1
            return {"applied": True}

        return {"applied": False, "reason": f"unsupported action type {action.get('type')!r}"}

    async def generate_event(self, event_type: str, **params) -> dict:
        if event_type == "patient_surge":
            count = params.get("count", 5)
            ids = await self.spawn_agents(count)
            return {"event": "patient_surge", "new_patients": len(ids)}

        if event_type == "staff_shortage":
            remove = min(params.get("doctors_removed", 1), len(self.entities["doctors"]))
            removed_ids = [d["id"] for d in self.entities["doctors"][:remove]]
            self.entities["doctors"] = self.entities["doctors"][remove:]
            self.constraints["doctors"] = len(self.entities["doctors"])
            return {"event": "staff_shortage", "doctors_removed": removed_ids}

        return {"event": event_type, "applied": False, "reason": "unknown event_type"}

    async def get_state(self) -> dict:
        return {
            "tick": self._tick,
            "entities": self.entities,
            "constraints": self.constraints,
            "metrics": self.metrics,
        }

    async def evaluate(self) -> dict:
        beds = self.entities["beds"]
        doctors = self.entities["doctors"]
        patients = self.entities["patients"]
        waiting = [p for p in patients if p["status"] == "waiting"]

        self.metrics = {
            "bed_utilization": round(sum(1 for b in beds if b["occupied"]) / max(1, len(beds)), 3),
            "doctor_utilization": round(sum(1 for d in doctors if d["busy"]) / max(1, len(doctors)), 3),
            "patients_waiting": len(waiting),
            "avg_wait_ticks": round(sum(p["wait_ticks"] for p in waiting) / len(waiting), 2) if waiting else 0.0,
            "patients_in_treatment": sum(1 for p in patients if p["status"] == "treatment"),
            "patients_discharged_total": self._total_discharged,
        }
        return self.metrics

    async def reset(self) -> None:
        """Safe to fully implement here — this environment owns nothing but its own
        in-memory state, unlike CityTwin wrapping a live shared simulation."""
        await self.initialize(self._config)

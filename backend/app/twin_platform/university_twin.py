"""
UniversityTwin: students carry a slow-moving state (enrolled -> attending -> exams ->
graduated) across many ticks representing a term, rather than the fast per-tick
resource contention of the other environments — a fourth distinct workflow shape,
closer to a long-horizon cohort simulation than a queueing system.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from backend.app.twin_platform.environment import TwinEnvironment


class UniversityTwin(TwinEnvironment):
    def __init__(self):
        self.entities: dict[str, Any] = {"students": [], "professors": []}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = [{"name": "Lecture Halls"}, {"name": "Labs"}, {"name": "Hostels"}]
        self.rules: dict[str, Any] = {"term_length_ticks": 40, "exam_period_start_ratio": 0.85}
        self.workflows: list[str] = ["enrollment_attendance_exams_graduation"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self._config: dict = {}
        self._tick = 0
        self._graduated_total = 0
        self._dropped_total = 0
        self._exam_period_active = False

    async def initialize(self, config: dict) -> None:
        self._config = config
        n_professors = config.get("professors", 15)
        self.entities = {
            "students": [],
            "professors": [{"id": f"prof_{i}", "students_assigned": 0} for i in range(n_professors)],
        }
        self.constraints = {"classrooms": config.get("classrooms", 10), "hostel_beds": config.get("hostel_beds", 200)}
        self._tick = 0
        self._graduated_total = 0
        self._dropped_total = 0
        self._exam_period_active = False

        for _ in range(config.get("initial_agents", 150)):
            await self.spawn_agents(1)
        await self.evaluate()

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        ids = []
        hostel_used = sum(1 for s in self.entities["students"] if s["housed"])
        for _ in range(count):
            sid = str(uuid.uuid4())
            self.entities["students"].append({
                "id": sid, "status": "attending", "gpa": round(random.uniform(2.2, 3.9), 2),
                "stress": round(random.uniform(0.2, 0.5), 2), "enrolled_tick": self._tick,
                "housed": hostel_used < self.constraints.get("hostel_beds", 200),
            })
            if self.entities["students"][-1]["housed"]:
                hostel_used += 1
            ids.append(sid)
        return ids

    async def step(self) -> dict:
        self._tick += 1
        exam_start = self.rules["term_length_ticks"] * self.rules["exam_period_start_ratio"]
        self._exam_period_active = self._tick % self.rules["term_length_ticks"] >= exam_start

        graduated, dropped = [], []
        for s in self.entities["students"]:
            if s["status"] != "attending":
                continue

            if self._exam_period_active:
                s["stress"] = min(1.0, s["stress"] + 0.05)
                s["gpa"] = round(max(0.0, min(4.0, s["gpa"] + random.uniform(-0.08, 0.05))), 2)
            else:
                s["stress"] = max(0.1, s["stress"] - 0.02)

            term_number = (self._tick - s["enrolled_tick"]) // self.rules["term_length_ticks"]
            if (self._tick - s["enrolled_tick"]) % self.rules["term_length_ticks"] == 0 and term_number > 0:
                if term_number >= 8:
                    s["status"] = "graduated"
                    self._graduated_total += 1
                    graduated.append(s["id"])
                elif s["stress"] > 0.9 and random.random() < 0.15:
                    s["status"] = "dropped_out"
                    self._dropped_total += 1
                    dropped.append(s["id"])

        await self.evaluate()
        return {"tick": self._tick, "exam_period": self._exam_period_active, "graduated": graduated, "dropped_out": dropped}

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        student = next((s for s in self.entities["students"] if s["id"] == agent_id), None)
        if not student:
            return {"applied": False, "reason": "unknown agent_id"}
        if action.get("type") == "counseling" and student["status"] == "attending":
            student["stress"] = max(0.0, student["stress"] - action.get("amount", 0.3))
            return {"applied": True, "new_stress": student["stress"]}
        return {"applied": False, "reason": f"unsupported action type {action.get('type')!r}"}

    async def generate_event(self, event_type: str, **params) -> dict:
        if event_type == "enrollment_surge":
            count = params.get("count", 30)
            ids = await self.spawn_agents(count)
            return {"event": "enrollment_surge", "new_students": len(ids)}

        if event_type == "professor_shortage":
            remove = min(params.get("professors_removed", 2), len(self.entities["professors"]))
            self.entities["professors"] = self.entities["professors"][remove:]
            return {"event": "professor_shortage", "professors_removed": remove}

        if event_type == "exam_period":
            self._exam_period_active = True
            return {"event": "exam_period", "forced": True}

        return {"event": event_type, "applied": False, "reason": "unknown event_type"}

    async def get_state(self) -> dict:
        return {"tick": self._tick, "entities": self.entities, "constraints": self.constraints, "metrics": self.metrics}

    async def evaluate(self) -> dict:
        students = self.entities["students"]
        active = [s for s in students if s["status"] == "attending"]

        self.metrics = {
            "active_students": len(active),
            "avg_gpa": round(sum(s["gpa"] for s in active) / len(active), 3) if active else 0.0,
            "avg_stress": round(sum(s["stress"] for s in active) / len(active), 3) if active else 0.0,
            "hostel_occupancy": round(sum(1 for s in active if s["housed"]) / max(1, self.constraints.get("hostel_beds", 200)), 3),
            "professor_count": len(self.entities["professors"]),
            "graduated_total": self._graduated_total,
            "dropped_out_total": self._dropped_total,
            "exam_period_active": self._exam_period_active,
        }
        return self.metrics

    async def reset(self) -> None:
        await self.initialize(self._config)

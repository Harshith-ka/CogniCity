"""
FactoryTwin: a throughput/rate simulation rather than per-agent journeys — orders flow
through production -> quality check -> storage -> shipment as batches, and machines
have persistent health (a failure doesn't just occupy them for a few ticks, it takes
them fully offline until repaired). A third genuinely different workflow shape.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from backend.app.twin_platform.environment import TwinEnvironment


class FactoryTwin(TwinEnvironment):
    def __init__(self):
        self.entities: dict[str, Any] = {"machines": [], "workers": [], "orders": []}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = [{"name": "Production Floor"}, {"name": "QC Bay"}, {"name": "Warehouse"}]
        self.rules: dict[str, Any] = {"units_per_machine_per_tick": 4, "defect_rate": 0.05}
        self.workflows: list[str] = ["production_qc_storage_shipment"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self._config: dict = {}
        self._tick = 0
        self._inventory = 0
        self._shipped_total = 0
        self._defects_total = 0

    async def initialize(self, config: dict) -> None:
        self._config = config
        n_machines = config.get("machines", 5)
        n_workers = config.get("workers", 8)
        self.entities = {
            "machines": [{"id": f"machine_{i}", "operational": True, "assigned_worker_id": None} for i in range(n_machines)],
            "workers": [{"id": f"worker_{i}", "assigned_machine_id": None} for i in range(n_workers)],
            "orders": [],
        }
        # Assign workers to machines up to whichever pool is smaller
        for machine, worker in zip(self.entities["machines"], self.entities["workers"]):
            machine["assigned_worker_id"] = worker["id"]
            worker["assigned_machine_id"] = machine["id"]

        self.constraints = {"machines": n_machines, "workers": n_workers}
        self._tick = 0
        self._inventory = 0
        self._shipped_total = 0
        self._defects_total = 0

        for _ in range(config.get("initial_orders", 20)):
            await self.spawn_agents(1)
        await self.evaluate()

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        ids = []
        for _ in range(count):
            oid = str(uuid.uuid4())
            self.entities["orders"].append({
                "id": oid, "units_required": random.randint(10, 50), "units_produced": 0, "status": "pending", "created_tick": self._tick,
            })
            ids.append(oid)
        return ids

    async def step(self) -> dict:
        self._tick += 1
        operational_machines = [m for m in self.entities["machines"] if m["operational"] and m["assigned_worker_id"]]
        capacity = len(operational_machines) * self.rules["units_per_machine_per_tick"]

        produced_this_tick = 0
        for order in self.entities["orders"]:
            if order["status"] not in ("pending", "in_production") or capacity <= 0:
                continue
            order["status"] = "in_production"
            remaining = order["units_required"] - order["units_produced"]
            take = min(remaining, capacity)
            order["units_produced"] += take
            capacity -= take
            produced_this_tick += take
            if order["units_produced"] >= order["units_required"]:
                order["status"] = "quality_check"

        defects = round(produced_this_tick * self.rules["defect_rate"])
        self._defects_total += defects
        self._inventory += max(0, produced_this_tick - defects)

        shipped = []
        for order in self.entities["orders"]:
            if order["status"] == "quality_check":
                order["status"] = "shipped"
                self._shipped_total += 1
                shipped.append(order["id"])

        await self.evaluate()
        return {"tick": self._tick, "units_produced": produced_this_tick, "defects": defects, "orders_shipped": shipped}

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        machine = next((m for m in self.entities["machines"] if m["id"] == agent_id), None)
        if not machine:
            return {"applied": False, "reason": "unknown agent_id"}
        if action.get("type") == "repair":
            machine["operational"] = True
            return {"applied": True}
        if action.get("type") == "reassign_worker":
            machine["assigned_worker_id"] = action.get("worker_id")
            return {"applied": True}
        return {"applied": False, "reason": f"unsupported action type {action.get('type')!r}"}

    async def generate_event(self, event_type: str, **params) -> dict:
        if event_type == "machine_failure":
            # The exact "what happens if machine #12 fails" scenario from the
            # original platform proposal.
            machine_id = params.get("machine_id")
            machine = next((m for m in self.entities["machines"] if m["id"] == machine_id), None)
            if not machine:
                machine = next((m for m in self.entities["machines"] if m["operational"]), None)
            if machine:
                machine["operational"] = False
                return {"event": "machine_failure", "machine_id": machine["id"]}
            return {"event": "machine_failure", "applied": False, "reason": "no operational machines to fail"}

        if event_type == "demand_surge":
            count = params.get("order_count", 10)
            ids = await self.spawn_agents(count)
            return {"event": "demand_surge", "new_orders": len(ids)}

        if event_type == "supply_delay":
            factor = params.get("slowdown_factor", 0.5)
            self.rules["units_per_machine_per_tick"] = max(1, round(self.rules["units_per_machine_per_tick"] * factor))
            return {"event": "supply_delay", "new_units_per_machine_per_tick": self.rules["units_per_machine_per_tick"]}

        return {"event": event_type, "applied": False, "reason": "unknown event_type"}

    async def get_state(self) -> dict:
        return {"tick": self._tick, "entities": self.entities, "constraints": self.constraints, "metrics": self.metrics}

    async def evaluate(self) -> dict:
        machines = self.entities["machines"]
        orders = self.entities["orders"]
        pending_or_in_production = [o for o in orders if o["status"] in ("pending", "in_production")]

        self.metrics = {
            "machine_utilization": round(sum(1 for m in machines if m["operational"]) / max(1, len(machines)), 3),
            "inventory_level": self._inventory,
            "orders_pending": len(pending_or_in_production),
            "orders_shipped_total": self._shipped_total,
            "defects_total": self._defects_total,
            "defect_rate_actual": round(self._defects_total / max(1, self._shipped_total * 20), 4),
        }
        return self.metrics

    async def reset(self) -> None:
        await self.initialize(self._config)

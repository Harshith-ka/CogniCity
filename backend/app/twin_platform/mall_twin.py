"""
MallTwin: customers flow through a probabilistic conversion funnel (arrive -> browse ->
maybe purchase -> leave) instead of a deterministic pipeline — every other environment
here has entities that eventually complete their journey the same way; this one
genuinely branches, which is the point of building it last.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from backend.app.twin_platform.environment import TwinEnvironment


class MallTwin(TwinEnvironment):
    def __init__(self):
        self.entities: dict[str, Any] = {"customers": [], "parking_spots": [], "checkout_counters": []}
        self.resources: dict[str, Any] = {}
        self.locations: list[dict] = [{"name": "Parking"}, {"name": "Stores"}, {"name": "Food Court"}]
        self.rules: dict[str, Any] = {"base_conversion_rate": 0.3, "browse_ticks": 3}
        self.workflows: list[str] = ["arrival_browse_purchase_or_leave"]
        self.constraints: dict[str, Any] = {}
        self.metrics: dict[str, float] = {}
        self._config: dict = {}
        self._tick = 0
        self._revenue_total = 0.0
        self._purchases_total = 0
        self._left_without_buying_total = 0
        self._conversion_multiplier = 1.0

    async def initialize(self, config: dict) -> None:
        self._config = config
        n_parking = config.get("parking_spots", 100)
        n_checkout = config.get("checkout_counters", 8)
        self.entities = {
            "customers": [],
            "parking_spots": [{"id": f"park_{i}", "occupied": False} for i in range(n_parking)],
            "checkout_counters": [{"id": f"chk_{i}", "busy": False} for i in range(n_checkout)],
        }
        self.constraints = {"parking_spots": n_parking, "checkout_counters": n_checkout}
        self._tick = 0
        self._revenue_total = 0.0
        self._purchases_total = 0
        self._left_without_buying_total = 0
        self._conversion_multiplier = 1.0

        for _ in range(config.get("initial_agents", 20)):
            await self.spawn_agents(1)
        await self.evaluate()

    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        ids = []
        for _ in range(count):
            spot = next((p for p in self.entities["parking_spots"] if not p["occupied"]), None)
            cid = str(uuid.uuid4())
            self.entities["customers"].append({
                "id": cid, "stage": "browsing" if spot else "no_parking", "arrival_tick": self._tick,
                "browse_ticks_remaining": self.rules["browse_ticks"], "parking_spot_id": spot["id"] if spot else None,
                "spend": 0.0,
            })
            if spot:
                spot["occupied"] = True
            ids.append(cid)
        return ids

    async def step(self) -> dict:
        self._tick += 1
        purchased, left = [], []

        for c in self.entities["customers"]:
            if c["stage"] in ("purchased", "left", "no_parking"):
                continue

            if c["stage"] == "browsing":
                c["browse_ticks_remaining"] -= 1
                if c["browse_ticks_remaining"] > 0:
                    continue
                converts = random.random() < (self.rules["base_conversion_rate"] * self._conversion_multiplier)
                c["stage"] = "checkout" if converts else "leaving"
                continue

            if c["stage"] == "checkout":
                counter = next((k for k in self.entities["checkout_counters"] if not k["busy"]), None)
                if not counter:
                    continue  # queued at checkout, retried next tick
                counter["busy"] = True
                c["spend"] = round(random.uniform(500, 5000), 2)
                self._revenue_total += c["spend"]
                self._purchases_total += 1
                c["stage"] = "purchased"
                purchased.append(c["id"])
                counter["busy"] = False  # single-tick checkout — frees immediately for the next customer
                self._release_parking(c)
                continue

            if c["stage"] == "leaving":
                c["stage"] = "left"
                self._left_without_buying_total += 1
                left.append(c["id"])
                self._release_parking(c)

        await self.evaluate()
        return {"tick": self._tick, "purchased": purchased, "left_without_buying": left}

    def _release_parking(self, customer: dict) -> None:
        spot = next((p for p in self.entities["parking_spots"] if p["id"] == customer["parking_spot_id"]), None)
        if spot:
            spot["occupied"] = False

    async def apply_action(self, agent_id: str, action: dict) -> dict:
        customer = next((c for c in self.entities["customers"] if c["id"] == agent_id), None)
        if not customer:
            return {"applied": False, "reason": "unknown agent_id"}
        if action.get("type") == "targeted_discount" and customer["stage"] == "browsing":
            customer["browse_ticks_remaining"] = 0  # nudges them toward the checkout decision immediately
            return {"applied": True}
        return {"applied": False, "reason": f"unsupported action type {action.get('type')!r}"}

    async def generate_event(self, event_type: str, **params) -> dict:
        if event_type == "sale_event":
            self._conversion_multiplier = params.get("multiplier", 1.8)
            return {"event": "sale_event", "conversion_multiplier": self._conversion_multiplier}

        if event_type == "peak_hour_surge":
            count = params.get("count", 25)
            ids = await self.spawn_agents(count)
            return {"event": "peak_hour_surge", "new_customers": len(ids)}

        if event_type == "store_closure":
            remove = min(params.get("checkout_counters_removed", 2), len(self.entities["checkout_counters"]))
            self.entities["checkout_counters"] = self.entities["checkout_counters"][remove:]
            self.constraints["checkout_counters"] = len(self.entities["checkout_counters"])
            return {"event": "store_closure", "checkout_counters_removed": remove}

        return {"event": event_type, "applied": False, "reason": "unknown event_type"}

    async def get_state(self) -> dict:
        return {"tick": self._tick, "entities": self.entities, "constraints": self.constraints, "metrics": self.metrics}

    async def evaluate(self) -> dict:
        customers = self.entities["customers"]
        active = [c for c in customers if c["stage"] not in ("purchased", "left", "no_parking")]
        completed = self._purchases_total + self._left_without_buying_total

        self.metrics = {
            "parking_utilization": round(sum(1 for p in self.entities["parking_spots"] if p["occupied"]) / max(1, len(self.entities["parking_spots"])), 3),
            "customers_active": len(active),
            "conversion_rate": round(self._purchases_total / completed, 3) if completed else 0.0,
            "total_revenue": round(self._revenue_total, 2),
            "purchases_total": self._purchases_total,
            "left_without_buying_total": self._left_without_buying_total,
        }
        return self.metrics

    async def reset(self) -> None:
        await self.initialize(self._config)

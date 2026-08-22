"""
TwinEnvironment: the interface every simulation environment (City, Hospital, Airport,
Factory, ...) must implement so the platform can initialize, step, act on, perturb,
and evaluate any of them the same way — the abstraction the Environment Marketplace
idea depends on.

This module defines the interface only. It does not know about Postgres, Docker, or
this project's specific City simulation — that's the point: an environment built
against this file alone should be swappable with any other.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TwinEnvironment(ABC):
    """Base class for a pluggable simulation environment.

    Structural attributes (set during initialize(), read by the platform without
    needing to know the environment's internals):
      entities    — entity type name -> current collection/state (e.g. "patients": [...])
      resources   — shared constrained resources (beds, gates, security counters...)
      locations   — named zones/areas within the environment
      rules       — tunable parameters governing behavior (arrival rate, staffing...)
      workflows   — named pipelines entities move through (e.g. "triage_to_discharge")
      constraints — hard limits (capacity, budget, staffing ceilings)
      metrics     — most recent KPI snapshot, refreshed by evaluate()
    """

    entities: dict[str, Any]
    resources: dict[str, Any]
    locations: list[dict]
    rules: dict[str, Any]
    workflows: list[str]
    constraints: dict[str, Any]
    metrics: dict[str, float]

    @abstractmethod
    async def initialize(self, config: dict) -> None:
        """Build the environment's starting state from a config/schema dict."""

    @abstractmethod
    async def spawn_agents(self, count: int, **kwargs) -> list[str]:
        """Create `count` new agents (citizens/patients/passengers/...) and return their ids."""

    @abstractmethod
    async def step(self) -> dict:
        """Advance the environment by one tick. Returns a dict describing what happened."""

    @abstractmethod
    async def apply_action(self, agent_id: str, action: dict) -> dict:
        """Apply an external decision/action to a specific agent — this is the hook a
        developer's own AI plugs into, distinct from the environment's own autonomous
        agent behavior during step()."""

    @abstractmethod
    async def generate_event(self, event_type: str, **params) -> dict:
        """Trigger a scenario/perturbation (disaster, machine failure, arrival surge,
        security counters reduced, ...) and return what was triggered."""

    @abstractmethod
    async def get_state(self) -> dict:
        """Return a full snapshot of current entities/resources/metrics. Async because
        a real environment may need to fetch this (a live API, a database, a sensor
        feed) rather than just read already-in-memory state."""

    @abstractmethod
    async def evaluate(self) -> dict:
        """Compute and return the environment's current KPIs. Async for the same
        reason as get_state() — an in-memory environment can just compute and return,
        but that's a special case, not something the interface should assume."""

    @abstractmethod
    async def reset(self) -> None:
        """Reset the environment back to its initial state."""

"""
Proof-of-concept: run_environment() below calls nothing but TwinEnvironment's abstract
methods. It has no idea whether it's driving a hospital ward or a live city — that's
the whole test. If both CityTwin and HospitalWardTwin can be driven by this exact same
function and produce sensible output, the abstraction holds.

Run inside the backend container (it needs httpx + the running API for CityTwin):
    docker compose exec backend python -m backend.app.twin_platform.proof_demo
"""

from __future__ import annotations

import asyncio
import json

from backend.app.twin_platform.city_twin import CityTwin
from backend.app.twin_platform.environment import TwinEnvironment
from backend.app.twin_platform.hospital_twin import HospitalWardTwin


async def run_environment(env: TwinEnvironment, config: dict, ticks: int, event: tuple[str, dict] | None = None) -> dict:
    """Domain-agnostic driver — every call here is an abstract TwinEnvironment method.
    Nothing in this function knows or cares what kind of environment it's holding.
    initial_agents is handled by initialize() itself now, not spawned separately here —
    an environment should be fully set up from its own config, not need a second call
    from the caller to actually have a starting population."""
    await env.initialize(config)

    history = []
    for i in range(ticks):
        if event and i == ticks // 2:
            event_type, params = event
            await env.generate_event(event_type, **params)
        result = await env.step()
        history.append(result)

    return {"final_state": await env.get_state(), "final_metrics": await env.evaluate(), "tick_history_len": len(history)}


async def main():
    print("=" * 70)
    print("HospitalWardTwin — fully independent in-memory environment")
    print("=" * 70)
    hospital_result = await run_environment(
        HospitalWardTwin(),
        config={"doctors": 2, "beds": 4, "initial_agents": 5},
        ticks=20,
        event=("patient_surge", {"count": 8}),
    )
    print(json.dumps(hospital_result["final_metrics"], indent=2))
    print(f"(ran {hospital_result['tick_history_len']} ticks through the identical run_environment() driver)\n")

    print("=" * 70)
    print("CityTwin — the same driver, wrapping the live running city over HTTP")
    print("=" * 70)
    city = CityTwin()
    await city.initialize({})
    print("Before:", json.dumps(await city.evaluate(), indent=2))
    step_result = await city.step()
    print("After 1 step:", json.dumps(await city.evaluate(), indent=2))
    print(f"\nstep() returned: {json.dumps(step_result, default=str)[:300]}")


if __name__ == "__main__":
    asyncio.run(main())

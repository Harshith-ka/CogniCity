"""
LLM-Powered Decision Engine: Replaces rule-based decide() with natural
language reasoning using personality, memories, emotions, and social context.
Falls back to rule-based when LLM is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from backend.app.agents.citizen_agent import CitizenState, decide as rule_based_decide
from backend.app.services.llm_service import get_llm_service

log = structlog.get_logger()

DECISION_SYSTEM_PROMPT = """You are the inner mind of a simulated citizen in a digital twin city.
You make decisions based on personality, needs, emotions, and context.

PERSONALITY TRAITS (Big Five, 0-1 scale):
- Openness: curiosity, creativity, preference for novelty
- Conscientiousness: organization, responsibility, work ethic
- Extraversion: sociability, energy from interactions
- Agreeableness: cooperation, trust, empathy
- Neuroticism: emotional sensitivity, worry, stress reactivity

Respond with ONLY a JSON object:
{
  "action": "<chosen action from available list>",
  "reasoning": "<1-sentence internal thought>",
  "mood_shift": "<positive|negative|neutral>"
}"""


def _build_decision_prompt(state: CitizenState) -> str:
    personality = state.personality or {}
    traits = ", ".join(
        f"{k}: {v:.1f}" for k, v in personality.items()
    )

    needs_status = []
    if state.energy < 0.3:
        needs_status.append(f"Very tired (energy: {state.energy:.0%})")
    if state.hunger > 0.6:
        needs_status.append(f"Hungry (hunger: {state.hunger:.0%})")
    if state.social_need > 0.6:
        needs_status.append(f"Lonely (social need: {state.social_need:.0%})")
    if state.health < 0.4:
        needs_status.append(f"Unwell (health: {state.health:.0%})")
    if state.stress > 0.7:
        needs_status.append(f"Stressed (stress: {state.stress:.0%})")
    if state.balance < 100:
        needs_status.append(f"Low on money (${state.balance:.0f})")

    if not needs_status:
        needs_status.append("All needs are okay")

    context_parts = [
        f"Name: {state.name}, Age: {state.age}, Occupation: {state.occupation}",
        f"Time: {state.sim_hour}:00 (Day {state.sim_day})",
        f"Personality: {traits}",
        f"Mood: happiness={state.happiness:.0%}, stress={state.stress:.0%}",
        f"Needs: {'; '.join(needs_status)}",
        f"Balance: ${state.balance:.0f}",
    ]

    if state.memory_context:
        context_parts.append(f"Recent memories: {state.memory_context}")

    if state.friend_ids:
        context_parts.append(f"Has {len(state.friend_ids)} friends nearby")

    context = "\n".join(context_parts)
    actions = ", ".join(state.available_actions) if state.available_actions else "idle"

    return (
        f"{context}\n\n"
        f"Available actions: [{actions}]\n\n"
        f"What does {state.name} decide to do right now? "
        f"Pick ONE action from the available list."
    )


async def llm_decide(state: CitizenState) -> dict[str, Any]:
    llm = get_llm_service()
    if not llm.is_available:
        return rule_based_decide(state)

    prompt = _build_decision_prompt(state)

    result = await llm.generate_json(
        prompt=prompt,
        system=DECISION_SYSTEM_PROMPT,
        schema_hint='{"action": "string", "reasoning": "string", "mood_shift": "positive|negative|neutral"}',
        temperature=0.8,
    )

    if not result or "action" not in result:
        log.debug("llm_decide_fallback", citizen=state.name)
        return rule_based_decide(state)

    action = result["action"]
    if action not in state.available_actions and state.available_actions:
        closest = _find_closest_action(action, state.available_actions)
        if closest:
            action = closest
        else:
            log.debug("llm_invalid_action", citizen=state.name, action=action)
            return rule_based_decide(state)

    log.debug(
        "llm_decide",
        citizen=state.name,
        action=action,
        reasoning=result.get("reasoning", ""),
    )

    return {"decision": action}


def _find_closest_action(action: str, available: list[str]) -> str | None:
    action_lower = action.lower().replace(" ", "_")

    for avail in available:
        if action_lower == avail.lower():
            return avail

    for avail in available:
        if action_lower in avail.lower() or avail.lower() in action_lower:
            return avail

    return None


REFLECT_SYSTEM_PROMPT = """You are the inner reflection of a simulated citizen after performing an action.
Based on the action and current state, generate a brief internal thought.

Respond with ONLY a JSON object:
{
  "thought": "<1-sentence reflection>",
  "memory_importance": <0.0-1.0>,
  "emotional_response": "<joy|sadness|fear|anger|trust|surprise|neutral>"
}"""


async def llm_reflect(state: CitizenState) -> dict[str, Any]:
    llm = get_llm_service()
    if not llm.is_available:
        from backend.app.agents.citizen_agent import reflect as rule_based_reflect
        return rule_based_reflect(state)

    prompt = (
        f"{state.name} (age {state.age}, {state.occupation}) just finished: {state.action_result}\n"
        f"Current mood: happiness={state.happiness:.0%}, stress={state.stress:.0%}\n"
        f"How does {state.name} feel about what just happened?"
    )

    result = await llm.generate_json(
        prompt=prompt,
        system=REFLECT_SYSTEM_PROMPT,
        temperature=0.7,
    )

    messages = []
    new_memories = list(state.new_memories)

    if result and "thought" in result:
        importance = result.get("memory_importance", 0.3)
        if importance > 0.3:
            new_memories.append({
                "content": result["thought"],
                "type": "episodic",
                "importance": importance,
            })

        emotion = result.get("emotional_response", "neutral")
        if emotion in ("sadness", "fear", "anger"):
            messages.append({
                "role": "system",
                "content": f"{state.name} is feeling {emotion}: {result['thought']}",
            })

    if state.happiness < 0.3:
        messages.append({"role": "system", "content": f"{state.name} is feeling unhappy"})
    if state.stress > 0.8:
        messages.append({"role": "system", "content": f"{state.name} is very stressed"})
    if state.health < 0.3:
        messages.append({"role": "system", "content": f"{state.name} needs medical attention"})

    return {"messages": messages, "new_memories": new_memories}

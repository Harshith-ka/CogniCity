"""
Citizen Agent: LangGraph-based autonomous agent for each citizen.
Handles decision-making, activity selection, and social interactions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog
from langgraph.graph import StateGraph, END

from backend.app.models.citizen import Citizen

log = structlog.get_logger()


@dataclass
class CitizenState:
    citizen_id: str = ""
    name: str = ""
    age: int = 0
    occupation: str = "unemployed"
    personality: dict = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)

    happiness: float = 0.7
    stress: float = 0.3
    health: float = 0.9
    energy: float = 1.0
    hunger: float = 0.0
    social_need: float = 0.5
    balance: float = 1000.0

    current_activity: str = "idle"
    current_location: str = "home"
    sim_hour: int = 6
    sim_day: int = 0

    memory_context: str = ""
    nearby_citizens: list[str] = field(default_factory=list)
    available_actions: list[str] = field(default_factory=list)

    decision: str = ""
    action_result: str = ""
    new_memories: list[dict] = field(default_factory=list)
    emotional_changes: dict = field(default_factory=dict)
    transactions: list[dict] = field(default_factory=list)

    messages: list[dict] = field(default_factory=list)
    relationship_count: int = 0
    friend_ids: list[str] = field(default_factory=list)


def perceive(state: CitizenState) -> dict[str, Any]:
    """Gather available actions based on needs and time of day."""
    hour = state.sim_hour
    actions = []

    if state.energy < 0.2:
        actions.append("sleep")
    if state.hunger > 0.7:
        actions.extend(["eat_at_home", "eat_at_restaurant"])
    if state.social_need > 0.7:
        actions.extend(["socialize", "call_friend", "visit_neighbor", "post_social_media"])
    if state.health < 0.3:
        actions.append("visit_hospital")

    if 6 <= hour < 8:
        actions.extend(["wake_up", "breakfast", "exercise"])
    elif 8 <= hour < 9:
        actions.extend(["commute_to_work", "breakfast"])
    elif 9 <= hour < 17:
        if state.occupation != "unemployed":
            actions.extend(["work", "lunch_break", "meeting"])
        else:
            actions.extend(["job_search", "learn_skill", "freelance"])
    elif 17 <= hour < 18:
        actions.extend(["commute_home", "shopping"])
    elif 18 <= hour < 21:
        actions.extend(["dinner", "entertainment", "exercise", "socialize", "study", "post_social_media", "call_friend"])
    elif 21 <= hour < 23:
        actions.extend(["relax", "read", "watch_tv", "prepare_for_bed"])
    else:
        actions.append("sleep")

    if state.balance < 100:
        actions.append("worry_about_finances")
    if state.balance > 5000:
        actions.append("invest")

    unique_actions = list(dict.fromkeys(actions))
    return {"available_actions": unique_actions}


def decide(state: CitizenState) -> dict[str, Any]:
    """Rule-based decision engine with personality weighting."""
    needs = {
        "energy": 1.0 - state.energy,
        "hunger": state.hunger,
        "social": state.social_need,
        "health": 1.0 - state.health,
        "financial": 1.0 if state.balance < 100 else 0.0,
    }

    most_urgent = max(needs, key=needs.get)  # type: ignore[arg-type]

    action_map = {
        "energy": "sleep",
        "hunger": "eat_at_home" if state.balance < 500 else "eat_at_restaurant",
        "social": "socialize",
        "health": "visit_hospital",
        "financial": "job_search" if state.occupation == "unemployed" else "work",
    }

    critical_need = needs[most_urgent] > 0.8
    if critical_need:
        decision = action_map[most_urgent]
    elif state.available_actions:
        hour = state.sim_hour
        openness = state.personality.get("openness", 0.5)
        extraversion = state.personality.get("extraversion", 0.5)
        conscientiousness = state.personality.get("conscientiousness", 0.5)
        neuroticism = state.personality.get("neuroticism", 0.5)

        if 9 <= hour < 17 and state.occupation != "unemployed" and "work" in state.available_actions:
            if conscientiousness > 0.6:
                decision = "work"
            elif "meeting" in state.available_actions and extraversion > 0.6:
                decision = "meeting"
            else:
                decision = "work"
        elif "sleep" in state.available_actions and (hour >= 23 or hour < 6):
            decision = "sleep"
        elif extraversion > 0.7 and state.social_need > 0.4:
            if "call_friend" in state.available_actions and state.friend_ids:
                decision = "call_friend"
            elif "socialize" in state.available_actions:
                decision = "socialize"
            elif "post_social_media" in state.available_actions:
                decision = "post_social_media"
            else:
                decision = state.available_actions[0]
        elif openness > 0.7:
            for preferred in ["entertainment", "learn_skill", "study", "exercise"]:
                if preferred in state.available_actions:
                    decision = preferred
                    break
            else:
                decision = state.available_actions[0]
        elif neuroticism > 0.7 and state.stress > 0.5:
            for calming in ["relax", "exercise", "read", "sleep"]:
                if calming in state.available_actions:
                    decision = calming
                    break
            else:
                decision = state.available_actions[0]
        elif "socialize" in state.available_actions and state.social_need > 0.5:
            decision = "socialize"
        else:
            decision = state.available_actions[0]
    else:
        decision = "idle"

    return {"decision": decision}


def act(state: CitizenState) -> dict[str, Any]:
    """Execute the decided action and compute effects."""
    action = state.decision
    result = f"Performed: {action}"
    new_memories: list[dict] = []
    emotional_changes: dict[str, float] = {}
    transactions: list[dict] = []

    energy_delta = 0.0
    hunger_delta = 0.05
    social_delta = 0.02
    happiness_delta = 0.0
    stress_delta = 0.0
    balance_delta = 0.0

    if action == "sleep":
        energy_delta = 0.3
        hunger_delta = 0.02
        stress_delta = -0.1
        result = "Slept and recovered energy"

    elif action in ("eat_at_home", "breakfast", "dinner", "lunch_break"):
        hunger_delta = -0.5
        energy_delta = 0.05
        balance_delta = -15.0
        result = "Had a meal at home"
        transactions.append({"type": "purchase", "amount": 15.0, "desc": "Meal"})

    elif action == "eat_at_restaurant":
        hunger_delta = -0.6
        energy_delta = 0.05
        happiness_delta = 0.05
        social_delta = -0.1
        balance_delta = -40.0
        result = "Enjoyed a restaurant meal"
        transactions.append({"type": "purchase", "amount": 40.0, "desc": "Restaurant meal"})

    elif action == "work":
        energy_delta = -0.15
        stress_delta = 0.05
        hunger_delta = 0.1
        social_delta = -0.05
        daily_salary = state.balance * 0 + (3000.0 / 30.0)
        balance_delta = daily_salary / 8
        result = f"Worked for an hour, earned ${balance_delta:.0f}"

    elif action == "socialize":
        social_delta = -0.3
        happiness_delta = 0.1
        energy_delta = -0.05
        result = "Socialized with others"
        emotional_changes["joy"] = 0.1
        new_memories.append({
            "content": "Had a good time socializing",
            "type": "episodic",
            "importance": 0.3,
        })

    elif action == "exercise":
        energy_delta = -0.1
        health_delta = 0.05
        stress_delta = -0.1
        happiness_delta = 0.05
        result = "Exercised at the gym"

    elif action == "entertainment":
        happiness_delta = 0.1
        energy_delta = -0.05
        balance_delta = -25.0
        stress_delta = -0.1
        result = "Enjoyed entertainment"
        transactions.append({"type": "purchase", "amount": 25.0, "desc": "Entertainment"})

    elif action == "shopping":
        balance_delta = -50.0
        happiness_delta = 0.05
        result = "Went shopping"
        transactions.append({"type": "purchase", "amount": 50.0, "desc": "Shopping"})

    elif action == "visit_hospital":
        balance_delta = -100.0
        result = "Visited hospital"
        emotional_changes["fear"] = 0.1
        transactions.append({"type": "purchase", "amount": 100.0, "desc": "Hospital visit"})
        new_memories.append({
            "content": "Visited the hospital for health concerns",
            "type": "episodic",
            "importance": 0.6,
        })

    elif action == "job_search":
        stress_delta = 0.05
        energy_delta = -0.05
        result = "Searched for jobs"

    elif action == "commute_to_work":
        energy_delta = -0.05
        stress_delta = 0.02
        result = "Commuted to work"

    elif action == "commute_home":
        energy_delta = -0.03
        result = "Commuted home"

    elif action == "study":
        energy_delta = -0.1
        stress_delta = 0.03
        result = "Studied and learned"

    elif action == "call_friend":
        social_delta = -0.25
        happiness_delta = 0.08
        energy_delta = -0.03
        result = "Called a friend"
        new_memories.append({
            "content": "Had a phone call with a friend",
            "type": "relationship",
            "importance": 0.3,
        })

    elif action == "visit_neighbor":
        social_delta = -0.2
        happiness_delta = 0.06
        energy_delta = -0.05
        result = "Visited a neighbor"
        emotional_changes["trust"] = 0.05
        new_memories.append({
            "content": "Visited a neighbor and chatted",
            "type": "relationship",
            "importance": 0.25,
        })

    elif action == "post_social_media":
        social_delta = -0.1
        happiness_delta = 0.03
        energy_delta = -0.02
        result = "Posted on social media"

    elif action == "invest":
        investment = min(state.balance * 0.1, 500.0)
        balance_delta = -investment
        stress_delta = 0.02
        result = f"Invested ${investment:.0f}"
        transactions.append({"type": "investment", "amount": investment, "desc": "Investment"})
        new_memories.append({
            "content": f"Made an investment of ${investment:.0f}",
            "type": "episodic",
            "importance": 0.4,
        })

    elif action in ("relax", "read", "watch_tv", "prepare_for_bed"):
        energy_delta = 0.05
        stress_delta = -0.05
        happiness_delta = 0.02
        result = f"Relaxed: {action.replace('_', ' ')}"

    elif action == "learn_skill":
        energy_delta = -0.1
        stress_delta = 0.02
        happiness_delta = 0.03
        result = "Learned a new skill"
        new_memories.append({
            "content": "Spent time learning a new skill",
            "type": "semantic",
            "importance": 0.4,
        })

    elif action == "freelance":
        energy_delta = -0.12
        stress_delta = 0.04
        balance_delta = 30.0
        result = "Did freelance work"
        transactions.append({"type": "salary", "amount": 30.0, "desc": "Freelance income"})

    elif action == "meeting":
        energy_delta = -0.08
        stress_delta = 0.03
        social_delta = -0.1
        result = "Attended a meeting"

    elif action == "worry_about_finances":
        stress_delta = 0.1
        happiness_delta = -0.05
        result = "Worried about finances"
        emotional_changes["fear"] = 0.1
        emotional_changes["stress"] = 0.1

    else:
        result = f"Did: {action}"

    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    new_energy = clamp(state.energy + energy_delta)
    new_hunger = clamp(state.hunger + hunger_delta)
    new_social = clamp(state.social_need + social_delta)
    new_happiness = clamp(state.happiness + happiness_delta)
    new_stress = clamp(state.stress + stress_delta)
    new_balance = state.balance + balance_delta

    return {
        "action_result": result,
        "current_activity": action,
        "energy": new_energy,
        "hunger": new_hunger,
        "social_need": new_social,
        "happiness": new_happiness,
        "stress": new_stress,
        "balance": new_balance,
        "new_memories": new_memories,
        "emotional_changes": emotional_changes,
        "transactions": transactions,
    }


def reflect(state: CitizenState) -> dict[str, Any]:
    """Post-action reflection: generate memories and emotional updates."""
    messages = []

    if state.happiness < 0.3:
        messages.append({"role": "system", "content": f"{state.name} is feeling unhappy"})
    if state.stress > 0.8:
        messages.append({"role": "system", "content": f"{state.name} is very stressed"})
    if state.health < 0.3:
        messages.append({"role": "system", "content": f"{state.name} needs medical attention"})
    if state.balance < 0:
        messages.append({"role": "system", "content": f"{state.name} is in debt"})

    return {"messages": messages}


def build_citizen_graph(use_llm: bool = False) -> StateGraph:
    """Build the LangGraph state machine for citizen agent lifecycle."""
    workflow = StateGraph(CitizenState)

    workflow.add_node("perceive", perceive)

    if use_llm:
        from backend.app.agents.llm_decision import llm_decide, llm_reflect
        workflow.add_node("decide", llm_decide)
        workflow.add_node("act", act)
        workflow.add_node("reflect", llm_reflect)
    else:
        workflow.add_node("decide", decide)
        workflow.add_node("act", act)
        workflow.add_node("reflect", reflect)

    workflow.set_entry_point("perceive")
    workflow.add_edge("perceive", "decide")
    workflow.add_edge("decide", "act")
    workflow.add_edge("act", "reflect")
    workflow.add_edge("reflect", END)

    return workflow


citizen_graph = build_citizen_graph(use_llm=False).compile()

_llm_graph = None


def get_llm_citizen_graph():
    """Get the LLM-powered citizen graph (lazy-initialized)."""
    global _llm_graph
    if _llm_graph is None:
        from backend.app.services.llm_service import get_llm_service
        if get_llm_service().is_available:
            _llm_graph = build_citizen_graph(use_llm=True).compile()
    return _llm_graph


def citizen_to_state(citizen: Citizen, sim_hour: int, sim_day: int) -> CitizenState:
    """Convert a DB citizen model to agent state."""
    return CitizenState(
        citizen_id=str(citizen.id),
        name=citizen.name,
        age=citizen.age,
        occupation=citizen.occupation,
        personality=citizen.personality_traits or {},
        goals=citizen.goals or [],
        happiness=citizen.happiness,
        stress=citizen.stress,
        health=citizen.health,
        energy=citizen.energy,
        hunger=citizen.hunger,
        social_need=citizen.social_need,
        balance=citizen.balance,
        current_activity=citizen.current_activity,
        sim_hour=sim_hour,
        sim_day=sim_day,
    )


def apply_state_to_citizen(citizen: Citizen, state: CitizenState) -> None:
    """Apply agent state changes back to the DB model."""
    citizen.happiness = state.happiness
    citizen.stress = state.stress
    citizen.health = state.health
    citizen.energy = state.energy
    citizen.hunger = state.hunger
    citizen.social_need = state.social_need
    citizen.balance = state.balance
    citizen.current_activity = state.current_activity

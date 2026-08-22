"""
LLM-Powered Conversation Generator: Generates natural dialogue between
citizens using personality, relationship history, current events, and
emotional state. Falls back to template-based when LLM is unavailable.
"""

from __future__ import annotations

import json
import random
from datetime import datetime

import structlog

from backend.app.models.citizen import Citizen
from backend.app.services.llm_service import get_llm_service

log = structlog.get_logger()

CONVERSATION_SYSTEM = """You are generating a realistic conversation between citizens in a simulated city.
Each citizen has distinct personality traits, moods, and life circumstances.
Write dialogue that reflects their personalities and current emotional states.

Respond with ONLY a JSON object:
{
  "messages": [
    {"speaker": "<name>", "text": "<dialogue line>", "sentiment": "positive|neutral|negative"},
    ...
  ],
  "topic_summary": "<1-sentence summary of what they talked about>",
  "overall_sentiment": "positive|neutral|negative"
}

Rules:
- 2-5 messages total
- Each message is 1-2 sentences max
- Dialogue should feel natural and grounded
- Reflect personality differences in speaking style
- Reference current events or shared context when relevant"""

SOCIAL_POST_SYSTEM = """You are generating a social media post for a citizen in a simulated city.
The post should reflect their personality, mood, and current situation.

Respond with ONLY a JSON object:
{
  "content": "<the post text, 1-2 sentences>",
  "sentiment": "positive|neutral|negative",
  "hashtags": ["tag1", "tag2"]
}

Rules:
- Keep it brief and natural
- Match the citizen's personality (introverts are more reflective, extraverts more expressive)
- Reference their current activity or mood"""


def _describe_citizen(citizen: Citizen) -> str:
    personality = citizen.personality_traits or {}
    traits = []
    if personality.get("extraversion", 0.5) > 0.7:
        traits.append("outgoing")
    elif personality.get("extraversion", 0.5) < 0.3:
        traits.append("quiet/reserved")
    if personality.get("agreeableness", 0.5) > 0.7:
        traits.append("friendly")
    if personality.get("openness", 0.5) > 0.7:
        traits.append("curious")
    if personality.get("neuroticism", 0.5) > 0.7:
        traits.append("anxious")
    if personality.get("conscientiousness", 0.5) > 0.7:
        traits.append("disciplined")

    mood = []
    if citizen.happiness > 0.7:
        mood.append("happy")
    elif citizen.happiness < 0.3:
        mood.append("unhappy")
    if citizen.stress > 0.7:
        mood.append("stressed")

    desc = f"{citizen.name} (age {citizen.age}, {citizen.occupation or 'unemployed'})"
    if traits:
        desc += f" — personality: {', '.join(traits)}"
    if mood:
        desc += f" — feeling: {', '.join(mood)}"
    return desc


async def generate_llm_conversation(
    participants: list[Citizen],
    context: str | None = None,
    sim_time: datetime | None = None,
) -> dict | None:
    llm = get_llm_service()
    if not llm.is_available:
        return None

    if len(participants) < 2:
        return None

    citizen_descriptions = "\n".join(
        f"- {_describe_citizen(c)}" for c in participants
    )

    prompt_parts = [
        f"Participants:\n{citizen_descriptions}",
    ]
    if context:
        prompt_parts.append(f"Context: {context}")
    if sim_time:
        hour = sim_time.hour
        time_desc = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
        prompt_parts.append(f"Time: {time_desc}")

    prompt = "\n\n".join(prompt_parts)
    prompt += "\n\nGenerate their conversation."

    result = await llm.generate_json(
        prompt=prompt,
        system=CONVERSATION_SYSTEM,
        temperature=0.9,
    )

    if not result or "messages" not in result:
        return None

    return {
        "messages": result["messages"],
        "topic": result.get("topic_summary", "A conversation"),
        "sentiment": result.get("overall_sentiment", "neutral"),
    }


async def generate_llm_social_post(
    citizen: Citizen,
    context: str | None = None,
    sim_time: datetime | None = None,
) -> dict | None:
    llm = get_llm_service()
    if not llm.is_available:
        return None

    desc = _describe_citizen(citizen)
    prompt = f"Citizen: {desc}\n"
    if citizen.current_activity:
        prompt += f"Currently doing: {citizen.current_activity}\n"
    if context:
        prompt += f"City context: {context}\n"

    prompt += "\nGenerate their social media post."

    result = await llm.generate_json(
        prompt=prompt,
        system=SOCIAL_POST_SYSTEM,
        temperature=0.9,
    )

    if not result or "content" not in result:
        return None

    return {
        "content": result["content"],
        "sentiment": result.get("sentiment", "neutral"),
        "tags": result.get("hashtags", []),
    }


async def generate_llm_gossip(
    speaker: Citizen,
    subject_name: str,
    gossip_topic: str,
) -> str | None:
    llm = get_llm_service()
    if not llm.is_available:
        return None

    desc = _describe_citizen(speaker)
    prompt = (
        f"Citizen {desc} is spreading gossip about {subject_name}.\n"
        f"Topic: {gossip_topic}\n\n"
        f"Generate 1-2 sentences of gossip that {speaker.name} would say, "
        f"reflecting their personality. Just the gossip text, no JSON."
    )

    result = await llm.chat(
        messages=[{"role": "user", "content": prompt}],
        system="You generate brief, realistic gossip dialogue for a city simulation. Respond with just the gossip text.",
        temperature=0.9,
        max_tokens=100,
    )

    return result

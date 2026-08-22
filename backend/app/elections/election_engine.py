"""
Election System: Candidate generation, campaigning, voter opinion modeling,
debate effects, voting day, and result tabulation.
"""

from __future__ import annotations

import random
from datetime import datetime

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.citizen import Citizen
from backend.app.models.election import (
    Election, ElectionPhase, Candidate,
)

log = structlog.get_logger()

PARTY_PLATFORMS = {
    "Progressive Alliance": {
        "focus": ["healthcare", "education", "environment", "social_welfare"],
        "tax_stance": "higher",
        "spending": "increase_public_services",
    },
    "Liberty Coalition": {
        "focus": ["economy", "business", "deregulation", "tax_cuts"],
        "tax_stance": "lower",
        "spending": "reduce_government",
    },
    "Centrist Union": {
        "focus": ["infrastructure", "moderate_reform", "balanced_budget"],
        "tax_stance": "moderate",
        "spending": "balanced",
    },
    "Green Future": {
        "focus": ["environment", "sustainability", "renewable_energy"],
        "tax_stance": "moderate",
        "spending": "green_investment",
    },
}

SLOGANS = [
    "A City for Everyone",
    "Building Tomorrow Today",
    "Prosperity Through Unity",
    "Change We Can Trust",
    "Forward Together",
    "Strength in Community",
    "New Vision, Real Results",
    "People First, Always",
]

PHASE_DURATIONS = {
    ElectionPhase.ANNOUNCEMENT: 20,
    ElectionPhase.CAMPAIGNING: 80,
    ElectionPhase.DEBATE: 20,
    ElectionPhase.VOTING: 10,
    ElectionPhase.COUNTING: 5,
}


class ElectionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_election(self, name: str, sim_time: datetime, candidate_count: int = 4) -> Election:
        pop_result = await self.db.execute(
            select(func.count(Citizen.id)).where(Citizen.is_alive == True)  # noqa: E712
        )
        total_voters = pop_result.scalar() or 0

        election = Election(
            name=name,
            phase=ElectionPhase.ANNOUNCEMENT,
            total_voters=total_voters,
            phase_ticks_remaining=PHASE_DURATIONS[ElectionPhase.ANNOUNCEMENT],
            started_at=sim_time,
        )
        self.db.add(election)
        await self.db.flush()

        citizens_result = await self.db.execute(
            select(Citizen)
            .where(Citizen.is_alive == True, Citizen.age >= 25)  # noqa: E712
            .order_by(func.random())
            .limit(candidate_count)
        )
        candidate_citizens = list(citizens_result.scalars().all())

        parties = list(PARTY_PLATFORMS.keys())
        used_slogans = set()

        for i, citizen in enumerate(candidate_citizens):
            party = parties[i % len(parties)]
            available_slogans = [s for s in SLOGANS if s not in used_slogans]
            slogan = random.choice(available_slogans) if available_slogans else f"Vote for {citizen.name}"
            used_slogans.add(slogan)

            personality = citizen.personality_traits or {}
            base_popularity = (
                personality.get("extraversion", 0.5) * 0.3
                + personality.get("agreeableness", 0.5) * 0.25
                + personality.get("conscientiousness", 0.5) * 0.2
                + random.uniform(0.1, 0.3)
            )

            candidate = Candidate(
                election_id=election.id,
                citizen_id=citizen.id,
                name=citizen.name,
                party=party,
                platform=PARTY_PLATFORMS[party],
                slogan=slogan,
                popularity=min(1.0, base_popularity),
                campaign_funds=random.uniform(10000, 50000),
            )
            self.db.add(candidate)

        await self.db.flush()
        log.info("election_started", name=name, candidates=len(candidate_citizens), voters=total_voters)
        return election

    async def process_tick(self, sim_time: datetime) -> dict:
        result = await self.db.execute(
            select(Election).where(Election.is_active == True)  # noqa: E712
        )
        elections = list(result.scalars().all())

        stats = {"active_elections": len(elections), "events": []}

        for election in elections:
            election.phase_ticks_remaining -= 1

            if election.phase == ElectionPhase.CAMPAIGNING:
                await self._process_campaigning(election)
            elif election.phase == ElectionPhase.DEBATE:
                await self._process_debate(election)
            elif election.phase == ElectionPhase.VOTING:
                await self._process_voting(election)
            elif election.phase == ElectionPhase.COUNTING:
                await self._process_counting(election)

            if election.phase_ticks_remaining <= 0:
                next_phase = self._next_phase(election.phase)
                if next_phase:
                    election.phase = next_phase
                    election.phase_ticks_remaining = PHASE_DURATIONS.get(next_phase, 10)
                    stats["events"].append(f"{election.name}: entered {next_phase.value}")
                    log.info("election_phase_change", name=election.name, phase=next_phase.value)
                else:
                    election.phase = ElectionPhase.COMPLETED
                    election.is_active = False
                    election.ended_at = sim_time
                    await self._finalize_results(election)
                    stats["events"].append(f"{election.name}: completed")
                    log.info("election_completed", name=election.name, winner=election.winner_name)

        await self.db.flush()
        return stats

    async def _process_campaigning(self, election: Election) -> None:
        candidates_result = await self.db.execute(
            select(Candidate).where(Candidate.election_id == election.id)
        )
        candidates = list(candidates_result.scalars().all())

        for candidate in candidates:
            if candidate.campaign_funds > 100:
                spend = min(candidate.campaign_funds * 0.02, 500)
                candidate.campaign_funds -= spend
                boost = spend / 50000 * random.uniform(0.5, 1.5)
                candidate.popularity = min(1.0, candidate.popularity + boost)

            candidate.popularity += random.uniform(-0.005, 0.005)
            candidate.popularity = max(0.05, min(1.0, candidate.popularity))

    async def _process_debate(self, election: Election) -> None:
        candidates_result = await self.db.execute(
            select(Candidate).where(Candidate.election_id == election.id)
        )
        candidates = list(candidates_result.scalars().all())

        for candidate in candidates:
            citizen_result = await self.db.execute(
                select(Citizen).where(Citizen.id == candidate.citizen_id)
            )
            citizen = citizen_result.scalar_one_or_none()
            if not citizen:
                continue

            personality = citizen.personality_traits or {}
            debate_skill = (
                personality.get("openness", 0.5) * 0.4
                + personality.get("extraversion", 0.5) * 0.3
                + personality.get("conscientiousness", 0.5) * 0.3
            )

            performance = debate_skill * random.uniform(0.7, 1.3)
            shift = (performance - 0.5) * 0.02
            candidate.popularity = max(0.05, min(1.0, candidate.popularity + shift))

    async def _process_voting(self, election: Election) -> None:
        if election.votes_cast > 0:
            return

        candidates_result = await self.db.execute(
            select(Candidate).where(Candidate.election_id == election.id)
        )
        candidates = list(candidates_result.scalars().all())
        if not candidates:
            return

        citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        voters = list(citizens_result.scalars().all())

        total_popularity = sum(c.popularity for c in candidates)
        if total_popularity == 0:
            return

        for voter in voters:
            turnout_chance = 0.6
            personality = voter.personality_traits or {}
            turnout_chance += personality.get("conscientiousness", 0.5) * 0.2
            turnout_chance += personality.get("agreeableness", 0.5) * 0.1
            if voter.happiness < 0.3:
                turnout_chance += 0.15

            if random.random() > turnout_chance:
                continue

            weights = []
            for candidate in candidates:
                weight = candidate.popularity

                platform = candidate.platform or {}
                if voter.political_opinion is not None:
                    if platform.get("tax_stance") == "lower" and voter.political_opinion > 0.5:
                        weight *= 1.3
                    elif platform.get("tax_stance") == "higher" and voter.political_opinion < 0.5:
                        weight *= 1.3

                weight *= random.uniform(0.8, 1.2)
                weights.append(max(0.01, weight))

            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]

            chosen = random.choices(candidates, weights=probabilities, k=1)[0]
            chosen.votes += 1
            election.votes_cast += 1

        election.turnout_rate = election.votes_cast / max(election.total_voters, 1)

    async def _process_counting(self, election: Election) -> None:
        pass

    async def _finalize_results(self, election: Election) -> None:
        candidates_result = await self.db.execute(
            select(Candidate).where(Candidate.election_id == election.id)
        )
        candidates = list(candidates_result.scalars().all())

        total_votes = sum(c.votes for c in candidates)
        results = {}

        winner = None
        max_votes = 0

        for candidate in candidates:
            candidate.vote_share = candidate.votes / max(total_votes, 1)
            results[candidate.name] = {
                "party": candidate.party,
                "votes": candidate.votes,
                "vote_share": round(candidate.vote_share, 4),
            }
            if candidate.votes > max_votes:
                max_votes = candidate.votes
                winner = candidate

        if winner:
            winner.is_winner = True
            election.winner_id = winner.citizen_id
            election.winner_name = winner.name
            election.results = results

            citizens_result = await self.db.execute(
                select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
            )
            citizens = list(citizens_result.scalars().all())
            for citizen in citizens:
                shift = random.uniform(-0.02, 0.02)
                citizen.happiness = max(0.0, min(1.0, citizen.happiness + shift))

        log.info("election_results", winner=winner.name if winner else None, turnout=election.turnout_rate)

    def _next_phase(self, current: ElectionPhase) -> ElectionPhase | None:
        order = [
            ElectionPhase.ANNOUNCEMENT,
            ElectionPhase.CAMPAIGNING,
            ElectionPhase.DEBATE,
            ElectionPhase.VOTING,
            ElectionPhase.COUNTING,
        ]
        try:
            idx = order.index(current)
            return order[idx + 1] if idx + 1 < len(order) else None
        except ValueError:
            return None

    async def get_elections(self) -> list[dict]:
        result = await self.db.execute(
            select(Election).order_by(Election.created_at.desc())
        )
        elections = list(result.scalars().all())
        out = []
        for e in elections:
            candidates_result = await self.db.execute(
                select(Candidate).where(Candidate.election_id == e.id)
            )
            candidates = list(candidates_result.scalars().all())
            out.append({
                "id": str(e.id),
                "name": e.name,
                "phase": e.phase.value,
                "total_voters": e.total_voters,
                "votes_cast": e.votes_cast,
                "turnout_rate": round(e.turnout_rate, 4),
                "winner": e.winner_name,
                "is_active": e.is_active,
                "candidates": [
                    {
                        "name": c.name,
                        "party": c.party,
                        "slogan": c.slogan,
                        "popularity": round(c.popularity, 3),
                        "votes": c.votes,
                        "vote_share": round(c.vote_share, 4),
                        "is_winner": c.is_winner,
                    }
                    for c in candidates
                ],
                "results": e.results,
            })
        return out

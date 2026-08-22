"""
Simulation Engine: Orchestrates the tick-based simulation loop.
Processes all citizens each tick through their agent graph.
Phase 5: Adds weather, crime, healthcare, education, housing, and news.
Phase 6: Adds culture, environment, demographics, infrastructure, and tourism.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import async_session

from backend.app.agents.citizen_agent import (
    CitizenState,
    citizen_graph,
    get_llm_citizen_graph,
    citizen_to_state,
    apply_state_to_citizen,
)
from backend.app.communication.communication_engine import CommunicationEngine
from backend.app.communication.relationship_engine import RelationshipEngine
from backend.app.crime.crime_engine import CrimeEngine
from backend.app.culture.culture_engine import CultureEngine
from backend.app.demographics.demographics_engine import DemographicsEngine
from backend.app.disasters.disaster_engine import DisasterEngine
from backend.app.education.education_engine import EducationEngine
from backend.app.elections.election_engine import ElectionEngine
from backend.app.engine.world_clock import WorldClock
from backend.app.environment.environment_engine import EnvironmentEngine
from backend.app.events.event_engine import EventEngine
from backend.app.government.government_ai import GovernmentAI
from backend.app.healthcare.healthcare_engine import HealthcareEngine
from backend.app.housing.housing_engine import HousingEngine
from backend.app.infrastructure.infrastructure_engine import InfrastructureEngine
from backend.app.memory.memory_engine import MemoryEngine
from backend.app.models.citizen import Citizen
from backend.app.models.city import District
from backend.app.models.economy import Transaction, TransactionType
from backend.app.models.event import CityEvent
from backend.app.models.memory import MemoryType
from backend.app.analytics.history import MetricsHistoryTracker
from backend.app.news.news_engine import NewsEngine
from backend.app.pandemic.pandemic_engine import PandemicEngine
from backend.app.schemas.simulation import SimulationStatus, TickResult
from backend.app.social_media.social_media_engine import SocialMediaEngine
from backend.app.tourism.tourism_engine import TourismEngine
from backend.app.traffic.traffic_engine import TrafficEngine
from backend.app.weather.weather_engine import WeatherEngine

log = structlog.get_logger()


class SimulationEngine:
    def __init__(self, db: AsyncSession, time_scale: int = 60):
        self.db = db
        self.clock = WorldClock(time_scale=time_scale)
        self.status = SimulationStatus.STOPPED
        self.memory_engine = MemoryEngine(db)
        self.communication_engine = CommunicationEngine(db)
        self.traffic_engine = TrafficEngine(db)
        self.government_ai = GovernmentAI(db)
        self.relationship_engine = RelationshipEngine(db)
        self.event_engine = EventEngine(db)
        self.metrics_tracker = MetricsHistoryTracker(db)
        self.disaster_engine = DisasterEngine(db)
        self.pandemic_engine = PandemicEngine(db)
        self.election_engine = ElectionEngine(db)
        self.social_media_engine = SocialMediaEngine(db)
        self.weather_engine = WeatherEngine(db)
        self.crime_engine = CrimeEngine(db)
        self.healthcare_engine = HealthcareEngine(db)
        self.education_engine = EducationEngine(db)
        self.housing_engine = HousingEngine(db)
        self.news_engine = NewsEngine(db)
        self.culture_engine = CultureEngine(db)
        self.environment_engine = EnvironmentEngine(db)
        self.demographics_engine = DemographicsEngine(db)
        self.infrastructure_engine = InfrastructureEngine(db)
        self.tourism_engine = TourismEngine(db)
        self._task: asyncio.Task | None = None
        self._tick_results: list[TickResult] = []
        self._last_gov_cycle_day: int = -1
        self._last_salary_day: int = -1
        self._seeded_phase5: bool = False
        self._seeded_phase6: bool = False
        self._db_lock = asyncio.Lock()

    @property
    def current_tick(self) -> int:
        return self.clock.tick_count

    @property
    def sim_time(self) -> datetime:
        return self.clock.sim_time

    async def start(self, tick_interval: float = 1.0) -> None:
        if self.status == SimulationStatus.RUNNING:
            return
        self.status = SimulationStatus.RUNNING
        log.info("simulation_started", time=self.clock.time_str())
        self._task = asyncio.create_task(self._run_loop(tick_interval))

    async def stop(self) -> None:
        self.status = SimulationStatus.STOPPED
        if self._task:
            self._task.cancel()
            self._task = None
        log.info("simulation_stopped", tick=self.current_tick)

    async def pause(self) -> None:
        self.status = SimulationStatus.PAUSED
        log.info("simulation_paused", tick=self.current_tick)

    async def resume(self, tick_interval: float = 1.0) -> None:
        if self.status != SimulationStatus.PAUSED:
            return
        self.status = SimulationStatus.RUNNING
        self._task = asyncio.create_task(self._run_loop(tick_interval))
        log.info("simulation_resumed", tick=self.current_tick)

    async def step(self, steps: int = 1) -> list[TickResult]:
        if self.status == SimulationStatus.RUNNING:
            # The background loop already owns self.db; stepping concurrently would
            # race two _process_tick() calls on the same session.
            return self._tick_results[-steps:] if self._tick_results else []
        results = []
        for _ in range(steps):
            result = await self._process_tick()
            results.append(result)
        return results

    async def _run_loop(self, tick_interval: float) -> None:
        try:
            while self.status == SimulationStatus.RUNNING:
                await self._process_tick()
                await asyncio.sleep(tick_interval)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("simulation_error")
            self.status = SimulationStatus.STOPPED

    async def _seed_phase5_data(self, citizens: list) -> None:
        if self._seeded_phase5:
            return
        self._seeded_phase5 = True

        districts = await self._get_districts()
        if not districts:
            return

        try:
            await self.crime_engine.seed_police_units(districts)
            await self.healthcare_engine.seed_hospitals(districts)
            await self.education_engine.seed_schools(districts)
            await self.housing_engine.seed_properties(districts, len(citizens))
            await self.news_engine.seed_outlets()
            await self.db.flush()
            log.info("phase5_seeded")
        except Exception as e:
            log.warning("phase5_seed_error", error=str(e))

    async def _seed_phase6_data(self) -> None:
        if self._seeded_phase6:
            return
        self._seeded_phase6 = True

        districts = await self._get_districts()
        if not districts:
            return

        try:
            await self.culture_engine.seed_venues(districts)
            await self.environment_engine.seed_state()
            await self.infrastructure_engine.seed_grids(districts)
            await self.tourism_engine.seed_hotels_and_attractions(districts)
            await self.db.flush()
            log.info("phase6_seeded")
        except Exception as e:
            log.warning("phase6_seed_error", error=str(e))

    async def _get_districts(self) -> list[dict]:
        result = await self.db.execute(select(District))
        districts = list(result.scalars().all())
        return [{
            "id": d.id,
            "name": d.name,
            "safety": d.safety_index,
            "wealth": d.wealth_index,
            "center": [d.center_x, d.center_y],
            "radius": d.radius,
        } for d in districts]

    async def _process_tick(self) -> TickResult:
        start = time.monotonic()
        phase_timings: list[tuple[str, float]] = []
        _phase_t0 = start

        def _mark(phase: str) -> None:
            nonlocal _phase_t0
            now = time.monotonic()
            phase_timings.append((phase, (now - _phase_t0) * 1000))
            _phase_t0 = now

        self.clock.tick()

        citizens_result = await self.db.execute(
            select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
        )
        citizens = list(citizens_result.scalars().all())

        _mark("fetch_citizens")

        await self._seed_phase5_data(citizens)
        await self._seed_phase6_data()
        _mark("seed_phase5_6")

        transaction_count = 0
        events_triggered = 0
        conversations_count = 0
        trips_count = 0
        gov_decisions = 0

        # --- Phase 5: Weather update ---
        weather_data = await self.weather_engine.process_tick(
            self.clock.sim_time, self.clock.day, self.clock.hour
        )

        # Apply weather effects to citizens
        if weather_data:
            h_mod = weather_data.get("happiness_modifier", 0)
            health_mod = weather_data.get("health_modifier", 0)
            for citizen in citizens:
                citizen.happiness = max(0.0, min(1.0, citizen.happiness + h_mod * 0.1))
                citizen.health = max(0.1, min(1.0, citizen.health + health_mod * 0.1))

        _mark("weather")

        # --- Traffic: update congestion based on time ---
        traffic_stats = await self.traffic_engine.process_tick(self.clock.hour)
        _mark("traffic")

        # --- Process each citizen through their agent ---
        # The agent graph itself (perceive/decide/act/reflect) never touches the DB, so
        # all citizens' decisions can run concurrently across the thread pool instead of
        # one full round-trip at a time — this is the dominant cost at real population
        # sizes. Only the DB writes below stay sequential (they share self.db).
        states = [citizen_to_state(citizen, self.clock.hour, self.clock.day) for citizen in citizens]
        result_states = await asyncio.gather(*(self._run_agent(state) for state in states))
        _mark("agent_graph_parallel")

        for citizen, result_state in zip(citizens, result_states):
            apply_state_to_citizen(citizen, result_state)

            for mem_data in result_state.new_memories:
                await self.memory_engine.store_memory(
                    citizen_id=citizen.id,
                    content=mem_data["content"],
                    memory_type=MemoryType(mem_data.get("type", "episodic")),
                    sim_time=self.clock.sim_time,
                    importance=mem_data.get("importance", 0.5),
                )

            for tx_data in result_state.transactions:
                tx = Transaction(
                    citizen_id=citizen.id,
                    transaction_type=TransactionType(tx_data.get("type", "purchase")),
                    amount=tx_data["amount"],
                    description=tx_data.get("desc", ""),
                    sim_timestamp=self.clock.sim_time,
                )
                self.db.add(tx)
                transaction_count += 1

            if result_state.current_activity in ("commute_to_work", "commute_home"):
                origin = citizen.current_location_id
                dest = (
                    citizen.workplace_id
                    if result_state.current_activity == "commute_to_work"
                    else citizen.home_location_id
                )
                trip = await self.traffic_engine.calculate_trip(
                    citizen, origin, dest, self.clock.sim_time
                )
                if trip:
                    trips_count += 1
                    citizen.stress = min(1.0, citizen.stress + trip.congestion_experienced * 0.02)
                    citizen.balance -= trip.cost

        _mark("agent_apply_and_db_writes")

        # --- Communication: multi-agent conversations ---
        comm_stats = await self.communication_engine.process_tick_conversations(
            citizens, self.clock.sim_time
        )
        conversations_count = comm_stats.get("conversations", 0)

        if conversations_count > 0 and len(citizens) >= 2:
            import random
            for _ in range(min(conversations_count, 5)):
                pair = random.sample(citizens, 2)
                await self.relationship_engine.record_interaction(
                    pair[0].id, pair[1].id,
                    positive=random.random() > 0.3,
                    sim_time=self.clock.sim_time,
                )
        _mark("communication")

        # --- Events: random chance of city events ---
        random_event = await self.event_engine.random_event_chance(
            self.clock.sim_time, probability=0.003
        )
        if random_event:
            events_triggered += 1
            await self.event_engine.apply_event_effects(random_event)

        await self._process_active_events()
        _mark("events")

        # --- Phase 3: Disaster simulation ---
        disaster_stats = await self.disaster_engine.process_tick(self.clock.sim_time)
        _mark("disaster")

        # --- Phase 3: Pandemic simulation ---
        pandemic_stats = await self.pandemic_engine.process_tick(self.clock.sim_time)
        _mark("pandemic")

        # --- Phase 3: Election processing ---
        election_stats = await self.election_engine.process_tick(self.clock.sim_time)
        _mark("election")

        # --- Phase 3: Social media simulation ---
        social_context = {
            "active_disasters": disaster_stats.get("active_disasters", 0),
            "active_pandemics": pandemic_stats.get("active_pandemics", 0),
            "active_elections": election_stats.get("active_elections", 0),
        }
        social_media_stats = await self.social_media_engine.process_tick(
            self.clock.sim_time, city_context=social_context
        )
        _mark("social_media")

        # --- Phase 5: Crime simulation ---
        districts = await self._get_districts()
        crime_modifier = weather_data.get("crime_modifier", 1.0) if weather_data else 1.0
        crime_stats = await self.crime_engine.process_tick(
            self.clock.sim_time, self.clock.hour, citizens, districts, crime_modifier
        )
        _mark("crime")

        # --- Phase 5: Healthcare simulation ---
        healthcare_stats = await self.healthcare_engine.process_tick(
            self.clock.sim_time, citizens, weather_data
        )
        _mark("healthcare")

        # --- Phase 5: Education processing ---
        education_stats = await self.education_engine.process_tick(
            self.clock.sim_time, citizens
        )
        _mark("education")

        # --- Phase 5: Housing / rent collection ---
        housing_stats = await self.housing_engine.process_tick(
            self.clock.sim_time, self.clock.day, citizens
        )
        _mark("housing")

        # --- Phase 5: News generation ---
        news_context = {
            **social_context,
            "crimes_generated": crime_stats.get("crimes_generated", 0),
            "weather_condition": weather_data.get("condition", "clear") if weather_data else "clear",
        }
        news_stats = await self.news_engine.process_tick(self.clock.sim_time, news_context)
        _mark("news")

        # --- Phase 6: Culture & entertainment ---
        culture_stats = await self.culture_engine.process_tick(self.clock.sim_time, citizens)
        _mark("culture")

        # --- Phase 6: Environment & sustainability ---
        weather_condition = weather_data.get("condition", "clear") if weather_data else "clear"
        environment_stats = await self.environment_engine.process_tick(
            population=len(citizens), weather_condition=weather_condition
        )
        _mark("environment")

        # --- Phase 6: Demographics & population ---
        demographics_stats = await self.demographics_engine.process_tick(
            self.clock.sim_time, self.current_tick, citizens
        )
        _mark("demographics")

        # --- Phase 6: Infrastructure & utilities ---
        infrastructure_stats = await self.infrastructure_engine.process_tick(population=len(citizens))
        _mark("infrastructure")

        # --- Phase 6: Tourism ---
        avg_happiness = sum(c.happiness for c in citizens) / len(citizens) if citizens else 0.5
        tourism_stats = await self.tourism_engine.process_tick(
            city_happiness=avg_happiness, weather_condition=weather_condition
        )
        _mark("tourism")

        # --- Government AI: run once per sim day at noon ---
        if self.clock.hour == 12 and self.clock.day != self._last_gov_cycle_day:
            self._last_gov_cycle_day = self.clock.day
            metrics = await self.get_metrics()
            metrics["avg_congestion"] = traffic_stats.get("avg_congestion", 0)
            decisions = await self.government_ai.run_government_cycle(
                metrics, self.clock.sim_time
            )
            gov_decisions = len(decisions)

        # --- Economy: process daily salaries at 6 PM ---
        if self.clock.hour == 18 and self.clock.day != self._last_salary_day:
            self._last_salary_day = self.clock.day
            from backend.app.economy.economy_engine import EconomyEngine
            econ = EconomyEngine(self.db)
            await econ.process_salaries(self.clock.sim_time)
            await econ.process_business_revenue(self.clock.sim_time)

        _mark("gov_and_salary")
        await self.db.commit()
        _mark("commit")

        log.info(
            "tick_phase_timings",
            tick=self.current_tick,
            population=len(citizens),
            total_ms=round((time.monotonic() - start) * 1000, 1),
            phases={name: round(ms, 1) for name, ms in phase_timings},
        )

        duration = (time.monotonic() - start) * 1000
        result = TickResult(
            tick=self.current_tick,
            sim_time=self.clock.time_str(),
            citizens_processed=len(citizens),
            events_triggered=events_triggered,
            transactions=transaction_count,
            duration_ms=round(duration, 2),
        )

        self._tick_results.append(result)
        if len(self._tick_results) > 1000:
            self._tick_results = self._tick_results[-500:]

        if self.current_tick % 10 == 0:
            snapshot_metrics = await self.get_metrics()
            snapshot_metrics["conversations"] = conversations_count
            snapshot_metrics["trips"] = trips_count
            snapshot_metrics["avg_congestion"] = traffic_stats.get("avg_congestion", 0)
            snapshot_metrics["active_disasters"] = disaster_stats.get("active_disasters", 0)
            snapshot_metrics["pandemic_active_cases"] = pandemic_stats.get("active_cases", 0)
            snapshot_metrics["trending_topics"] = social_media_stats.get("trending_topics", 0)
            snapshot_metrics["weather_condition"] = weather_data.get("condition", "clear") if weather_data else "clear"
            snapshot_metrics["crimes"] = crime_stats.get("crimes_generated", 0)
            snapshot_metrics["hospitalizations"] = healthcare_stats.get("hospitalizations", 0)
            snapshot_metrics["news_articles"] = news_stats.get("articles_generated", 0)
            snapshot_metrics["venue_revenue"] = culture_stats.get("venue_revenue", 0)
            snapshot_metrics["active_festivals"] = culture_stats.get("active_festivals", 0)
            snapshot_metrics["air_quality"] = environment_stats.get("air_quality", 0)
            snapshot_metrics["carbon_emissions"] = environment_stats.get("carbon_emissions", 0)
            snapshot_metrics["births"] = demographics_stats.get("births", 0)
            snapshot_metrics["deaths"] = demographics_stats.get("deaths", 0)
            snapshot_metrics["utility_outages"] = infrastructure_stats.get("outages", 0)
            snapshot_metrics["active_tourists"] = tourism_stats.get("active_tourists", 0)
            snapshot_metrics["tourism_revenue"] = tourism_stats.get("tourism_revenue", 0)
            await self.metrics_tracker.record_snapshot(
                self.current_tick, self.clock.sim_time, snapshot_metrics
            )

            log.info(
                "tick_processed",
                tick=self.current_tick,
                sim_time=self.clock.time_str(),
                citizens=len(citizens),
                weather=weather_data.get("condition", "?") if weather_data else "?",
                conversations=conversations_count,
                trips=trips_count,
                disasters=disaster_stats.get("active_disasters", 0),
                pandemic_cases=pandemic_stats.get("active_cases", 0),
                crimes=crime_stats.get("crimes_generated", 0),
                hospitalizations=healthcare_stats.get("hospitalizations", 0),
                gov_decisions=gov_decisions,
                duration_ms=result.duration_ms,
            )

        return result

    async def _run_agent(self, state: CitizenState) -> CitizenState:
        llm_graph = get_llm_citizen_graph()
        if llm_graph is not None:
            result = await llm_graph.ainvoke(state)
        else:
            result = await asyncio.to_thread(citizen_graph.invoke, state)
        if isinstance(result, dict):
            for key, value in result.items():
                if hasattr(state, key):
                    setattr(state, key, value)
        return state

    async def _process_active_events(self) -> None:
        events_result = await self.db.execute(
            select(CityEvent).where(CityEvent.is_active == True)  # noqa: E712
        )
        events = list(events_result.scalars().all())

        for event in events:
            event.remaining_ticks -= 1
            await self.event_engine.apply_event_effects(event)

            if event.remaining_ticks <= 0:
                event.is_active = False
                event.sim_ended_at = self.clock.sim_time
                await self.communication_engine.broadcast_emergency_alert(
                    f"{event.name} has ended. The city is recovering.",
                    self.clock.sim_time,
                )
                log.info("event_ended", event_name=event.name)

    async def get_metrics(self) -> dict:
        """Read-only snapshot. Uses its own short-lived session (never self.db) so a
        concurrent request (e.g. the /status endpoint polled while a tick is mid-flush)
        can't collide with the simulation loop's own session and crash it."""
        async with async_session() as db:
            citizens_result = await db.execute(
                select(Citizen).where(Citizen.is_alive == True)  # noqa: E712
            )
            citizens = list(citizens_result.scalars().all())

            if not citizens:
                return {"population": 0}

            population = len(citizens)
            employed = sum(1 for c in citizens if c.occupation != "unemployed")

            active_events_result = await db.execute(
                select(CityEvent).where(CityEvent.is_active == True)  # noqa: E712
            )
            active_events = len(list(active_events_result.scalars().all()))

        return {
            "population": population,
            "employed": employed,
            "unemployed": population - employed,
            "unemployment_rate": (population - employed) / population if population else 0,
            "avg_happiness": sum(c.happiness for c in citizens) / population,
            "avg_health": sum(c.health for c in citizens) / population,
            "avg_stress": sum(c.stress for c in citizens) / population,
            "total_gdp": sum(c.balance for c in citizens),
            "avg_income": sum(c.salary for c in citizens) / population,
            "active_events": active_events,
            "sim_time": self.clock.time_str(),
            "tick": self.current_tick,
        }

    def get_recent_ticks(self, count: int = 50) -> list[TickResult]:
        return self._tick_results[-count:]

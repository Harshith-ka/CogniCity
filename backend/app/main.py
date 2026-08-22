"""
AI Digital Twin City — FastAPI Application
"""

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.api import ai_advisor as api_ai_advisor
from backend.app.api import crime as api_crime
from backend.app.api import disasters as api_disasters
from backend.app.api import education as api_education
from backend.app.api import elections as api_elections
from backend.app.api import graph as api_graph
from backend.app.api import healthcare as api_healthcare
from backend.app.api import housing as api_housing
from backend.app.api import news as api_news
from backend.app.api import pandemic as api_pandemic
from backend.app.api import social_media as api_social_media
from backend.app.api import vector_memory as api_vector_memory
from backend.app.api import culture as api_culture
from backend.app.api import demographics as api_demographics
from backend.app.api import environment as api_environment
from backend.app.api import infrastructure as api_infrastructure
from backend.app.api import tourism as api_tourism
from backend.app.api import weather as api_weather
from backend.app.api.routes import (
    simulation, citizens, events, analytics, economy, city,
    websocket, communication, traffic, government, relationships,
)
from backend.app.api.routes.simulation import set_simulation_engine
from backend.app.core.config import settings
from backend.app.core.database import engine as db_engine, async_session, Base
from backend.app.core.logging import setup_logging
from backend.app.engine.city_generator import generate_city
from backend.app.engine.simulation import SimulationEngine

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("starting_app", app=settings.app_name)

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        from sqlalchemy import select
        from backend.app.models.citizen import Citizen
        from backend.app.models.relationship import Relationship

        result = await db.execute(select(Citizen).limit(1))
        if result.scalar_one_or_none() is None:
            log.info("seeding_city", population=settings.initial_population)
            await generate_city(db, population=settings.initial_population, seed=settings.random_seed)

            citizens_result = await db.execute(
                select(Citizen).where(Citizen.is_alive == True).limit(200)  # noqa: E712
            )
            citizens = list(citizens_result.scalars().all())

            from backend.app.communication.relationship_engine import RelationshipEngine
            rel_engine = RelationshipEngine(db)
            await rel_engine.seed_relationships(citizens)
            await db.commit()

    async with async_session() as db:
        sim_engine = SimulationEngine(db, time_scale=settings.simulation_time_scale)
        set_simulation_engine(sim_engine)
        app.state.simulation_engine = sim_engine

    log.info("app_ready")
    yield

    if hasattr(app.state, "simulation_engine"):
        await app.state.simulation_engine.stop()

    await db_engine.dispose()
    log.info("app_shutdown")


app = FastAPI(
    title="AI Digital Twin City",
    description="Multi-Agent Autonomous Smart City Simulation Platform",
    version="6.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routes
app.include_router(simulation.router, prefix="/api")
app.include_router(citizens.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(economy.router, prefix="/api")
app.include_router(city.router, prefix="/api")

# Phase 2 routes
app.include_router(communication.router, prefix="/api")
app.include_router(traffic.router, prefix="/api")
app.include_router(government.router, prefix="/api")
app.include_router(relationships.router, prefix="/api")

# Phase 3 routes
app.include_router(api_disasters.router)
app.include_router(api_pandemic.router)
app.include_router(api_elections.router)
app.include_router(api_social_media.router)

# Phase 4 routes
app.include_router(api_ai_advisor.router)
app.include_router(api_vector_memory.router)
app.include_router(api_graph.router)

# Phase 5 routes
app.include_router(api_weather.router)
app.include_router(api_crime.router)
app.include_router(api_healthcare.router)
app.include_router(api_education.router)
app.include_router(api_housing.router)
app.include_router(api_news.router)

# Phase 6 routes
app.include_router(api_culture.router)
app.include_router(api_environment.router)
app.include_router(api_demographics.router)
app.include_router(api_infrastructure.router)
app.include_router(api_tourism.router)

# WebSocket
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {
        "name": "AI Digital Twin City",
        "version": "6.0.0",
        "phase": 6,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/city3d")
async def city_3d_view():
    return FileResponse(STATIC_DIR / "city3d.html")

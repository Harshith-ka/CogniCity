"""
AI Digital Twin City — FastAPI Application
"""

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.auth.dependencies import require_feature
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
from backend.app.api import agent_eval as api_agent_eval
from backend.app.api import twin_platform as api_twin_platform
from backend.app.api import auth as api_auth
from backend.app.api import admin as api_admin
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
        # create_all only creates whole new tables — it never alters an existing one, so
        # the x/y columns added to Hospital/School/PoliceUnit for exact Build Mode
        # placement need an explicit, idempotent ALTER TABLE (no Alembic in this project).
        from sqlalchemy import text
        for table in ("hospitals", "schools", "police_units"):
            await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS x DOUBLE PRECISION'))
            await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS y DOUBLE PRECISION'))
        await conn.execute(text(
            "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS allowed_environments JSON DEFAULT '[]'"
        ))
        await conn.execute(text(
            "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS allowed_modules JSON DEFAULT '[]'"
        ))
        await conn.execute(text(
            "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS credits_balance DOUBLE PRECISION DEFAULT 0.0"
        ))

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

    from backend.app.twin_platform.registry import register_all
    register_all()

    async with async_session() as db:
        from sqlalchemy import select
        from backend.app.models.auth import PlatformUser, UserRole
        from backend.app.auth.security import hash_password

        result = await db.execute(select(PlatformUser).where(PlatformUser.role == UserRole.SUPER_ADMIN))
        if result.scalar_one_or_none() is None:
            db.add(PlatformUser(
                email=settings.initial_admin_email.lower(),
                hashed_password=hash_password(settings.initial_admin_password),
                name="Platform Admin",
                role=UserRole.SUPER_ADMIN,
                organization_id=None,
            ))
            await db.commit()
            log.info("seeded_super_admin", email=settings.initial_admin_email)

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

# Phase 2 routes — each gated behind its feature-module entitlement (see
# backend/app/core/feature_modules.py). The dependency lives on the include_router
# call, not inside the router files themselves, so none of these files needed to
# change; an unauthenticated caller or an org with no restrictions set is unaffected.
app.include_router(communication.router, prefix="/api", dependencies=[Depends(require_feature("communication"))])
app.include_router(traffic.router, prefix="/api", dependencies=[Depends(require_feature("traffic"))])
app.include_router(government.router, prefix="/api", dependencies=[Depends(require_feature("government"))])
app.include_router(relationships.router, prefix="/api", dependencies=[Depends(require_feature("relationships"))])

# Phase 3 routes
app.include_router(api_disasters.router, dependencies=[Depends(require_feature("disasters"))])
app.include_router(api_pandemic.router, dependencies=[Depends(require_feature("pandemic"))])
app.include_router(api_elections.router, dependencies=[Depends(require_feature("elections"))])
app.include_router(api_social_media.router, dependencies=[Depends(require_feature("social_media"))])

# Phase 4 routes — vector_memory is AI Advisor's internal RAG store, not a standalone
# customer-facing tab, so it isn't independently gated.
app.include_router(api_ai_advisor.router, dependencies=[Depends(require_feature("ai_advisor"))])
app.include_router(api_vector_memory.router)
app.include_router(api_graph.router, dependencies=[Depends(require_feature("graph"))])

# Phase 5 routes
app.include_router(api_weather.router, dependencies=[Depends(require_feature("weather"))])
app.include_router(api_crime.router, dependencies=[Depends(require_feature("crime"))])
app.include_router(api_healthcare.router, dependencies=[Depends(require_feature("healthcare"))])
app.include_router(api_education.router, dependencies=[Depends(require_feature("education"))])
app.include_router(api_housing.router, dependencies=[Depends(require_feature("housing"))])
app.include_router(api_news.router, dependencies=[Depends(require_feature("news"))])

# Phase 6 routes
app.include_router(api_culture.router, dependencies=[Depends(require_feature("culture"))])
app.include_router(api_environment.router, dependencies=[Depends(require_feature("environment"))])
app.include_router(api_demographics.router, dependencies=[Depends(require_feature("demographics"))])
app.include_router(api_infrastructure.router, dependencies=[Depends(require_feature("infrastructure"))])
app.include_router(api_tourism.router, dependencies=[Depends(require_feature("tourism"))])
# Premium platform capabilities — gates the marketplace/sandbox as a whole (both
# listing and running); allowed_environments on the org then further narrows *which*
# environments within an entitled marketplace. Unauthenticated calls are unaffected,
# same as every other require_feature gate.
app.include_router(api_twin_platform.router, dependencies=[Depends(require_feature("twin_platform"))])
app.include_router(api_auth.router)
app.include_router(api_admin.router)
app.include_router(api_agent_eval.router, dependencies=[Depends(require_feature("agent_eval"))])

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
    # This view gets iterated on constantly during development; FileResponse alone lets
    # browsers cache it heuristically (no explicit Cache-Control), which has repeatedly
    # meant a real fix landing here didn't visibly do anything until a hard refresh —
    # confusing and hard to distinguish from the fix actually failing. Force no caching.
    return FileResponse(
        STATIC_DIR / "city3d.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@app.get("/dashboard")
async def dashboard_view():
    # Same no-cache reasoning as /city3d below — this was the one static view still
    # missing it, which is exactly why an edit to dashboard.html stopped showing up
    # in the browser without a hard refresh.
    return FileResponse(
        STATIC_DIR / "dashboard.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@app.get("/admin")
async def admin_portal_view():
    # Iterated on like city3d — force no caching so a fix here doesn't require the
    # user to know to hard-refresh before they can see it took effect.
    return FileResponse(
        STATIC_DIR / "admin.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )

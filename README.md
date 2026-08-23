# AI Digital Twin City

A next-generation simulation platform where thousands of autonomous AI citizens live inside a realistic virtual city. Every citizen has memory, goals, relationships, occupations, schedules, and evolving behaviors.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+ (or use Docker)

### Option 1: Docker (Recommended)

```bash
# Start all services
docker compose up -d

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
# Operational dashboard (Streamlit) at http://localhost:8501
# 3D city view & Urban Planner at http://localhost:8000/city3d
# Multi-tenant admin portal at http://localhost:8000/admin
```

Seeded super-admin login (change immediately outside local dev — see `.env.example`'s Security section): `admin@cognicity.local` / `changeme123`.

### Option 2: Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy env file
cp .env.example .env

# Start PostgreSQL and Redis (via Docker)
docker compose up -d postgres redis

# Run the API server
python scripts/run_dev.py

# In another terminal, run the dashboard
streamlit run frontend/dashboard.py
```

### Seed the City

The city auto-seeds on first startup. To manually seed:

```bash
python scripts/seed_city.py
```

## API Endpoints

### Core (Phase 1)
| Endpoint | Description |
|---|---|
| `GET /api/simulation/status` | Current simulation state |
| `POST /api/simulation/control` | Start/stop/pause/step simulation |
| `GET /api/citizens/` | List citizens |
| `GET /api/citizens/{id}` | Get citizen details |
| `GET /api/citizens/{id}/memories` | Get citizen memories |
| `GET /api/analytics/metrics` | City-wide metrics |
| `GET /api/analytics/population` | Population breakdown |
| `GET /api/analytics/history` | Historical metrics time-series |
| `GET /api/economy/businesses` | List businesses |
| `GET /api/economy/stats` | Economy statistics |
| `GET /api/events/` | List events |
| `POST /api/events/trigger` | Trigger a city event |
| `GET /api/city/districts` | List districts |
| `GET /api/city/map` | City map data |
| `WS /ws/simulation` | Real-time updates |

### Phase 2
| Endpoint | Description |
|---|---|
| `GET /api/communication/conversations` | Recent conversations |
| `GET /api/communication/citizens/{id}/conversations` | Citizen's conversations |
| `GET /api/communication/social-feed` | Social media feed |
| `POST /api/communication/emergency-alert` | Broadcast emergency |
| `GET /api/traffic/stats` | Traffic statistics |
| `GET /api/traffic/congestion` | Congestion map data |
| `GET /api/traffic/trips` | Recent trips |
| `GET /api/traffic/routes` | Transit routes |
| `GET /api/government/policies` | Active policies |
| `GET /api/government/budgets` | Department budgets |
| `POST /api/government/run-cycle` | Force government decisions |
| `GET /api/relationships/stats` | Social network stats |
| `GET /api/relationships/citizens/{id}` | Citizen relationships |
| `GET /api/relationships/citizens/{id}/graph` | Social graph |
| `POST /api/relationships/seed` | Seed initial relationships |

### Phase 3
| Endpoint | Description |
|---|---|
| `GET /api/disasters/active` | Active disasters |
| `GET /api/disasters/history` | Disaster history |
| `POST /api/disasters/trigger` | Trigger a disaster |
| `GET /api/pandemic/stats` | Pandemic statistics |
| `POST /api/pandemic/start` | Start a pandemic |
| `POST /api/pandemic/lockdown` | Toggle lockdown |
| `POST /api/pandemic/mask-mandate` | Toggle mask mandate |
| `POST /api/pandemic/vaccinate` | Start vaccination |
| `GET /api/elections/` | List elections |
| `POST /api/elections/start` | Start an election |
| `GET /api/social-media/trending` | Trending topics |
| `GET /api/social-media/opinion-shifts` | Opinion shifts |
| `POST /api/social-media/trigger-topic` | Launch a topic |

### Phase 4
| Endpoint | Description |
|---|---|
| `GET /api/ai-advisor/status` | AI advisor availability |
| `GET /api/ai-advisor/analyze` | Analyze city state |
| `POST /api/ai-advisor/scenario` | What-if scenario analysis |
| `GET /api/ai-advisor/report` | Generate city report |
| `POST /api/ai-advisor/ask` | Ask the advisor a question |
| `GET /api/vector-memory/status` | Vector store status |
| `POST /api/vector-memory/search` | Semantic memory search |
| `POST /api/vector-memory/context-search` | Context-aware memory search |
| `GET /api/graph/status` | Neo4j graph stats |
| `POST /api/graph/sync` | Sync Postgres → Neo4j |
| `GET /api/graph/influencers` | Top influencers |
| `GET /api/graph/shortest-path/{a}/{b}` | Shortest social path |
| `GET /api/graph/influence-path/{a}/{b}` | Influence propagation path |
| `GET /api/graph/communities` | Community detection |
| `GET /api/graph/district-connections` | Inter-district connections |

### Phase 5
| Endpoint | Description |
|---|---|
| `GET /api/weather/current` | Current weather conditions |
| `GET /api/weather/history` | Weather history |
| `GET /api/crime/stats` | Crime statistics |
| `GET /api/crime/recent` | Recent crime incidents |
| `GET /api/crime/police` | Police units |
| `GET /api/healthcare/stats` | Healthcare overview |
| `GET /api/healthcare/hospitals` | Hospital list |
| `GET /api/healthcare/records` | Recent medical records |
| `GET /api/education/stats` | Education statistics |
| `GET /api/education/schools` | Schools and programs |
| `GET /api/education/enrollments` | Active enrollments |
| `GET /api/education/skills/{id}` | Citizen skills |
| `GET /api/housing/stats` | Housing market stats |
| `GET /api/housing/properties` | Property listings |
| `GET /api/housing/transactions` | Recent property transactions |
| `GET /api/news/stats` | News media stats |
| `GET /api/news/articles` | Recent articles |
| `GET /api/news/outlets` | News outlets |

### Phase 6
| Endpoint | Description |
|---|---|
| `GET /api/culture/stats` | Culture & entertainment overview |
| `GET /api/culture/venues` | Venue listings |
| `GET /api/culture/festivals` | Festivals and events |
| `GET /api/environment/stats` | Environment & sustainability overview |
| `GET /api/environment/initiatives` | Green initiatives |
| `GET /api/demographics/stats` | Population overview |
| `GET /api/demographics/events` | Recent life events |
| `GET /api/demographics/snapshots` | Population snapshots over time |
| `GET /api/infrastructure/stats` | Infrastructure & utilities overview |
| `GET /api/infrastructure/grids` | Utility grid status |
| `GET /api/infrastructure/projects` | Infrastructure projects |
| `GET /api/tourism/stats` | Tourism overview |
| `GET /api/tourism/hotels` | Hotel listings |
| `GET /api/tourism/attractions` | Tourist attractions |
| `GET /api/tourism/visitors` | Active tourist visitors |

### Phase 7 — Multi-Tenant SaaS Platform
| Endpoint | Description |
|---|---|
| `POST /api/auth/signup` | Self-service org creation — lands on the Free Trial plan, auto-login |
| `POST /api/auth/login` | Session login (httpOnly cookie for browsers, JWT in body for mobile) |
| `POST /api/auth/logout` | Clear session |
| `GET /api/auth/me` | Current user + role |
| `GET /api/admin/organizations` | List/manage organizations (super_admin) |
| `GET /api/admin/plans` | Plan catalog |
| `POST /api/admin/organizations/{id}/subscribe` | Self-service plan upgrade (org_admin) |
| `PUT /api/admin/organizations/{id}/plan` | Override an org's plan (super_admin) |
| `GET /api/admin/organizations/{id}/billing` | Credits balance + transaction ledger |
| `POST /api/admin/organizations/{id}/credits` | Grant credits (super_admin) |
| `GET /api/twin-platform/environments` | List Twin Platform environments (city, hospital ward, airport terminal, factory line, university campus, shopping mall) |
| `POST /api/twin-platform/environments/{key}/run` | Run a simulation in a marketplace environment |
| `POST /api/eval/upload-model` | Upload a `.onnx` model for the Agent Sandbox (ONNX-only — no pickle/joblib, for RCE safety) |
| `POST /api/eval/run-test` | Run an evaluation (mock benchmark, uploaded model, REST webhook, or OpenAI-chat protocol) against synthetic citizens |
| `GET /api/eval/schema-presets` / `GET /api/eval/cohort-distributions` | Available evaluation domains and population cohorts |
| `GET /api/ai-advisor/scorecard` | Real-time health/economy/safety/carbon scorecard for the mobile AI Advisor screen |
| `GET /api/demographics/live-stats` | Live population aggregate (age, income, health) for the Population Explorer |
| `POST /api/disasters/{id}/resolve` | Resolve an active disaster |
| `GET /api/infrastructure/config` | Placeable infrastructure catalog for the Urban Planner (cost, service radius, capacity) |
| `POST /api/infrastructure/trigger` | Commit an Urban Planner placement into the simulation |
| `GET /metrics` | Prometheus metrics |

## Architecture

```
FastAPI Backend (v6.0)
    ├── Simulation Engine (tick-based world clock)
    ├── Citizen Agents (LangGraph state machines)
    │   ├── Perceive → Decide → Act → Reflect
    │   ├── LLM-powered decisions with rule-based fallback (Phase 4)
    │   ├── Personality-driven decisions (Big 5 traits)
    │   └── Memory Engine (episodic, semantic, emotional + vector search)
    ├── Communication Engine (Phase 2)
    │   ├── LLM-generated natural conversations (Phase 4)
    │   ├── Face-to-face / phone / text conversations
    │   ├── Gossip propagation
    │   ├── Social media posts
    │   └── Emergency alerts
    ├── Traffic Engine (Phase 2)
    │   ├── Road network graph with Dijkstra routing
    │   ├── Dynamic congestion & rush hours
    │   └── Multi-modal transport (walk/car/bus/metro/bike)
    ├── Government AI (Phase 2)
    │   ├── 6 autonomous departments
    │   ├── Policy enactment & budget allocation
    │   └── Emergency response coordination
    ├── Disaster Engine (Phase 3)
    │   ├── 7 disaster types with physics-inspired intensity curves
    │   ├── Building damage, casualties, evacuations
    │   └── Aftershock mechanics, spread simulation
    ├── Pandemic Engine (Phase 3)
    │   ├── SEIR epidemiological model
    │   ├── Hospital capacity, lockdowns, vaccination
    │   └── Mortality and recovery tracking
    ├── Election System (Phase 3)
    │   ├── Candidates, campaigns, debates
    │   ├── Personality-driven voter modeling
    │   └── Multi-phase election lifecycle
    ├── Social Media Engine (Phase 3)
    │   ├── Trending topics with virality
    │   ├── Misinformation generation
    │   └── Opinion influence via personality susceptibility
    ├── AI City Advisor (Phase 4)
    │   ├── LLM-powered city analysis & recommendations
    │   ├── What-if scenario analysis
    │   └── Natural language city reports
    ├── Weather & Environment Engine (Phase 5)
    │   ├── 8 weather conditions with season cycling
    │   └── Effects on happiness, health, traffic, crime
    ├── Crime & Public Safety (Phase 5)
    │   ├── 7 crime types, district-based probability
    │   └── Police units, investigation, resolution
    ├── Healthcare System (Phase 5)
    │   ├── Hospitals, clinics, psychiatric facilities
    │   └── Medical conditions, treatment, occupancy
    ├── Education System (Phase 5)
    │   ├── Schools, universities, vocational training
    │   └── Skill trees, graduation, career advancement
    ├── Housing & Real Estate (Phase 5)
    │   ├── Property market with 6 types
    │   └── Rent, evictions, value fluctuation
    ├── News & Media Engine (Phase 5)
    │   ├── 6 AI news outlets with bias/credibility
    │   └── LLM-enhanced article generation
    ├── Culture & Entertainment (Phase 6)
    │   ├── Venues (theaters, stadiums, museums, parks, clubs)
    │   └── City festivals with attendee-driven happiness boosts
    ├── Environment & Sustainability (Phase 6)
    │   ├── Air/water quality, noise, emissions, waste tracking
    │   └── Green initiatives (solar, wind, recycling, tree planting)
    ├── Demographics & Population (Phase 6)
    │   ├── Births, deaths, immigration, emigration
    │   └── Marriages, promotions, retirements, population snapshots
    ├── Infrastructure & Utilities (Phase 6)
    │   ├── Power, water, internet, gas grids with reliability/health
    │   └── Infrastructure projects (repairs, upgrades, installs)
    ├── Tourism (Phase 6)
    │   ├── Hotels, attractions, tourist arrivals and spending
    │   └── Satisfaction-driven visitor lifecycle
    ├── LLM Service (Phase 4) — OpenAI / Anthropic / Ollama
    ├── Vector Memory Store (Phase 4) — Qdrant semantic search
    ├── Graph Service (Phase 4) — Neo4j community detection, influence paths
    ├── Economy Engine (salary, taxes, businesses)
    ├── Event Engine (disasters, health, social)
    ├── Analytics (real-time metrics + historical time-series)
    ├── Multi-Tenant Auth (Phase 7)
    │   ├── JWT bearer/httpOnly-cookie dual auth
    │   ├── RBAC: super_admin / org_admin / org_member
    │   ├── Per-org entitlements (allowed_environments, allowed_modules)
    │   └── Self-service signup on the Free Trial plan
    ├── Billing & Credits (Phase 7)
    │   ├── Simulated credits ledger (grant/consume/adjust) — no real payment gateway
    │   ├── 5-tier plan catalog (Trial → Researcher → Startup → Enterprise → Government)
    │   └── Plan-linked entitlements applied on subscribe/signup
    ├── Twin Platform (Phase 7)
    │   ├── Environment marketplace (hospital ward, airport terminal, factory line,
    │   │   university campus, shopping mall, plus the flagship city)
    │   └── Per-run credit metering and quota enforcement
    ├── Agent Evaluation Sandbox (Phase 7)
    │   ├── Upload a real ONNX model, or point at a REST webhook / OpenAI-chat endpoint
    │   ├── Runs against correlated synthetic citizen cohorts
    │   └── Robustness, fairness, adversarial-failure, and adoption-rate scoring
    └── Urban Planner (Phase 7)
        ├── Place Hospital / School / Housing Colony / Fire Station / Police Station
        ├── Draw Road / Bridge segments between two points
        ├── Live AI-scored impact analysis before committing
        └── Commits become real InfraProjects that complete over simulation ticks

Databases
    ├── PostgreSQL (all persistent data)
    ├── Redis (cache, pub/sub)
    ├── Neo4j (relationship graphs, community detection, influence paths)
    └── Qdrant (vector memory search, semantic retrieval)
```

## Project Structure

```
ai_twin_city/
├── backend/
│   ├── alembic.ini           # Migration config — run as `python -m alembic -c backend/alembic.ini upgrade head`
│   └── app/
│       ├── agents/           # LangGraph citizen agents + LLM decisions
│       ├── agent_eval/       # Agent Evaluation Sandbox — ONNX model store, universal client
│       ├── analytics/        # Metrics computation & history
│       ├── api/              # Phase 3-7 standalone route files (incl. auth, admin, agent_eval, twin_platform)
│       ├── api/routes/       # Phase 1-2 route files
│       ├── auth/             # JWT security, RBAC dependencies, feature-module gating
│       ├── communication/    # Conversations, gossip, LLM dialogue
│       ├── core/             # Config, database, logging, plan catalog, rate limiting
│       ├── disasters/        # Disaster simulation engine
│       ├── economy/          # Economy engine
│       ├── elections/        # Election system
│       ├── engine/           # Simulation engine, world clock, city generator
│       ├── events/           # Event engine
│       ├── government/       # Government AI departments
│       ├── memory/           # Memory engine + vector store
│       ├── migrations/       # Alembic migration history
│       ├── models/           # SQLAlchemy models
│       ├── pandemic/         # Pandemic SEIR engine
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # LLM service, graph service, city advisor, billing
│       ├── social_media/     # Advanced social media engine
│       ├── static/           # admin.html (admin portal), dashboard.html, city3d.html (3D Urban Planner)
│       ├── traffic/          # Traffic & transportation engine
│       ├── twin_platform/    # Environment marketplace registry
│       ├── weather/          # Dynamic weather engine
│       ├── crime/            # Crime & public safety engine
│       ├── healthcare/       # Healthcare & wellness engine
│       ├── education/        # Education & skills engine
│       ├── housing/          # Housing & real estate engine
│       ├── news/             # News & media engine
│       ├── culture/          # Culture & entertainment engine
│       ├── environment/      # Environment & sustainability engine
│       ├── demographics/     # Demographics & population engine
│       ├── infrastructure/   # Infrastructure & utilities engine + Urban Planner project completion
│       └── tourism/          # Tourism engine
├── frontend/
│   └── dashboard.py          # Streamlit operational dashboard — auth-gated, plan-scoped tabs, light/dark theme
├── mobile_app/                # React Native / Expo client (see Mobile App section below)
├── deployment/docker/
├── scripts/
├── tests/
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

## Phase 1 Features

- 100-10,000 autonomous citizens with personality traits
- LangGraph-based agent decision cycle (Perceive → Decide → Act → Reflect)
- Memory engine (episodic, semantic, emotional)
- 8 city districts with locations and buildings
- Economy: businesses, employment, salaries, taxes, spending
- Event engine: disasters, pandemics, economic shifts, festivals
- Real-time analytics dashboard
- REST API + WebSocket for live updates

## Phase 2 Features

- **Multi-agent conversations**: Citizens talk face-to-face, by phone, text; gossip propagates through social networks
- **Social media simulation**: Citizens post, get likes/shares, express mood
- **Dynamic traffic**: Road network graph, Dijkstra pathfinding, rush hour congestion, multi-modal transport
- **Government AI**: 6 autonomous departments make policy decisions based on city metrics
- **Relationship graph**: Friendships, family, colleagues, rivals with evolving trust and closeness
- **Enhanced citizen agent**: Personality-driven decisions using Big 5 traits, 20+ possible actions
- **Historical analytics**: Time-series metrics tracking with trend charts

## Phase 3 Features

- **Natural disasters**: 7 disaster types (earthquake, flood, cyclone, fire, tornado, tsunami, landslide) with physics-inspired intensity curves, building damage, evacuations, aftershocks
- **Pandemic simulation**: Full SEIR epidemiological model with infection spreading, hospital capacity limits, lockdowns, mask mandates, vaccination campaigns, mortality tracking
- **Election system**: Multi-phase elections with candidate generation, personality-driven campaigns, debates, voter opinion modeling, turnout and results
- **Advanced social media**: Trending topics with virality mechanics, misinformation generation, opinion influence via political topics, personality-driven susceptibility

## Phase 4 Features

- **LLM-powered citizen decisions**: Citizens use OpenAI/Anthropic/Ollama to make natural language decisions based on personality, memories, and context (with rule-based fallback)
- **LLM conversation generator**: Natural dialogue shaped by personality, relationship history, and emotional state
- **AI City Advisor**: LLM-powered city analysis, policy recommendations, what-if scenario analysis, natural language city reports
- **Vector memory (Qdrant)**: Semantic memory search — citizens retrieve contextually relevant memories using vector similarity
- **Neo4j graph integration**: Community detection, influence path analysis, shortest social distance, top influencer ranking, inter-district connection mapping
- **Multi-provider LLM service**: Unified abstraction over OpenAI, Anthropic, and Ollama with caching and graceful fallback

## Phase 5 Features

- **Dynamic weather system**: Season cycles, 8 weather conditions (clear, cloudy, rain, storm, snow, fog, heatwave, cold snap) with effects on citizen happiness, health, traffic speed, and crime rates
- **Crime & public safety**: 7 crime types with district-based probability, police units, investigation and resolution, economic damage tracking
- **Healthcare & wellness**: Hospitals (general, emergency, psychiatric, clinic), medical conditions (physical, mental, chronic), treatment cycles, bed occupancy, weather-triggered illnesses
- **Education & skills**: Schools (high school, university, vocational, online), enrollment, progress tracking, skill trees, graduation with career advancement and education level upgrades
- **Housing & real estate**: Property market with 6 property types, rent collection, evictions, tenant matching, property value fluctuation based on district and demand, homelessness tracking
- **News & media**: 6 AI news outlets with political bias, credibility, and sensationalism traits; auto-generated articles covering city events; LLM-enhanced reporting; opinion influence on citizens

## Phase 6 Features

- **Culture & entertainment**: Venues (theaters, stadiums, museums, galleries, parks, clubs, restaurants, bars) generate visitor revenue; city festivals boost happiness for a share of the population over their duration
- **Environment & sustainability**: City-wide air quality, water quality, noise, green coverage, carbon emissions, recycling rate, and renewable energy tracking; green initiatives (solar, wind, recycling, tree planting, EV charging, water treatment) that complete over time and improve metrics
- **Demographics & population**: Births, deaths (age and health-driven), immigration, emigration (unhappy/poor citizens), marriages, promotions, and retirements as life events; periodic population snapshots with average age, dependency ratio, and growth rate
- **Infrastructure & utilities**: Power, water, internet, and gas grids per district with capacity, load, reliability, and health; grids can suffer outages and receive maintenance; infrastructure projects (road repair, grid upgrades, pipe replacement, fiber install, bridge builds) improve reliability and capacity on completion
- **Tourism**: Hotels and attractions across districts; tourists arrive based on city happiness and weather, spend money, visit attractions, and depart after their stay, contributing to hotel and attraction revenue
- **26-tab dashboard**: All Phase 1-5 tabs plus Culture, Environment, Demographics, Infrastructure, and Tourism

## Phase 7 Features (Current) — Multi-Tenant SaaS Platform

Everything above is the simulation itself. Phase 7 wraps it in a real multi-tenant
product layer: accounts, plans, billing, a 3D operator console, and a mobile client —
so the simulation can be sold and operated as a platform, not just run standalone.

### Business Model — Plans, Billing & Entitlements

- **Self-service signup**: anyone can create an organization from the admin portal or
  the Streamlit dashboard — no invite needed. Every new org starts on the **Free
  Trial** plan (capped at 3 simulation runs) and can upgrade from inside the app.
- **5-tier plan catalog** (`backend/app/core/plans.py`), each with its own credit
  grant, agent quota, model tier, and — critically — its own **entitlements**:

  | Plan | Price (₹/mo) | Credits | Agent Quota | Environments | Feature Modules |
  |---|---|---|---|---|---|
  | Free Trial | 0 | 100 | 200 | Shopping Mall only | Agent Sandbox + Twin Platform only |
  | Researcher | 999 | 2,000 | 1,000 | +Hospital Ward, University | +Traffic, Weather, Healthcare, Education, Crime, AI Advisor |
  | Startup | 4,999 | 15,000 | 10,000 | +Airport, Factory Line | Everything except Government/Elections |
  | Enterprise | 25,000 | 100,000 | 100,000 | Unrestricted (incl. flagship city) | Unrestricted (every tab) |
  | Government | Custom | 500,000 | 500,000 | Unrestricted | Unrestricted, incl. Government/Elections |

- **Simulated credits ledger**: a real, auditable `CreditTransaction` ledger
  (grant / consumption / adjustment) tracks every org's balance — deliberately not
  wired to a real payment gateway, so it's safe to demo and test without moving
  actual money.
- **Entitlement enforcement is structural, not cosmetic**: an org's
  `allowed_environments` / `allowed_modules` are checked server-side on every
  request (`require_feature` dependency, wired at router-include time) — a
  restricted plan gets a real 403, and the dashboard/mobile UI independently hides
  tabs the org isn't entitled to, so the two stay in sync without either one being
  the sole gatekeeper.
- **Role-based control, independent of plan**: `super_admin` (platform operator, no
  organization) always has unrestricted access and is the only role that can control
  the shared simulation (start/stop/step, trigger disasters). `org_admin` and
  `org_member` get read/operate access scoped to their own organization's plan.

### 3D City View & Urban Planner (`/city3d`)

A full Three.js-rendered PBR city — not a schematic map — built from the same live
simulation data the API serves everywhere else (every citizen, building, and
district position is real, not decorative).

- **Architectural typology**: buildings render distinctly by type — Commercial
  Tower, Retail/Plaza, Residential Complex, Public Civic/Government, Hospital/
  Emergency (glass tower + red accent band + helipad), and Park/Urban Garden —
  driven directly by each building's real `building_type` from `/api/city/buildings`.
- **Urban Planner / Infrastructure Sandbox**: place new Hospitals, Schools, Housing
  Colonies, Fire Stations, and Police Stations, or draw new Road/Bridge links between
  two points — each with a live, AI-scored impact analysis (catchment population,
  businesses served, projected metric deltas) before you commit. A confirmed
  placement isn't cosmetic: it calls the same `/api/infrastructure/trigger` the
  autonomous Government AI uses, creating a real `InfraProject` that completes over
  simulation ticks into an actual Hospital/School/PoliceUnit/FireStation/Location row.
- **Compare Locations mode**: stage up to 3 candidate sites side-by-side before
  committing to any of them.
- **Disaster control**: trigger any of the 7 disaster types at a clicked point with
  adjustable severity; a live-updating, scrollable detail panel shows phase,
  intensity, casualties, evacuation zones, and exactly which hospitals/police/fire
  units are responding and with how many staff — sourced from the same disaster
  engine the REST API exposes.
- **Walk Mode, Heatmap, and District boundaries**: first-person street-level
  navigation, a data-driven population/activity heatmap overlay, and glowing
  per-district boundary rings with a minimap for fast navigation across a large city.
- **Utility Maintenance**: Grid Modernization and Fiber Optic Network upgrade
  actions feed the same infrastructure reliability model as the REST API.

### Dashboard & Admin Portal

- **Streamlit operational dashboard** (`frontend/dashboard.py`, `:8501`): real
  login (JWT bearer, no bypass), self-service signup, and every tab gated by the
  logged-in org's actual plan entitlements — an org on Trial simply doesn't see
  tabs it isn't paying for, instead of seeing them disabled. Shows live Organization
  Usage (plan, agent quota, credits balance, agent-ticks consumed, simulations run).
  Simulation start/stop/step and event triggers are `super_admin`-only; org accounts
  get read-only visibility into their own organization's data. Includes a light/dark
  theme toggle that doesn't touch any existing dashboard logic.
- **Admin portal** (`backend/app/static/admin.html`, `/admin`): the shared surface
  for both super-admin platform operations (organization management, plan overrides,
  credit grants, the full transaction ledger) and org-level self-service (plan cards
  with Subscribe buttons, billing summary) — same page, different controls per role.
- **Agent Evaluation Sandbox** (in both the dashboard and mobile app): test a
  candidate AI model against correlated synthetic citizen cohorts across domain
  presets (cardiology, credit lending, real estate, e-commerce). Supports a mock
  benchmark, a REST webhook, an OpenAI-chat endpoint, or **uploading a real `.onnx`
  file** — ONNX-only, deliberately not pickle/joblib, since self-signup means
  untrusted users can upload files and arbitrary deserialization is a real RCE risk.
  Returns robustness, fairness, adversarial-failure-rate, and adoption-rate scoring
  plus demographic fairness breakdowns and an executive summary.

### Mobile App (`mobile_app/` — React Native + Expo)

A full Expo Router app (`expo ~54`, `react-native 0.81`) targeting iOS, Android, and
web from one codebase, backed by the same REST/WebSocket API as everything else —
nothing in it is mocked-and-disconnected by design; where it still is, that's tracked
as a known gap, not a feature.

- **Auth**: real Sign In / Sign Up (self-service org creation), JWT bearer token
  persisted via AsyncStorage, one-tap logout, entitlement-filtered bottom
  navigation (a restricted org's tab bar only shows what its plan includes).
- **Command Center**: live system overview — active digital twins, agent/environment/
  experiment counts, virtual time and simulation speed control.
- **Digital Twin Catalog & Marketplace**: browse and launch the Twin Platform's
  environments (Smart City Metropolitan, Metropolitan Hospital, International
  Airport Hub, Mega Automotive Factory, Central University Campus, Solar-Wind
  Microgrid), filtered to what the org's plan actually allows.
- **Agent Sandbox**: the same real evaluation flow as the dashboard's — protocol
  picker, `.onnx` upload via `expo-document-picker`, domain/sample-size controls,
  and a live results scorecard, run against the real backend.
- **AI Advisor**: a real diagnostic scorecard (health/economy/safety/carbon index,
  all derived from live city metrics — not hardcoded) plus an interactive
  scenario-question chat backed by the LLM-powered City Advisor.
- **Population Explorer**: live aggregate stats (average age, median income, average
  health) computed directly from the citizen table, with a searchable, filterable
  citizen roster.
- **Disaster & Pandemic Operations**: trigger and resolve real disasters against the
  live backend, with the same evacuation-zone and response data the 3D view shows.
- **Billing**: real plan cards fetched from the plan catalog, self-service subscribe
  with a double-submit guard, and live credits/usage from the org's actual billing
  summary.
- **Command & governance screens**: Live Map, Alerts, Elections, Government/Policy
  Mode, Infrastructure, Social Feed, Reasoning Inspector (agent decision explainer),
  Experiment Watch/Comparison, Report Generator, and Collaboration/Team Workspace.

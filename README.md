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
# Dashboard at http://localhost:8501
# API docs at http://localhost:8000/docs
```

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
    └── Analytics (real-time metrics + historical time-series)

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
│   └── app/
│       ├── agents/          # LangGraph citizen agents + LLM decisions
│       ├── analytics/       # Metrics computation & history
│       ├── api/             # Phase 3-4 standalone route files
│       ├── api/routes/      # Phase 1-2 route files
│       ├── communication/   # Conversations, gossip, LLM dialogue
│       ├── core/            # Config, database, logging
│       ├── disasters/       # Disaster simulation engine
│       ├── economy/         # Economy engine
│       ├── elections/       # Election system
│       ├── engine/          # Simulation engine, world clock, city generator
│       ├── events/          # Event engine
│       ├── government/      # Government AI departments
│       ├── memory/          # Memory engine + vector store
│       ├── models/          # SQLAlchemy models (20 model files)
│       ├── pandemic/        # Pandemic SEIR engine
│       ├── schemas/         # Pydantic schemas
│       ├── services/        # LLM service, graph service, city advisor
│       ├── social_media/    # Advanced social media engine
│       ├── traffic/         # Traffic & transportation engine
│       ├── weather/         # Dynamic weather engine
│       ├── crime/           # Crime & public safety engine
│       ├── healthcare/      # Healthcare & wellness engine
│       ├── education/       # Education & skills engine
│       ├── housing/         # Housing & real estate engine
│       ├── news/            # News & media engine
│       ├── culture/         # Culture & entertainment engine
│       ├── environment/     # Environment & sustainability engine
│       ├── demographics/    # Demographics & population engine
│       ├── infrastructure/  # Infrastructure & utilities engine
│       └── tourism/         # Tourism engine
├── frontend/
│   └── dashboard.py         # Streamlit dashboard (26 tabs)
├── deployment/docker/
├── scripts/
├── tests/
├── docker-compose.yml
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

## Phase 6 Features (Current)

- **Culture & entertainment**: Venues (theaters, stadiums, museums, galleries, parks, clubs, restaurants, bars) generate visitor revenue; city festivals boost happiness for a share of the population over their duration
- **Environment & sustainability**: City-wide air quality, water quality, noise, green coverage, carbon emissions, recycling rate, and renewable energy tracking; green initiatives (solar, wind, recycling, tree planting, EV charging, water treatment) that complete over time and improve metrics
- **Demographics & population**: Births, deaths (age and health-driven), immigration, emigration (unhappy/poor citizens), marriages, promotions, and retirements as life events; periodic population snapshots with average age, dependency ratio, and growth rate
- **Infrastructure & utilities**: Power, water, internet, and gas grids per district with capacity, load, reliability, and health; grids can suffer outages and receive maintenance; infrastructure projects (road repair, grid upgrades, pipe replacement, fiber install, bridge builds) improve reliability and capacity on completion
- **Tourism**: Hotels and attractions across districts; tourists arrive based on city happiness and weather, spend money, visit attractions, and depart after their stay, contributing to hotel and attraction revenue
- **26-tab dashboard**: All Phase 1-5 tabs plus Culture, Environment, Demographics, Infrastructure, and Tourism

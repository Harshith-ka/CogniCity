# AI Digital Twin City — Documentation

A multi-agent autonomous smart city simulation. Hundreds of AI-driven citizens live, work,
socialize, get sick, vote, and react to disasters inside a simulated city whose government
also acts autonomously — all visible through a live dashboard and a 3D city view.

---

## 1. Running the project

### Prerequisites
- Docker Desktop (must be running before any `docker compose` command)

### Start everything

```bash
cd ai_twin_city
docker compose up -d --build
```

This starts five containers:

| Service     | Port(s)       | Purpose                                  |
|-------------|---------------|-------------------------------------------|
| `postgres`  | 5432          | Primary data store (citizens, events, etc.) |
| `redis`     | 6379          | Caching / pub-sub                         |
| `neo4j`     | 7474, 7687    | Relationship graph (who knows whom)       |
| `qdrant`    | 6333, 6334    | Vector memory store for citizen agents    |
| `backend`   | 8000          | FastAPI simulation engine + REST API      |
| `dashboard` | 8501          | Streamlit control-room UI                 |

### Access points

- **Dashboard (main UI)**: http://localhost:8501
- **3D City View**: http://localhost:8000/city3d
- **Raw API / OpenAPI docs**: http://localhost:8000/docs

### Common commands

```bash
# View backend logs (tick timing, errors, event triggers)
docker compose logs backend -f

# Restart just the backend after a Python code change
docker compose up -d --build backend

# Stop everything (data is preserved in Docker volumes)
docker compose down

# Stop and wipe all data (fresh city)
docker compose down -v
```

> **Note:** most backend files and the whole `frontend/` folder are live-mounted
> (`.:/app` in `docker-compose.yml`), so editing a `.py` file and reloading the
> browser is often enough. A `--build` is only required when dependencies change.
> `backend/app/static/city3d.html` is a single static file served directly —
> editing it and reloading the page (hard refresh / cache-busting query string)
> picks it up instantly, no rebuild needed.

### Starting/stopping the simulation itself

The containers running is not the same as the simulation *ticking*. Use the
dashboard's Play/Pause controls, or the API directly:

```bash
curl -X POST http://localhost:8000/api/simulation/control \
  -H "Content-Type: application/json" -d '{"action":"start"}'

curl -X POST http://localhost:8000/api/simulation/control \
  -H "Content-Type: application/json" -d '{"action":"pause"}'

curl http://localhost:8000/api/simulation/status
```

---

## 2. Core terminology

| Term | Meaning |
|---|---|
| **Tick** | One simulation step. Each tick, every citizen agent perceives → decides → acts → reflects, and every city engine (weather, traffic, economy, disasters, etc.) advances. |
| **Sim time** | The city's internal clock, independent of real time. `time_scale` controls how many sim-minutes pass per tick. |
| **Citizen** | An autonomous agent with a personality, goals, needs (hunger, energy, social, stress, health, happiness), a home, a workplace, and a memory of past events and relationships. |
| **Citizen Agent loop** | The LangGraph state machine each citizen runs every tick: **perceive** (read surroundings/needs) → **decide** (LLM or rule-based fallback) → **act** (move, work, socialize, shop) → **reflect** (update memory). |
| **District** | A named zone of the city (e.g. "Westside") containing locations, businesses, and civic buildings. |
| **Location / Building** | A physical place a citizen can be — home, workplace, shop, hospital, school, park, etc. |
| **Event** | A discrete happening (festival, protest, power outage, etc.) that can be city-wide or targeted at a specific `(x, y)` coordinate with a `radius`, affecting only nearby citizens. |
| **Disaster** | A more severe, evolving event (earthquake, flood, fire) with phases: **ONSET → PEAK → DECLINING → RECOVERY → RESOLVED**. Disasters can spawn aftershocks (capped at 8 concurrent disasters to prevent runaway chains). |
| **Pandemic** | A disease outbreak modeled with an R0 (reproduction number), spreading citizen-to-citizen based on proximity and contact. |
| **Government AI** | An autonomous agent representing city hall. Runs departments (Health, Infrastructure, Economic, Social, Political) that each have a budget and can independently propose and fund policies. |
| **Emergency response** | When any event, disaster, or pandemic is triggered, the Government AI immediately (same tick, not on a daily cycle) issues a coordinated response — a mayor-level action plus a category-specific department action — scaled by the incident's severity, and applies immediate relief effects to nearby citizens. |
| **Trending topic** | A hashtag-like subject that gains "mentions" over time as citizens post/talk about it; conversations and social posts have a chance to reference whatever is currently trending, so the city's social chatter reacts to what's actually happening. |
| **Conversation** | A generated dialogue between two or more citizens (`face_to_face` or online). Comments are separate reply objects attached to social media posts, distinct from conversations. |
| **Social media post / comment** | Citizens post opinions and other citizens reply with comments carrying their own sentiment — a second layer on top of raw conversations. |
| **Relationship graph** | Stored in Neo4j — tracks who knows whom, friendship/rivalry strength, and family ties, and grows as citizens interact. |
| **Grow-in-place** | The population-growth mechanism: adds new citizens, homes, and jobs on top of the existing city without resetting or touching current citizens' history/relationships. |

---

## 3. Feature set

### Simulation core
- Hundreds (currently ~1000) of autonomous citizens, each an independent LangGraph agent.
- Tick-based world clock with configurable time scale.
- LLM-powered decisions when an LLM provider (OpenAI/Anthropic/Ollama) is configured; deterministic rule-based fallback otherwise, so the sim always runs even offline.
- Per-tick phase timing instrumentation logged for performance visibility.

### City systems
- **Economy**: jobs, salaries, business revenue, GDP, unemployment.
- **Traffic**: commute trips, congestion, vehicle counts by mode.
- **Weather**: daily conditions affecting health/mood (heatwaves, storms, etc.).
- **Healthcare**: illnesses, hospital capacity/beds, treatment outcomes.
- **Crime & public safety**.
- **Education**: schools, skill growth.
- **Housing market**: property values, rent.
- **News media**: auto-generated news stories about city happenings.
- **Culture & entertainment**, **environment/sustainability**, **demographics** (births/deaths/aging), **tourism**.
- **Infrastructure & utilities**: power/water/etc. grids, and infrastructure *projects* (e.g. a new bridge) that progress over time and, on completion, physically appear in the 3D view.

### Events, disasters, pandemics
- Triggerable from the dashboard or API, either **city-wide** or targeted at a specific location + radius — only citizens within range are affected, scaled by distance.
- Government AI reacts **immediately** in the same tick an incident is triggered, not on a fixed daily schedule.

### Social layer
- Multi-citizen conversations, generated with awareness of current trending topics.
- Social media posts and threaded comments, both sentiment-scored.
- Elections and opinion shifts tied to citizens' political stance.

### Government AI
- Five departments (Mayor's office plus Health/Infrastructure/Economic/Social/Political), each with its own budget.
- Autonomous policy proposals and emergency response actions.

### Dashboard (Streamlit, port 8501)
- Live stat overview, radar charts per citizen, historical trends.
- Animated 2D city map (SVG) showing citizen movement and live interaction lines between people currently talking.
- Live action feed of what's happening city-wide.
- Sidebar controls to trigger events/disasters/pandemics at a chosen district or exact coordinates.
- Link out to the 3D city view.

### 3D City View (Three.js, standalone page at `/city3d`)
- Realistic-styled, textured buildings (houses, offices, shops, hospitals, schools, factories, etc.) generated procedurally per building type.
- Day/night cycle synced to sim time (sun/moon position, sky color, building window glow).
- Citizens rendered as small figures near (not inside) their home/work buildings, gliding toward their live polled positions.
- Ambient vehicle traffic scaled to real traffic-API trip volume.
- Hospital/police markers placed per district.
- Glowing interaction lines connecting citizens currently in a face-to-face conversation, fading in/out over the conversation's lifetime.
- Government infrastructure projects rendered as real construction sites; completed bridges remain as permanent 3D structures, other project types clear once finished.
- Polls the backend every 2.5s (citizens/conversations) and 5s (status/weather/projects) to stay live.

---

## 4. Key API groups

All routes are served from the backend at `http://localhost:8000`, most under `/api/...`.
Full interactive reference: **http://localhost:8000/docs**.

| Prefix | Covers |
|---|---|
| `/api/simulation` | start/pause/status/tick control |
| `/api/citizens` | list/detail citizens, `/grow` for population scaling |
| `/api/events`, `/api/disasters`, `/api/pandemic` | trigger and list incidents (city-wide or targeted) |
| `/api/city`, `/api/traffic` | districts, buildings, live traffic stats |
| `/api/communication`, `/api/social-media` | conversations, posts, comments |
| `/api/government`, `/api/elections` | departments, policies, election state |
| `/api/relationships` | relationship graph queries |
| `/api/economy`, `/api/analytics` | GDP/jobs, historical analytics |
| `/api/weather`, `/api/crime`, `/api/healthcare`, `/api/education`, `/api/housing`, `/api/news`, `/api/culture`, `/api/environment`, `/api/demographics`, `/api/infrastructure`, `/api/tourism` | one router per city subsystem |
| `/api/ai-advisor` | LLM-backed scenario analysis |
| `/api/vector-memory`, `/api/graph` | citizen memory search, Neo4j relationship queries |
| `/city3d` | serves the standalone 3D view page |

### Growing the population

```bash
curl -X POST http://localhost:8000/api/citizens/grow \
  -H "Content-Type: application/json" -d '{"target_population": 1000}'
```
Adds new citizens/homes/jobs on top of the existing city and seeds relationships
among the new citizens only — existing citizens are untouched.

---

## 5. Known limitations

- Uvicorn runs with a **single worker** intentionally — the simulation engine keeps
  its tick count and state in-process, so multiple workers would each run an
  independent, un-synced simulation.
- The 3D view's `requestAnimationFrame`-driven animations (citizen movement, fades)
  only progress while the browser tab is actually visible/focused — this is normal
  browser tab-throttling behavior, not a bug.
- LLM-powered decisions require a configured provider (OpenAI/Anthropic key, or a
  reachable local Ollama instance); without one, citizens use the rule-based fallback.

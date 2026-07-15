# MusicLab — AI-Powered Music Discovery Engine

An AI-powered music discovery app that reads your Last.fm listening profile and generates personalized recommendations. Built with FastAPI + SvelteKit, integrates with Lidarr for library management, and supports multiple LLM providers.

## Design Decisions Summary

| Decision | Choice |
|---|---|
| Backend | Python (FastAPI) |
| Frontend | SvelteKit (built as static, served by FastAPI) |
| Database | SQLite via aiosqlite (raw SQL, no ORM) |
| Migrations | `schema.sql` run on startup (no Alembic) |
| LLM | Multi-provider (Claude, OpenAI, Ollama — any model) |
| Deployment | **Single container** (multi-stage Dockerfile) |
| Embeddings | Skip for v1 (design for v2 readiness) |
| Data Sync | Hybrid (auto-refresh on load + manual button) |
| Lidarr | Full bidirectional (read library + push with confirmation) |
| Chat | Session-based + SSE streaming + persistent distilled memory |
| Auth | Basic auth (modular, upgradeable to JWT/OAuth) |
| UI | Light/dark mode, function-first aesthetics |
| Structure | Monorepo (`/backend`, `/frontend`) |
| External APIs | Last.fm + Discogs + MusicBrainz |
| Discovery UX | Batch cards + explore-similar drill-down |
| Name | **MusicLab** |

---

## Proposed Changes

### Project Root Structure

```
musiclab/
├── Dockerfile                       # Multi-stage: builds frontend, serves from backend
├── docker-compose.yml               # Single service, simple deployment
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── schema.sql                   # DDL — run on startup, idempotent
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry, lifespan, static mount
│   │   ├── config.py                # Settings via pydantic-settings (.env)
│   │   ├── database.py              # aiosqlite connection pool, raw SQL helpers
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # /auth/login, /auth/logout
│   │   │   ├── dependencies.py      # get_current_user dependency
│   │   │   └── service.py           # password hashing, token creation
│   │   │
│   │   ├── lastfm/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # /lastfm/profile, /lastfm/refresh
│   │   │   ├── client.py            # Last.fm API wrapper (async httpx)
│   │   │   ├── service.py           # Profile aggregation logic
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   │
│   │   ├── discogs/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # Discogs API wrapper
│   │   │   ├── service.py           # Release/label enrichment
│   │   │   └── schemas.py
│   │   │
│   │   ├── musicbrainz/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # MusicBrainz API wrapper
│   │   │   ├── service.py           # Artist relations, aliases
│   │   │   └── schemas.py
│   │   │
│   │   ├── lidarr/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # /lidarr/library, /lidarr/add
│   │   │   ├── client.py            # Lidarr API wrapper
│   │   │   ├── service.py           # Library read + artist push logic
│   │   │   └── schemas.py
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # /llm/discover, /llm/chat, /llm/explore
│   │   │   ├── factory.py           # LLM provider factory (returns adapter)
│   │   │   ├── base.py              # Abstract LLMProvider interface
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── anthropic.py     # Claude adapter
│   │   │   │   ├── openai.py        # OpenAI adapter
│   │   │   │   └── ollama.py        # Ollama adapter
│   │   │   ├── prompts.py           # System prompts, profile templates
│   │   │   ├── memory.py            # Distilled memory extraction + storage
│   │   │   └── schemas.py
│   │   │
│   │   ├── discovery/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # /discover/batch, /discover/explore/{id}
│   │   │   ├── service.py           # Orchestrates LLM + metadata APIs
│   │   │   └── schemas.py
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── service.py           # TTL-based SQLite cache (get/set/expire)
│   │   │
│   │   └── common/
│   │       ├── __init__.py
│   │       ├── exceptions.py        # Custom exception hierarchy
│   │       ├── middleware.py         # Rate limiting, error handling
│   │       └── utils.py             # Shared helpers
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_lastfm/
│       ├── test_llm/
│       ├── test_discovery/
│       └── test_lidarr/
│
├── frontend/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.js
│   ├── tsconfig.json
│   ├── static/
│   │   └── favicon.png
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css                  # Global styles, CSS variables, theming
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts        # Fetch wrapper with auth headers
│   │   │   │   ├── lastfm.ts        # Last.fm API calls
│   │   │   │   ├── discovery.ts     # Discovery API calls
│   │   │   │   ├── lidarr.ts        # Lidarr API calls
│   │   │   │   └── chat.ts          # Chat API calls
│   │   │   ├── components/
│   │   │   │   ├── DiscoveryCard.svelte
│   │   │   │   ├── ArtistDetail.svelte
│   │   │   │   ├── TasteProfile.svelte
│   │   │   │   ├── ChatPanel.svelte
│   │   │   │   ├── ChatMessage.svelte
│   │   │   │   ├── LidarrConfirm.svelte
│   │   │   │   ├── RefreshButton.svelte
│   │   │   │   ├── ThemeToggle.svelte
│   │   │   │   └── Navbar.svelte
│   │   │   ├── stores/
│   │   │   │   ├── auth.ts          # Auth state
│   │   │   │   ├── profile.ts       # Last.fm profile store
│   │   │   │   ├── discovery.ts     # Discovery results store
│   │   │   │   └── theme.ts         # Dark/light mode
│   │   │   └── utils/
│   │   │       └── formatting.ts    # Date, number formatting helpers
│   │   └── routes/
│   │       ├── +layout.svelte       # App shell, navbar, theme
│   │       ├── +page.svelte         # Dashboard (taste profile + discover)
│   │       ├── login/
│   │       │   └── +page.svelte     # Login page
│   │       ├── discover/
│   │       │   ├── +page.svelte     # Discovery batch view
│   │       │   └── [id]/
│   │       │       └── +page.svelte # Artist detail / explore similar
│   │       ├── chat/
│   │       │   └── +page.svelte     # Chat panel (full page or sidebar)
│   │       └── settings/
│   │           └── +page.svelte     # API keys, Last.fm username, LLM provider
│   └── tests/
│       └── ...
│
└── docs/
    ├── API.md
    └── ARCHITECTURE.md
```

---

### Backend — Core Modules

#### [NEW] `backend/app/database.py` — Raw SQL Database Layer

No ORM. Direct `aiosqlite` with helper functions:

```python
import aiosqlite
from pathlib import Path

DB_PATH = "data/musiclab.db"

async def get_db() -> aiosqlite.Connection:
    """Get a database connection. Used as a FastAPI dependency."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row  # dict-like access
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    """Run schema.sql on startup. All statements are IF NOT EXISTS — idempotent."""
    schema = Path(__file__).parent.parent.parent / "schema.sql"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(schema.read_text())
```

All modules use `db: aiosqlite.Connection` as a dependency and write raw SQL. Clean, readable, zero abstraction tax.

---

#### [NEW] `backend/app/config.py` — Configuration

Pydantic-settings based configuration, loaded from `.env`:

```python
class Settings(BaseSettings):
    # App
    APP_SECRET_KEY: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./musiclab.db"

    # Last.fm
    LASTFM_API_KEY: str
    LASTFM_USERNAME: str = ""

    # Lidarr (optional)
    LIDARR_URL: str = ""
    LIDARR_API_KEY: str = ""

    # LLM (user picks provider)
    LLM_PROVIDER: str = "anthropic"  # anthropic | openai | ollama
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Discogs
    DISCOGS_TOKEN: str = ""

    # Auth
    AUTH_USERNAME: str = "admin"
    AUTH_PASSWORD_HASH: str = ""  # bcrypt hash

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = ""  # empty = user picks from installed models
```

---

#### [NEW] `backend/app/auth/` — Modular Auth Layer

**v1 implementation:**
- Basic username/password auth
- bcrypt password hashing
- Session-based tokens stored in SQLite (raw SQL via `aiosqlite`)
- `get_current_user` FastAPI dependency that gates all protected routes
- **Designed as a swappable module** — the dependency injection pattern means we can replace the auth backend (JWT, OAuth2, OIDC) without touching any route code

```python
# auth/dependencies.py
async def get_current_user(request: Request, db: aiosqlite.Connection) -> dict:
    """Dependency injected into all protected routes.
    v1: validates session token from cookie against sessions table.
    v2: swap to JWT validation without changing route signatures."""
    token = request.cookies.get("session_token")
    row = await db.execute_fetchone(
        "SELECT * FROM users u JOIN sessions s ON u.id = s.user_id "
        "WHERE s.token = ? AND s.expires_at > ?", (token, datetime.utcnow())
    )
    if not row:
        raise HTTPException(401)
    return dict(row)
```

---

#### [NEW] `backend/app/lastfm/client.py` — Last.fm API Client

Async HTTP client (httpx) wrapping these endpoints:

| Endpoint | Purpose | Cache TTL |
|---|---|---|
| `user.getTopArtists` | Core taste (all-time + recent periods) | 6 hours |
| `user.getTopAlbums` | Album-level preferences | 6 hours |
| `user.getTopTags` | Genre/tag affinity | 12 hours |
| `user.getRecentTracks` | Granular recent history | 1 hour |
| `user.getLovedTracks` | Explicit taste signals | 6 hours |
| `user.getWeeklyArtistChart` | Recent weekly trends | 6 hours |
| `artist.getSimilar` | For explore-from-card drill-down | 24 hours |
| `artist.getTopTags` | Tag data for recommended artists | 24 hours |

All responses cached in SQLite via the cache service with configurable TTLs.

---

#### [NEW] `backend/app/llm/` — Multi-Provider LLM Abstraction

```python
# llm/base.py
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str,
                       tools: list[dict] | None = None) -> LLMResponse: ...

    @abstractmethod
    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]: ...

# llm/factory.py
def get_llm_provider(provider: str) -> LLMProvider:
    match provider:
        case "anthropic": return AnthropicProvider(...)
        case "openai": return OpenAIProvider(...)
        case "ollama": return OllamaProvider(...)
```

Each provider implements the same interface. The factory selects based on config. Tool calling support is required for the memory extraction feature.

---

#### [NEW] `backend/app/llm/memory.py` — Distilled Memory System

The key innovation — after each chat session, the LLM extracts preference signals and writes them to a structured memory block.

```
Memory Block Schema (stored in SQLite as JSON):
{
    "updated_at": "2026-07-15T12:00:00Z",
    "core_preferences": [
        "Dislikes lo-fi production quality",
        "Prefers 80s-influenced darkwave over modern synthwave",
        "Has been exploring Japanese ambient recently"
    ],
    "liked_recommendations": [
        {"artist": "Molchat Doma", "context": "loved the post-punk energy"},
        {"artist": "Kikagaku Moyo", "context": "exactly the psych rock they wanted"}
    ],
    "disliked_recommendations": [
        {"artist": "100 gecs", "context": "too experimental, too noisy"}
    ],
    "noted_patterns": [
        "Tends to prefer albums over singles",
        "Gravitates toward non-English language music"
    ]
}
```

**Flow:**
1. Chat session ends (user closes chat or navigates away)
2. Backend sends the full conversation to the LLM with a memory extraction tool
3. LLM calls the `update_memory` tool with structured preference data
4. Memory block is merged with existing memory in SQLite
5. On next session, memory block is injected into the system prompt alongside Last.fm data

---

#### [NEW] `backend/app/main.py` — App Entry Point

FastAPI app with lifespan that initializes the database and mounts the built SvelteKit frontend as static files:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # runs schema.sql — idempotent
    yield

app = FastAPI(title="MusicLab", lifespan=lifespan)

# API routes
app.include_router(auth_router, prefix="/api/auth")
app.include_router(lastfm_router, prefix="/api/lastfm")
# ... etc

# Serve SvelteKit build output as static files (single container)
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")
```

All API routes are prefixed with `/api/` so they don't conflict with the SvelteKit SPA routing.

---

#### [NEW] `backend/app/llm/prompts.py` — System Prompt Engineering

The system prompt is assembled dynamically from:

1. **Base instructions** — what the LLM is (music discovery assistant), tone, output format
2. **Last.fm profile snapshot** — top artists, top tags, recent tracks, loved tracks, weekly chart
3. **Memory block** — distilled preferences from past conversations
4. **Lidarr library** — list of artists already in the user's library (to avoid duplicate recs)
5. **Discovery context** — if in explore mode, the specific artist being explored

```
System Prompt Structure:
┌─────────────────────────────────────────────┐
│ BASE: You are MusicLab, a music discovery   │
│ assistant. You analyze listening profiles    │
│ and recommend artists the user hasn't heard. │
├─────────────────────────────────────────────┤
│ PROFILE: {last.fm data — top artists,       │
│ tags, recent tracks, loved tracks}           │
├─────────────────────────────────────────────┤
│ MEMORY: {distilled preference history}       │
├─────────────────────────────────────────────┤
│ LIBRARY: {Lidarr artist list — DO NOT        │
│ recommend these}                             │
├─────────────────────────────────────────────┤
│ TASK-SPECIFIC: {discover batch / explore /   │
│ chat instructions}                           │
└─────────────────────────────────────────────┘
```

---

#### [NEW] `backend/app/discovery/service.py` — Discovery Orchestrator

The core engine that coordinates everything:

```
Discover Batch Flow:
1. Load Last.fm profile (from cache or fresh)
2. Load Lidarr library (exclude list)
3. Load memory block
4. Assemble system prompt
5. Call LLM: "Generate 8 artist recommendations with structured output"
6. LLM returns: [{artist, genre, era, why_it_matches, listener_count_hint}, ...]
7. For each artist:
   a. Fetch Last.fm stats (listeners, playcount, similar artists)
   b. Fetch MusicBrainz data (relations, aliases, country)
   c. Fetch Discogs data (labels, key releases, years active)
8. Merge all data into DiscoveryCard objects
9. Cache the batch in SQLite
10. Return to frontend

Explore Similar Flow:
1. User clicks "Explore" on a card
2. Fetch artist.getSimilar from Last.fm
3. Cross-reference with Lidarr (exclude owned)
4. Call LLM: "From these similar artists, pick 5 the user would like based on their profile"
5. Enrich with metadata
6. Return new card set
```

---

#### [NEW] `backend/app/cache/service.py` — TTL Cache

Simple key-value cache in SQLite:

```python
class CacheService:
    async def get(self, key: str) -> dict | None:
        """Returns cached value if not expired, else None."""

    async def set(self, key: str, value: dict, ttl_seconds: int = 3600):
        """Stores value with expiration timestamp."""

    async def invalidate(self, pattern: str):
        """Invalidate all keys matching pattern (for manual refresh)."""
```

Table: `cache_entries(key TEXT PK, value JSON, expires_at TIMESTAMP)`

---

### Backend — Database Schema

```sql
-- Users (v1: single user, future: multi-user)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    lastfm_username TEXT,
    llm_provider TEXT DEFAULT 'anthropic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session tokens
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL
);

-- Last.fm profile snapshots
CREATE TABLE lastfm_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    data JSON NOT NULL,  -- full aggregated profile
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery batches
CREATE TABLE discovery_batches (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    cards JSON NOT NULL,  -- array of discovery cards
    prompt_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory blocks
CREATE TABLE memory_blocks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    memory JSON NOT NULL,  -- structured preference data
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API response cache
CREATE TABLE cache_entries (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- Chat history (per-session, not persisted long-term)
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    messages JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Frontend — Key Components

#### Dashboard (`+page.svelte`)

The main view with two panels:
- **Left**: Taste Profile summary (LLM-generated analysis of your Last.fm data)
- **Right**: Quick actions — Discover, Refresh Profile, Recent discoveries

#### Discovery Cards (`DiscoveryCard.svelte`)

Each card shows:
- Artist name + genre tags
- AI blurb: *"Why this matches your profile"*
- Last.fm listener count + playcount
- "Explore Similar" button → navigates to drill-down
- "Add to Lidarr" button → opens confirmation modal

#### Artist Detail (`/discover/[id]/+page.svelte`)

Full artist view:
- All Last.fm stats
- MusicBrainz relations (members, associated acts)
- Discogs discography highlights
- Similar artists grid (explore further)
- "Add to Lidarr" with quality profile selection

#### Chat Panel (`/chat/+page.svelte`)

- Clean message thread UI
- System message at top: *"I've analyzed your listening profile. Ask me anything about music discovery."*
- Streaming responses from the LLM
- Memory indicator: shows what the system remembers about your preferences

#### Settings (`/settings/+page.svelte`)

- Last.fm username configuration
- Lidarr URL + API key
- LLM provider selector (dropdown: Claude / OpenAI / Ollama)
- LLM API key input
- Discogs token
- Theme toggle
- Account settings (change password)

---

### Dockerfile — Multi-Stage Single Container

```dockerfile
# Stage 1: Build SvelteKit frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build  # outputs to /app/frontend/build

# Stage 2: Python backend + built frontend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# Copy built SvelteKit output into FastAPI's static directory
COPY --from=frontend-build /app/frontend/build ./static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  musiclab:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # SQLite persistence
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

One container. One port. `docker-compose up` and you're running.

---

### API Endpoints (REST + SSE)

All endpoints prefixed with `/api/` to separate from SvelteKit static routing.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login, returns session cookie |
| `POST` | `/api/auth/logout` | Invalidate session |
| `GET` | `/api/lastfm/profile` | Get aggregated Last.fm profile |
| `POST` | `/api/lastfm/refresh` | Force re-fetch from Last.fm |
| `GET` | `/api/lidarr/library` | Get current Lidarr artist list |
| `POST` | `/api/lidarr/add` | Add artist to Lidarr (with confirmation data) |
| `POST` | `/api/discover/batch` | Generate discovery batch (LLM + metadata) |
| `GET` | `/api/discover/explore/{artist_id}` | Explore similar to a discovered artist |
| `GET` | `/api/discover/history` | Past discovery batches |
| `POST` | `/api/chat/message` | Send chat message, returns **SSE stream** |
| `GET` | `/api/chat/memory` | View current memory block |
| `GET` | `/api/ollama/models` | List installed Ollama models (for settings UI) |
| `GET` | `/api/settings` | Get current settings |
| `PUT` | `/api/settings` | Update settings |
| `GET` | `/api/health` | Health check |

---

## Resolved Decisions

| Question | Decision |
|---|---|
| Chat streaming | **SSE** via FastAPI `StreamingResponse` — real-time token streaming |
| Ollama models | User picks **any installed model** — `/api/ollama/models` lists what's available |
| Container model | **Single container** — multi-stage build, SvelteKit built into FastAPI static |
| ORM | **None** — raw SQL via `aiosqlite`, no SQLAlchemy |
| Migrations | **`schema.sql`** on startup, idempotent `CREATE TABLE IF NOT EXISTS` |

## Open Questions

> [!IMPORTANT]
> **Discogs rate limit:** Discogs allows 60 requests/minute for authenticated users. If a discovery batch has 8 artists and each needs a Discogs lookup, that's fine. But if the user does rapid "explore similar" chains, we could hit limits. Should we:
> - Queue Discogs enrichment asynchronously (show card without Discogs data first, fill in later)?
> - Or block until all data is fetched?

---

## Verification Plan

### Automated Tests
```bash
# Backend unit tests
cd backend && pytest tests/ -v

# Frontend tests
cd frontend && npm run test
```

### Manual Verification
- Configure with a real Last.fm username and verify profile data loads correctly
- Test each LLM provider (Claude, OpenAI, Ollama) generates valid discovery batches
- Verify Lidarr bidirectional sync (read library, add artist)
- Test the memory extraction flow: have a chat, close it, verify memory block updates
- Verify cache TTL behavior — stale data refreshes automatically
- Docker Compose: `docker-compose up --build` from clean state, verify everything works
- Test light/dark mode toggle

# MusicLab — Agent Ruleset

> Concise, actionable rules for writing consistent, safe code in this codebase.
> The full reference is `ARCHITECTURE.md` — when in doubt, defer to it.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, aiosqlite, httpx, Pydantic v2 |
| Frontend | SvelteKit, Svelte 5 (runes mode), TypeScript, Vite |
| LLM | OpenAI SDK (used for OpenAI + DeepSeek via base_url override) |
| DB | SQLite via `aiosqlite` (file: `backend/data/musiclab.db`) |
| APIs | Last.fm, Discogs, MusicBrainz, Lidarr |

---

## Project Layout

```
backend/app/
├── main.py          # FastAPI app, lifespan, router registration
├── config.py        # Pydantic Settings — singleton `settings` import
├── database.py      # get_db() async generator, init_db()
├── common/          # exceptions.py, middleware.py, http.py, utils.py
├── auth/            # router, service, dependencies
├── lastfm/          # client, service, schemas, router
├── discogs/         # client, service, schemas
├── musicbrainz/     # client, service, schemas
├── lidarr/          # client, service, schemas, router
├── llm/             # base, providers/{openai,ollama}, memory, prompts, schemas, router
├── discovery/       # service, schemas, router
├── explore/         # service, schemas, router, seed_service, genre_seed.json
├── settings/        # service, router
└── cache/           # service
```

Every module follows: `__init__.py` → `schemas.py` → `client.py` (optional) → `service.py` → `router.py`

---

## Inviolable Rules

### 1. Every `.py` file starts with
```python
"""Module-level docstring."""

from __future__ import annotations
```
No exceptions. Docstring first, then `from __future__ import annotations`.

### 2. All imports at the top of the file
No mid-file imports. No in-function imports. Standard library → third-party → local app. Blank line between groups. The ONLY exception: circular import workarounds with an explanatory comment.

### 3. Routers have NO prefix or tags
```python
# ✅ Correct
router = APIRouter()

# ❌ WRONG — double-prefix bug
router = APIRouter(prefix="/some", tags=["some"])
```
Prefixes and tags are set ONLY in `main.py`: `app.include_router(router, prefix="/api/x", tags=["x"])`.

### 4. Service layer never imports HTTP types
`service.py` raises domain exceptions from `common/exceptions.py` (NotFoundError, ExternalAPIError, etc.). It never imports `HTTPException` or FastAPI types. Only `router.py` may raise `HTTPException`.

### 5. ExternalAPIError uses keyword arguments
```python
raise ExternalAPIError(service="Discogs", message=str(e))   # ✅
raise ExternalAPIError(f"Discogs API error: {str(e)}")       # ❌ — sets service= to the message
```

### 6. Never silently swallow exceptions
```python
# ✅ Correct
except httpx.HTTPError:
    logger.exception("Failed to fetch artist info for %s", artist_name)
    return None

# ❌ WRONG
except Exception:
    return []
```
Every `except` must log. Catch specific types, not bare `Exception`. Use `logger.exception()` inside `except` blocks (captures traceback automatically).

### 7. `datetime.now(timezone.utc)` — never `datetime.utcnow()`

### 8. All endpoints (except health, login) require auth
```python
current_user: dict = Depends(get_current_user)
```

### 9. Dependency injection uses async generators with cleanup
```python
async def get_explore_service(db = Depends(get_db)) -> AsyncGenerator[ExploreService, None]:
    client = SomeClient(...)
    service = SomeService(db, client)
    try:
        yield service
    finally:
        await client.close()  # ALWAYS close HTTP clients
```

### 10. Pydantic models: use `Field(default_factory=list)`, `Literal` for constrained strings
```python
role: Literal["user", "assistant"]  # ✅
role: str  # "user" or "assistant"  # ❌
```
Never pass fields to a Pydantic model that aren't defined in its schema — Pydantic v2 rejects extra fields.

---

## Module Patterns

### API Client (`client.py`)
```python
from app.common.http import BaseHttpClient
from app.common.exceptions import ExternalAPIError

class SomeClient(BaseHttpClient):
    BASE_URL = "https://api.example.com"

    def __init__(self, api_key: str) -> None:
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = await self._http.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ExternalAPIError(service="SomeAPI", message=str(e)) from e
```

### Service (`service.py`)
- Constructor takes clients and aiosqlite connection
- Uses `self._db` for the DB connection
- Raises domain exceptions (NotFoundError, etc.) — never HTTPException
- All I/O is async
- Parallel calls use `asyncio.gather()`

### Router (`router.py`)
- Thin HTTP layer — parses params, calls service, returns response
- Sets up dependency generator function for the service
- Never contains business logic

---

## Common Pitfalls

1. **Forgetting to close HTTP clients**: Every `*Client` that inherits `BaseHttpClient` MUST be closed. If you create one in a `get_*_service` dependency, use `try/finally` with `await client.close()`.

2. **Schema/config mismatch**: If you change `config.py` defaults, check `schema.sql` for matching defaults. If you delete a provider, remove it from schema defaults and frontend select options too.

3. **`type(x) == str` instead of `isinstance(x, str)`**: `isinstance` supports subclasses.

4. **`asyncio.create_task()` without error collection**: Background tasks that fail are silently lost. Add a done callback that logs exceptions:
   ```python
   task = asyncio.create_task(self.enrich_and_cache_artist(name))
   task.add_done_callback(lambda t: logger.exception("Background enrich failed") if t.exception() else None)
   ```

5. **f-string SQL**: Parameterize all user-controlled values. Table/column names from constants should at minimum be validated against a whitelist.

6. **Memory leaks in in-memory stores**: Dict-based stores (rate limiter, caches) must evict stale entries. Without cleanup, they grow unboundedly.

7. **`| string` in TypeScript unions**: `'openai' | 'deepseek' | string` is just `string`. Drop the `| string` or use a proper union.

8. **Import `asyncio` at the top**: Not inside functions. ARCHITECTURE.md §2.6 is explicit about this.

---

## Database Schema Rules

- Schema is in `backend/schema.sql`, executed by `init_db()` on startup
- Table/column names in code must match `schema.sql` exactly
- `discovery_batches.id` is TEXT (UUID), not INTEGER AUTOINCREMENT
- `discovery_cards` has its own table with `batch_id` FK — don't store cards as JSON in batches
- `artists` table has UNIQUE on `slug` only — `discogs_id` and `mbid` are nullable and not unique
- Favorites use composite UNIQUE on `(user_id, entity_type, entity_id)`
- `ON CONFLICT(slug)` for genres, `ON CONFLICT(name, genre_id)` for styles

---

## Frontend Rules

- **Svelte 5 runes**: `$props()`, `$state()`, `$derived()`, `$effect()`
- **Props pattern**:
  ```svelte
  <script lang="ts">
      interface Props { artist: ArtistSummary; onSuccess?: () => void; }
      let { artist, onSuccess }: Props = $props();
  </script>
  ```
- **Types**: All shared types in `$lib/types.ts` — never redefine types in components or stores
- **API calls**: Always through `apiClient` (in `$lib/api.ts`) — never raw `fetch()`
- **Error handling**: `catch (err: unknown)` — never `catch (err: any)`. Display errors to user, not just `console.error`.
- **CSS**: Utility classes from `app.css` only. No hardcoded colors — use CSS variables. No Tailwind (not installed). No redefining global utilities in component `<style>` blocks.
- **`{#each}` blocks**: Always provide a key expression

---

## Testing

- **Backend**: pytest with `pytest-asyncio` (`asyncio_mode = auto`). Tests at `backend/tests/`.
- **DB fixtures**: Use `@pytest_asyncio.fixture(autouse=True)` with `init_db()` then seed test data.
- **HTTP tests**: Use `httpx.AsyncClient(app=app, base_url="http://test")`.
- **Auth in tests**: Login via `/api/auth/login` to get session cookies, pass them to subsequent requests.
- **Settings tests**: Mutate `settings` module-level singleton directly — tests should restore original values.

### Running tests
```bash
cd backend
pytest tests/ -v
```

---

## Running the App

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

---

## Files to Never Modify Without Careful Thought

- `backend/schema.sql` — schema changes need migration consideration for existing DBs
- `backend/app/config.py` — changes affect all modules
- `backend/app/main.py` — router registration order matters
- `backend/app/common/exceptions.py` — exception hierarchy affects all error handlers
- `backend/app/common/middleware.py` — rate limiting and error handlers affect all routes
- `frontend/src/lib/types.ts` — must stay in sync with backend Pydantic schemas
- `frontend/src/lib/api.ts` — single API client surface for the entire frontend
- `frontend/src/app.css` — design tokens affect all components

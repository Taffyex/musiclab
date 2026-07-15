# MusicLab — Architecture & Coding Standards

> **This is the single source of truth** for all coding conventions, architectural decisions, and security requirements in MusicLab. Every contributor (human or AI) **must** follow these rules. When in doubt, defer to this document.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Backend Conventions (Python / FastAPI)](#2-backend-conventions-python--fastapi)
3. [Frontend Conventions (SvelteKit / Svelte 5)](#3-frontend-conventions-sveltekit--svelte-5)
4. [Database & Schema](#4-database--schema)
5. [API Design](#5-api-design)
6. [Security Requirements](#6-security-requirements)
7. [Error Handling](#7-error-handling)
8. [Type System](#8-type-system)
9. [Naming Conventions](#9-naming-conventions)
10. [Imports & Module Organisation](#10-imports--module-organisation)
11. [Styling (CSS)](#11-styling-css)
12. [Testing](#12-testing)
13. [Docker & Deployment](#13-docker--deployment)
14. [Checklist for New Code](#14-checklist-for-new-code)

---

## 1. Project Structure

```
musiclab/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, lifespan, router registration
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── database.py          # aiosqlite connection helpers
│   │   ├── common/              # Shared: exceptions, middleware, utils
│   │   ├── auth/                # Authentication module
│   │   ├── lastfm/              # Last.fm integration
│   │   ├── discogs/             # Discogs integration
│   │   ├── musicbrainz/         # MusicBrainz integration
│   │   ├── lidarr/              # Lidarr integration
│   │   ├── llm/                 # LLM providers & chat
│   │   ├── discovery/           # Discovery orchestration
│   │   └── cache/               # Cache service
│   ├── tests/
│   ├── schema.sql
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app.css              # Global design tokens & utilities ONLY
│   │   ├── app.html
│   │   ├── lib/
│   │   │   ├── api.ts           # Centralised API client
│   │   │   ├── stores.ts        # Svelte stores (NO type definitions here)
│   │   │   ├── types.ts         # ALL shared TypeScript types (single source)
│   │   │   ├── utils/           # Pure helper functions
│   │   │   └── components/      # Reusable Svelte components
│   │   └── routes/              # SvelteKit file-based routing
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── ARCHITECTURE.md               # ← THIS FILE
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

### Module anatomy (backend)

Every backend module follows the same 4-file structure:

```
module_name/
├── __init__.py      # Package marker — "# MusicLab <module_name> module"
├── schemas.py       # Pydantic models for this module
├── client.py        # External API client (if applicable)
├── service.py       # Business logic (NO HTTP concerns)
└── router.py        # FastAPI router (HTTP layer only)
```

**Rules:**
- `router.py` → may raise `HTTPException`, handles request/response
- `service.py` → raises domain exceptions from `common/exceptions.py`, never imports FastAPI HTTP types
- `client.py` → wraps external HTTP calls, raises `ExternalAPIError`
- `schemas.py` → Pydantic models only, no logic

---

## 2. Backend Conventions (Python / FastAPI)

### 2.1 Every file starts with

```python
"""Module-level docstring describing purpose."""

from __future__ import annotations
```

**No exceptions.** The `from __future__ import annotations` import must be in every `.py` file for consistent Pydantic v2 behaviour and forward-reference support.

### 2.2 Router rules

```python
# ✅ Correct — no prefix or tags on the router itself
router = APIRouter()

# main.py sets the prefix and tags:
app.include_router(some_router, prefix="/api/some", tags=["some"])
```

```python
# ❌ WRONG — double-prefix bug
router = APIRouter(prefix="/some", tags=["some"])
# + main.py: app.include_router(router, prefix="/api/some")
# Result: /api/some/some/endpoint
```

**Router prefixes and tags are set only in `main.py`**, never on the router itself.

### 2.3 Dependency injection pattern

```python
# Type-annotate all Depends() parameters
async def my_endpoint(
    current_user: dict = Depends(get_current_user),
    service: SomeService = Depends(get_some_service),
    db: aiosqlite.Connection = Depends(get_db),
) -> SomeModel:
    ...
```

### 2.4 Docstring style — Google style

```python
async def generate_batch(self, user_id: int, count: int = 8) -> DiscoveryBatch:
    """Generate a batch of discovery recommendation cards.

    Args:
        user_id: Internal user ID.
        count: Number of cards to generate.

    Returns:
        A DiscoveryBatch containing enriched cards.

    Raises:
        NotFoundError: If the user does not exist.
    """
```

Every public function and method must have a Google-style docstring. Private helpers (`_prefixed`) may use a one-liner.

### 2.5 Logging

Every module must set up a logger:

```python
import logging

logger = logging.getLogger(__name__)
```

**Rules:**
- `logger.info()` for normal operations (startup, shutdown, cache hits)
- `logger.warning()` for recoverable issues (missing optional config)
- `logger.error()` for failures that return error responses
- `logger.exception()` inside `except` blocks (automatically captures traceback)
- **Never silently swallow exceptions** with bare `except: pass` or `except: return`

```python
# ✅ Correct
except Exception:
    logger.exception("Failed to parse LLM response")
    raw_recs = []

# ❌ WRONG
except Exception:
    raw_recs = []
```

### 2.6 Async patterns

- All I/O operations must be `async`.
- Use `asyncio.gather()` for parallel independent calls.
- Import `asyncio` at the **top of the file**, not inside functions.
- Async generators use `AsyncIterator[T]` return type, not `AsyncGenerator`.

### 2.7 ExternalAPIError usage

```python
# ✅ Correct — use keyword arguments
from app.common.exceptions import ExternalAPIError
raise ExternalAPIError(service="Discogs", message=str(e))

# ❌ WRONG — positional string sets service= to the whole message
raise ExternalAPIError(f"Discogs API error: {str(e)}")
```

### 2.8 Pydantic models

- All models inherit from `BaseModel`.
- Use `Field(default_factory=list)` for mutable defaults.
- **Only pass fields that exist on the model.** Pydantic v2 rejects extra fields by default.
- Use `model_validate()` when constructing from dicts, `model_dump()` when serialising.
- Use `Literal["opt1", "opt2"]` for constrained string fields (not bare `str` with a comment).

```python
# ✅ Correct
role: Literal["user", "assistant"]

# ❌ WRONG
role: str  # "user" or "assistant"
```

### 2.9 UUID generation

```python
from uuid import uuid4

# ✅ Correct
card_id = str(uuid4())

# ❌ WRONG — fragile, inconsistent format
id = str(import_uuid.uuid4()) if 'import_uuid' in locals() else __import__("uuid").uuid4().hex
```

### 2.10 Datetime handling

```python
from datetime import datetime, timezone

# ✅ Correct
now = datetime.now(timezone.utc)

# ❌ WRONG — deprecated in Python 3.12+, returns naive datetime
now = datetime.utcnow()
```

---

## 3. Frontend Conventions (SvelteKit / Svelte 5)

### 3.1 Component props — use the `interface Props` pattern

```svelte
<script lang="ts">
    interface Props {
        artist: DiscoveryCard;
        onSuccess?: () => void;
    }

    let { artist, onSuccess }: Props = $props();
</script>
```

**One pattern everywhere.** Do not use:
- ~~`$props<{ artist: DiscoveryCard }>()`~~ (generic type parameter)
- ~~`let { x }: { x: Type } = $props()`~~ (inline type)

### 3.2 Types live in `$lib/types.ts` — single source of truth

- **All** shared interfaces and types are defined in `$lib/types.ts`.
- **Never** define types in `stores.ts`, component files, or route files.
- If a component needs a local type (e.g., an internal `Message` shape), it must be defined in the component's `<script>` block and not exported.

```typescript
// ✅ stores.ts — import types, don't define them
import type { User, LastfmProfile } from '$lib/types';

// ❌ WRONG — stores.ts re-defining User with different shape
export interface User { id: number; username: string; lastfm_username: string; }
```

### 3.3 API calls — use `apiClient` exclusively

- All HTTP requests go through `$lib/api.ts` via `apiClient`.
- Never use raw `fetch()` in components or routes.
- The `fetchBase()` wrapper handles `Content-Type`, error parsing, and `credentials`.

### 3.4 Error handling in components

```typescript
// ✅ Correct — typed catch, user-friendly message
} catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'An unexpected error occurred';
    error = message;
}

// ❌ WRONG
} catch (err: any) {
    error = err.message;
}
```

- Always use `catch (err: unknown)`, never `catch (err: any)`.
- Always provide user-facing feedback (set an `error` state variable).
- Never silently `console.error()` without also informing the user.
- Use consistent variable name `err` (not `e`, `error`, `ex`).

### 3.5 Auth guard — use the shared utility

Protected pages must **not** duplicate the auth-check boilerplate. Use:

```typescript
import { ensureAuthenticated } from '$lib/utils/auth-guard';

onMount(async () => {
    await ensureAuthenticated();
    // ... page-specific init
});
```

The layout already checks auth on load — page-level guards are a fallback for direct navigation.

### 3.6 Svelte reactivity — Svelte 5 runes only

- Use `$state()`, `$props()`, `$effect()`, `$derived()`.
- **Never** use legacy `$:` reactive statements or `export let` for props.
- Use `{#each items as item (item.id)}` (keyed) for all dynamic lists.
- **Never** mutate props directly. Notify the parent via a callback prop.

```svelte
<!-- ✅ Correct — callback prop -->
onSuccess={() => { /* parent updates its own state */ }}

<!-- ❌ WRONG — direct prop mutation -->
artist.already_in_lidarr = true;
```

### 3.7 Barrel exports

`$lib/index.ts` must re-export commonly used symbols:

```typescript
export { apiClient } from './api';
export { userStore, profileStore, discoveryStore, themeStore } from './stores';
export type { User, LastfmProfile, DiscoveryCard, DiscoveryBatch } from './types';
```

---

## 4. Database & Schema

### 4.1 `schema.sql` is the canonical source

The table names, column names, and types in `schema.sql` are authoritative. Backend code **must** match exactly.

| schema.sql table    | Column              | What code must use       |
|---------------------|---------------------|--------------------------|
| `cache_entries`     | `key`, `value`, `expires_at` | `cache_entries` (not `cache`) |
| `discovery_batches` | `cards`, `created_at`        | `discovery_batches` (not `discovery_history`) |
| `memory_blocks`     | `memory`                     | `memory` (not `data`)    |
| `lastfm_profiles`   | `data`                       | `data` (not `profile_data`) |

**When adding a new table:**
1. Add it to `schema.sql` first.
2. Write the service code to match the exact table/column names.
3. Never rename tables or columns in code — change `schema.sql` instead.

### 4.2 SQL style

- Use parameterised queries exclusively (`?` placeholders). Never interpolate values.
- Table names: `snake_case`, plural (`users`, `sessions`, `cache_entries`).
- Column names: `snake_case` (`user_id`, `created_at`).

---

## 5. API Design

### 5.1 URL structure

```
/api/{module}/{action}
```

- Prefix is always `/api/`.
- Module name is singular or short: `auth`, `lastfm`, `lidarr`, `discovery`, `llm`.
- Action is a verb or noun: `login`, `profile`, `generate`, `library`.

### 5.2 HTTP methods

| Action            | Method | Example                        |
|-------------------|--------|--------------------------------|
| Read/list         | GET    | `GET /api/lidarr/library`      |
| Create/trigger    | POST   | `POST /api/discovery/generate` |
| Update            | PUT    | `PUT /api/settings`            |
| Delete            | DELETE | `DELETE /api/sessions/{id}`    |

### 5.3 Query parameter validation

Always use FastAPI's `Query()` with bounds for numeric parameters:

```python
from fastapi import Query

# ✅ Correct
count: int = Query(default=8, ge=1, le=50)

# ❌ WRONG — unbounded, user can pass count=999999
count: int = 8
```

### 5.4 Authentication

Every endpoint except `/api/health` and `/api/auth/login` **must** include:

```python
current_user: dict = Depends(get_current_user)
```

No exceptions. Do not wrap auth imports in `try/except`.

---

## 6. Security Requirements

### 6.1 Session cookies

```python
from app.config import settings

response.set_cookie(
    key="session",
    value=token,
    httponly=True,
    secure=settings.environment == "production",
    samesite="lax",
    max_age=7 * 24 * 60 * 60,
)
```

- `httponly=True` — always.
- `secure` — environment-aware: `True` in production, `False` in development.
- `samesite="lax"` — always.

### 6.2 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

CORS_ORIGINS = {
    "development": ["http://localhost:5173"],
    "production": ["https://musiclab.teoreze.com"],
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.get(settings.environment, []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.3 External API URLs

- **Always HTTPS** for external API calls. No `http://` in production code.
- API keys in query strings are acceptable only when the external API requires it (e.g., Last.fm), but the base URL must be HTTPS.

### 6.4 Secrets

- `config.py` must validate that `app_secret_key` is not the default value on startup.
- API keys are loaded from environment variables, never hardcoded.
- The backend never returns full API keys to the frontend — mask them if displayed.
- `.env` is in `.gitignore`. `.env.example` contains empty placeholder values only.

### 6.5 Input sanitisation

- All user-provided strings embedded in LLM prompts must be length-limited and stripped of control characters.
- Use `Literal` types for constrained fields (e.g., `ChatMessage.role`).
- Use `Query(ge=..., le=...)` for numeric bounds.

### 6.6 Frontend credentials

The `fetchBase` wrapper and all direct `fetch` calls must include:

```typescript
credentials: 'include'
```

This ensures cookies are sent on every request, even when frontend and backend run on different ports during development.

### 6.7 Docker

- Containers run as a non-root user (`USER appuser`).
- Health checks use Python's `urllib` (not `curl`, which isn't in `python:slim`).
- Dependencies are pinned to exact versions in `requirements.txt`.

---

## 7. Error Handling

### 7.1 Exception hierarchy

```
MusicLabError (base)
├── NotFoundError         → 404
├── AuthenticationError   → 401
├── RateLimitError        → 429
└── ExternalAPIError      → 502
```

### 7.2 Layer rules

| Layer         | May raise                              | Must NOT raise      |
|---------------|----------------------------------------|---------------------|
| `router.py`   | `HTTPException`, domain exceptions     | —                   |
| `service.py`  | Domain exceptions (`common/exceptions.py`) | `HTTPException` |
| `client.py`   | `ExternalAPIError`                     | `HTTPException`     |

### 7.3 Error handler registration

`register_error_handlers(app)` must be called in `main.py` after the app is created. This maps domain exceptions to HTTP status codes automatically. Routers should raise domain exceptions, and the handlers convert them.

### 7.4 Frontend error display

- Components that make API calls must have an `error` state variable.
- Errors are displayed in an `.error-msg` element (global CSS class).
- Raw API error messages are **not** shown to users — map them to friendly messages.

---

## 8. Type System

### 8.1 Backend type hints

- Every function and method has full type annotations (parameters + return type).
- Use `T | None` syntax (not `Optional[T]`).
- Use `list[T]`, `dict[K, V]` (not `List[T]`, `Dict[K, V]`).
- `from __future__ import annotations` enables this in all Python versions.

### 8.2 Frontend TypeScript

- `lang="ts"` on every `<script>` block.
- Strict mode enabled in `tsconfig.json`.
- All API response data is typed — no `any` types in production code.
- Use `unknown` for error catches, not `any`.

### 8.3 Type definitions stay in sync

When a backend schema changes, the corresponding frontend type in `$lib/types.ts` must be updated in the same PR. The backend Pydantic model is authoritative.

---

## 9. Naming Conventions

### 9.1 Python (backend)

| Item                | Convention      | Example                     |
|---------------------|-----------------|-----------------------------|
| Files / modules     | `snake_case`    | `auth_service.py`           |
| Classes             | `PascalCase`    | `DiscoveryService`          |
| Functions / methods | `snake_case`    | `get_full_profile()`        |
| Constants           | `UPPER_SNAKE`   | `BASE_URL`                  |
| Variables           | `snake_case`    | `user_id`                   |
| Private members     | `_prefixed`     | `_http`, `_parse_response()`|
| Package `__init__`  | Comment format  | `# MusicLab <name> module`  |

### 9.2 TypeScript / Svelte (frontend)

| Item                | Convention      | Example                     |
|---------------------|-----------------|-----------------------------|
| Files (components)  | `PascalCase`    | `DiscoveryCard.svelte`      |
| Files (lib/utils)   | `camelCase`     | `api.ts`, `formatting.ts`   |
| Interfaces / types  | `PascalCase`    | `DiscoveryCard`             |
| Functions           | `camelCase`     | `handleSubmit()`            |
| Variables           | `camelCase`     | `isLoading`, `errorMsg`     |
| CSS classes         | `kebab-case`    | `.error-msg`, `.btn-primary`|
| Stores              | `camelCase`     | `userStore`, `profileStore` |
| Constants           | `UPPER_SNAKE`   | `API_BASE`                  |

### 9.3 API field names

- Request/response JSON fields use `snake_case` — this matches Python convention.
- The frontend `apiClient` handles any camelCase ↔ snake_case conversion where needed.

---

## 10. Imports & Module Organisation

### 10.1 Python import order

```python
"""Module docstring."""

from __future__ import annotations

# 1. Standard library
import logging
from datetime import datetime, timezone
from uuid import uuid4

# 2. Third-party
import aiosqlite
from fastapi import APIRouter, Depends, Query

# 3. Local application
from app.common.exceptions import ExternalAPIError, NotFoundError
from app.config import settings
```

**Rules:**
- Blank line between each group.
- All imports at the top of the file.
- **No mid-file or in-function imports** unless there's a documented circular dependency.
- No `from module import *`.

### 10.2 TypeScript import order

```typescript
// 1. Svelte / SvelteKit
import { onMount } from 'svelte';
import { goto } from '$app/navigation';

// 2. Lib modules
import { apiClient } from '$lib/api';
import { userStore } from '$lib/stores';
import type { DiscoveryCard } from '$lib/types';

// 3. Components
import DiscoveryCardComp from '$lib/components/DiscoveryCard.svelte';
```

- Use `import type` for type-only imports.
- Prefer named imports over default imports (except for Svelte components).

---

## 11. Styling (CSS)

### 11.1 Design tokens in `app.css` only

All CSS custom properties (`--var-name`) are defined in `app.css` under `:root` and `[data-theme='dark']`. Components must not define their own custom properties.

### 11.2 Global utility classes

Common spacing, layout, and typography utilities live in `app.css`:

```css
/* These exist globally — DO NOT redefine in component <style> blocks */
.flex, .flex-col, .flex-center, .flex-between
.gap-xs, .gap-sm, .gap-md, .gap-lg
.mb-xs, .mb-sm, .mb-md, .mb-lg
.mt-xs, .mt-sm, .mt-md, .mt-lg
.py-md, .py-xl, .py-2xl
.wrap, .items-center, .justify-end
.w-full, .block, .inline-block
.text-sm, .text-lg, .text-xl, .text-2xl
.text-secondary, .text-center
.font-bold, .font-medium
.error-msg
```

**When you need a utility that doesn't exist:** add it to `app.css`, not to a component's `<style>` block.

### 11.3 Component `<style>` blocks

Component styles should only contain:
- Component-specific layout (e.g., `.discovery-card { height: 100% }`)
- Component-specific visual treatments (e.g., `.score-badge`)
- Responsive overrides for that component's layout

They must **not** contain:
- Redefinitions of global utilities (`.mb-md`, `.mt-sm`, `.error-msg`, etc.)
- Hardcoded colour values — use CSS variables instead
- Hardcoded border-radius values — use `var(--radius-sm/md/lg)`

### 11.4 CSS variable usage

```css
/* ✅ Correct */
border-radius: var(--radius-sm);
color: var(--accent);

/* ❌ WRONG — hardcoded magic values */
border-radius: 4px;
color: rgba(108, 92, 231, 0.1);
```

### 11.5 Media query order

```css
/* Mobile-first is the default. Override for larger screens: */
@media (max-width: 1024px) { /* tablets */ }
@media (max-width: 768px)  { /* mobile — must come AFTER 1024px */ }
```

The more-specific (smaller) breakpoint must come **after** the larger one to correctly cascade.

---

## 12. Testing

### 12.1 Test file naming

```
tests/
├── test_auth.py
├── test_discovery.py
├── test_lastfm.py
└── conftest.py       # Shared fixtures
```

Pattern: `test_{module_name}.py`.

### 12.2 Fixture usage

- Database fixtures use `conftest.py` with `@pytest.fixture`.
- Use `aiosqlite` in-memory databases for tests (`:memory:`).
- Test async code with `pytest-asyncio`.

### 12.3 Frontend

- Component tests use Svelte Testing Library.
- API integration tests mock `fetch` via MSW (Mock Service Worker) or similar.

---

## 13. Docker & Deployment

### 13.1 Multi-stage build

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
# ...

# Stage 2: Production backend + static files
FROM python:3.12-slim AS production
# Non-root user
RUN adduser --disabled-password --no-create-home appuser
# ... install deps, copy code ...
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 13.2 Health check

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
```

Do **not** use `curl` — it's not available in `python:slim`.

### 13.3 Dependencies

```
# requirements.txt — ALWAYS pin versions
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic-settings==2.6.0
aiosqlite==0.20.0
httpx==0.27.2
bcrypt==4.2.0
python-multipart==0.0.12
anthropic==0.39.0
openai==1.55.0
```

---

## 14. Checklist for New Code

Before submitting any change, verify:

### Backend
- [ ] `from __future__ import annotations` at top of file
- [ ] All imports at file top (no in-function imports)
- [ ] Google-style docstrings on all public functions
- [ ] Full type annotations on all function signatures
- [ ] `logger = logging.getLogger(__name__)` is set up
- [ ] No silent `except: pass` — all exceptions are logged
- [ ] Service layer uses domain exceptions, not `HTTPException`
- [ ] `ExternalAPIError` uses keyword args (`service=`, `message=`)
- [ ] Router has no `prefix=` or `tags=` — set in `main.py` only
- [ ] All endpoints (except health/login) have `Depends(get_current_user)`
- [ ] Query parameters have `Query(ge=..., le=...)` bounds
- [ ] Table/column names match `schema.sql` exactly
- [ ] Pydantic models only receive fields they define
- [ ] `datetime.now(timezone.utc)` — never `datetime.utcnow()`
- [ ] External URLs use HTTPS

### Frontend
- [ ] `lang="ts"` on all `<script>` blocks
- [ ] Props use `interface Props` + `$props()` pattern
- [ ] Types imported from `$lib/types.ts` — not redefined locally
- [ ] API calls go through `apiClient` only
- [ ] `catch (err: unknown)` — never `catch (err: any)`
- [ ] Error state is displayed to user, not just `console.error`
- [ ] Auth guard uses shared utility, not copy-pasted boilerplate
- [ ] `{#each}` blocks have key expressions
- [ ] No CSS utility class redefinitions in `<style>` blocks
- [ ] All colours use CSS variables — no hardcoded hex/rgba
- [ ] All border-radius values use `var(--radius-*)`
- [ ] No unused components or dead imports

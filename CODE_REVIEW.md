# MusicLab — Code Review: Security & Quality Assessment

**Date**: 2026-07-17
**Reviewer**: AI Code Review (OpenHands)
**Scope**: Entire codebase — backend (Python/FastAPI), frontend (SvelteKit), Docker, configuration

---

## Taste Rating

🔴 **Needs improvement** — Multiple critical security issues, runtime-breaking bugs, and architectural concerns must be addressed before this codebase is production-ready.

---

## [CRITICAL ISSUES] — Must Fix

### 1. [backend/.env] **Hardcoded Secrets on Disk** — 🔴 HIGH

The file `backend/.env` contains **real, live credentials** stored in plaintext:

```
LASTFM_API_KEY='****'
LIDARR_URL='https://lidarr.home.teoreze.com'
LIDARR_API_KEY='****'
DEEPSEEK_API_KEY='sk-****'
AUTH_PASSWORD_HASH='****'
```

While `.env` is in root `.gitignore`, these files exist on disk. If they were ever committed before the gitignore was added, they are permanently in git history. The `LIDARR_URL` points to a real home server (`lidarr.home.teoreze.com`), exposing internal network infrastructure. All four keys must be rotated **immediately**.

**Action**: Rotate all keys, use `.env.example` as a template (copy to `.env` locally), and verify with `git log --all --full-history -- .env` that no `.env` file was ever tracked.

---

### 2. [backend/app/settings/router.py, Lines 53-77] **API Keys Written & Returned in Plaintext** — 🔴 HIGH

The `PUT /api/settings` endpoint **writes API keys directly to the `.env` file** via `dotenv.set_key()`:

```python
if update.lastfm_api_key is not None:
    set_key(str(env_path), "LASTFM_API_KEY", update.lastfm_api_key)
```

And `GET /api/settings` (lines 25-36) **returns every API key unmasked** in the response:

```python
return {
    "lastfm_api_key": settings.lastfm_api_key,
    "lidarr_api_key": settings.lidarr_api_key,
    "anthropic_api_key": settings.anthropic_api_key,
    "openai_api_key": settings.openai_api_key,
    "deepseek_api_key": getattr(settings, "deepseek_api_key", ""),
}
```

Any authenticated user can exfiltrate all configured API keys by calling `GET /api/settings`. The settings page in the frontend (`settings/+page.svelte`) stores these API keys in JavaScript `$state()` where they are accessible via browser DevTools.

**Action**: 
- Never return full API keys from the API. Return masked versions (e.g., `sk-****...c721`).
- Accept partial updates: only write keys that have actually changed (not re-sent as masked).
- Consider using a proper secrets manager or at minimum encrypting the `.env` at rest.

---

### 3. [backend/app/explore/router.py, Line 8] **Broken Import — Will Crash at Runtime** — 🔴 HIGH

```python
from app.common.auth_deps import get_current_user
```

The module `app.common.auth_deps` **does not exist**. The correct import is:

```python
from app.auth.dependencies import get_current_user
```

This will cause an `ImportError` the moment any `/api/explore/*` endpoint is accessed.

---

### 4. [backend/app/explore/seed_service.py, Line 21] **LastfmClient Initialized Without API Key** — 🔴 HIGH

```python
self._lastfm = LastfmClient()
```

The `LastfmClient.__init__` requires `api_key: str` as a positional argument. This will raise a `TypeError` at startup when `seed_if_needed()` calls `supplement_with_lastfm_tags()`.

---

### 5. [backend/app/llm/memory.py, Line 68] **LLM.generate() Called With Wrong Signature** — 🔴 HIGH

```python
response = await self.llm.generate(prompt)
```

The abstract method signature is:

```python
async def generate(self, system_prompt: str, user_message: str, tools: ...) -> LLMResponse:
```

This passes the full prompt as the `system_prompt` parameter, leaving `user_message` missing. For the OpenAI provider, this will fail because `user_message` is required. For Anthropic/Ollama, it raises `NotImplementedError` anyway.

**Action**: Fix the call to match the interface — either split the prompt or add a separate `generate_raw` method to the base class.

---

### 6. [backend/app/llm/providers/anthropic.py, All Methods] & [backend/app/llm/providers/ollama.py, All Methods] **Stub Providers That Raise NotImplementedError** — 🔴 HIGH

Both `AnthropicProvider` and `OllamaProvider` have all core methods stubbed with `raise NotImplementedError`. Yet:
- `config.py` defaults `llm_provider` to `"anthropic"`
- The LLM router's else-clause falls through to `OllamaProvider`

The **only working provider** is `OpenAIProvider` (which also handles DeepSeek by reusing the OpenAI client with a custom `base_url`). Selecting Anthropic or Ollama from the UI will result in 500 errors.

**Action**: Either implement these providers or remove them from the UI selector until they're ready.

---

### 7. [backend/app/settings/router.py, Lines 25-36] **DeepSeek API Key Uses `getattr` Fallback Inconsistently**

```python
"deepseek_api_key": getattr(settings, "deepseek_api_key", ""),
```

All other keys are accessed directly (`settings.lastfm_api_key`), but `deepseek_api_key` uses `getattr` with a fallback. This suggests the field may not exist on the `Settings` model — but it **does** (line 42 of `config.py`). This inconsistency hints at a previous bug that was papered over. If there's a runtime issue where `deepseek_api_key` is sometimes missing, the root cause should be fixed.

---

## [IMPROVEMENT OPPORTUNITIES] — Should Fix

### 8. [backend/app/discovery/service.py, Line 219] **Last.fm Profile Method Used as Artist Data Proxy**

```python
lastfm_data, discogs_data, mb_data = await asyncio.gather(
    self.lastfm.get_full_profile(artist_name),  # <-- wrong method
    ...
)
```

`get_full_profile()` makes **6 parallel API calls** (top artists, albums, tags, recent tracks, loved tracks, weekly chart) to Last.fm — but for artist enrichment, you only need `get_artist_info()`. This wastes API quota and adds latency for every discovery card.

**Action**: Use `self.lastfm.client.get_artist_info(artist_name)` directly instead.

---

### 9. [backend/app/explore/service.py, Lines 82-131] **Sort Order Logic Bug for Name Sorting**

When `sort_by="name"`, the default `order_by` is `"a.name ASC"`. If `sort_order="desc"` (the default), the code does nothing (the replace only triggers on `"asc"`), so the sort stays ASC. Sorting by name will always be ascending regardless of user selection.

```python
order_by = "a.name ASC"
# ...
if filters.sort_order == "asc":
    order_by = order_by.replace("DESC", "ASC")
# "DESC" not found in "a.name ASC" → no-op
# Result: always ASC
```

**Action**: Build the ORDER BY clause from validated values rather than string-replacing:
```python
column = {"listeners": "a.lastfm_listeners", "scrobbles": "a.lastfm_playcount", "name": "a.name"}[filters.sort_by]
direction = "ASC" if filters.sort_order == "asc" else "DESC"
order_by = f"{column} {direction}"
```

---

### 10. [backend/app/config.py, Line 1-3] **`from __future__ import annotations` Placed Before Docstring**

Per the project's own ARCHITECTURE.md (§2.1), every file must start with the module docstring, then `from __future__ import annotations`. This file has them reversed. This is a minor standards violation but signals that the conventions aren't being consistently followed.

---

### 11. [.env.example] **Missing `DEEPSEEK_API_KEY` Field**

`config.py` defines `deepseek_api_key: str = ""` and the settings router reads/writes it, but `.env.example` doesn't list it. Users following the example file won't know this configuration option exists.

---

### 12. [backend/app/main.py, Line 61] **Hardcoded CORS Origin**

```python
allow_origins=["http://localhost:5173"],
```

This only works in local development. For Docker/production deployment, the frontend is served from the same origin (port 8000) via StaticFiles, so CORS isn't needed there — but the hardcoded value should at minimum be configurable via environment variable for flexibility.

---

### 13. [backend/app/common/middleware.py, Lines 80-89] **Rate Limiting Is a No-Op Placeholder**

```python
async def rate_limit_middleware(request: Request, call_next):
    """Placeholder rate-limiting middleware. TODO: ..."""
    response = await call_next(request)
    return response
```

The login endpoint has no brute-force protection. Combined with the single-user design (only one admin user), this means an attacker can hammer `/api/auth/login` indefinitely.

**Action**: Implement token-bucket or sliding-window rate limiting, at minimum on the login endpoint.

---

### 14. [backend/app/auth/router.py, Line 48] **Session Cookie `secure` Flag Tied to Environment Name**

```python
secure=settings.environment == 'production',
```

This is the correct approach for local dev, but the environment variable `ENVIRONMENT` defaults to `"development"`. If someone deploys to a real server but forgets to set `ENVIRONMENT=production`, session cookies will be transmitted over HTTP (no `Secure` flag). Consider also checking whether the request itself arrived over HTTPS.

---

### 15. [backend/app/explore/service.py, Lines 168-169] **Silent Exception Swallowing**

```python
except Exception:
    logger.warning("Failed to fetch lastfm info for %s", artist_name)
    lf_info = {}
```

Multiple places in `enrich_and_cache_artist` catch `Exception` broadly and continue with empty data. While the intent is resilience against external API failures, this also swallows programming errors (e.g., `AttributeError`, `TypeError`) making them hard to debug. Consider catching only `ExternalAPIError` and `httpx.HTTPError`.

---

### 16. [frontend/src/routes/login/+page.svelte, Line 19] **`catch (err: any)` Instead of `unknown`**

```typescript
} catch (err: any) {
```

Per the ARCHITECTURE.md checklist (§14), catch blocks must use `err: unknown`. Using `any` bypasses TypeScript's type safety.

---

### 17. [frontend/src/routes/settings/+page.svelte, Lines 25-35] **Settings Page Bypasses apiClient**

```typescript
const res = await fetch('/api/settings');
```

The settings page uses raw `fetch()` instead of the centralized `apiClient`. This means:
- No automatic error handling via `ApiError`
- No `credentials: 'include'` consistency guarantee
- Bypasses the `fetchBase` error wrapper

The `saveSettings()` function (line 42) has the same issue.

---

### 18. [frontend/src/routes/settings/+page.svelte, Lines 89-144] **CSS Utility Redefinitions in Component Style**

```css
.mb-md { margin-bottom: var(--space-md); }
.mb-sm { margin-bottom: var(--space-sm); }
.mt-sm { margin-top: var(--space-sm); }
.mt-md { margin-top: var(--space-md); }
.py-xl { padding: var(--space-xl) 0; }
.w-full { width: 100%; }
```

These global utility classes are redefined in the component `<style>` block. Per ARCHITECTURE.md (§11.2), these already exist in `app.css` and must not be redefined. Same issue in `login/+page.svelte`.

---

### 19. [backend/tests/] **Only One Trivial Test Exists**

The test suite contains exactly one test (`test_health`) that checks the health endpoint returns `{"status": "ok"}`. There are no tests for:
- Authentication (login, logout, session expiry)
- Settings CRUD (including the API key exposure issue)
- Discovery pipeline
- LLM chat flow
- Explore endpoints

This means there is **zero regression protection** for any of the issues identified above.

---

## [SECURITY ANALYSIS]

### Secrets Management — 🔴 CRITICAL

| Secret | Location | Risk |
|--------|----------|------|
| Last.fm API Key | `backend/.env` (plaintext) | Exposure on disk |
| Lidarr API Key | `backend/.env` (plaintext) | Internal service access |
| Lidarr URL | `backend/.env` (plaintext) | Internal network recon |
| DeepSeek API Key | `backend/.env` (plaintext) | LLM API abuse/cost |
| Auth Password Hash | `backend/.env` (plaintext) | Credential cracking |

### Attack Surface Summary

1. **Authenticated API key exfiltration**: `GET /api/settings` returns all keys unmasked
2. **Credential stuffing**: No rate limiting on `/api/auth/login`
3. **Internal network exposure**: `LIDARR_URL` reveals internal hostname
4. **Session security**: Cookie `Secure` flag depends on correct `ENVIRONMENT` setting
5. **No CSP/Security headers**: Missing `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`

---

## [TESTING GAPS]

- **No auth tests**: Login, logout, session validation, password hashing
- **No settings tests**: API key masking, .env write behavior
- **No discovery tests**: LLM response parsing, artist enrichment, batch generation
- **No explore tests**: Genre tree, artist queries, pagination, sort ordering
- **No error handling tests**: External API failures, malformed LLM responses, DB errors

---

## [ARCHITECTURAL OBSERVATIONS]

### What's Good

- **Clean module structure** — The 4-file module pattern (schemas, client, service, router) is consistently applied and well-designed
- **Proper async patterns** — `asyncio.gather()` for parallel API calls, async generators for DB connections
- **Separation of concerns** — Services don't import FastAPI types, HTTP concerns stay in routers
- **Sensible dependency injection** — FastAPI `Depends()` is used throughout
- **Good cryptography choices** — bcrypt for passwords, `secrets.token_urlsafe()` for sessions
- **HTTP-only session cookies** — Correct use of `httponly`, `samesite=lax`

### What's Concerning

- **API keys as mutable settings**: Writing secrets to `.env` at runtime via an HTTP endpoint is an anti-pattern. API keys should be treated as deployment configuration, not user settings.
- **Single-user design without multi-tenancy**: The auth system creates one admin user from env vars. This is fine for a personal project but the architecture won't scale to multiple users without significant refactoring.
- **Stub implementations in critical path**: Two of four LLM providers are unimplemented stubs, yet selectable from the UI.

---

## [RISK ASSESSMENT]

- **[Overall Codebase]** ⚠️ Risk Assessment: 🔴 **HIGH**

**Factors**:
- Live API keys and internal network URLs exposed on disk
- API endpoints return secrets unmasked to any authenticated user
- Multiple runtime-breaking bugs (broken imports, wrong function signatures) would crash the app
- Stub LLM providers in the default configuration path
- No rate limiting, no security headers, no brute-force protection
- Near-zero test coverage

**Recommendation**: Do not deploy in current state. Address all CRITICAL issues first, rotate exposed credentials immediately, and add test coverage before considering any production use.

---

## VERDICT

❌ **Needs rework** — Multiple critical security and runtime-blocking issues must be addressed before this codebase is safe to run.

**KEY INSIGHT**: The most dangerous pattern is treating API keys as mutable user settings — exposing them via `GET /api/settings` and writing them to `.env` via `PUT /api/settings`. This design turns any authenticated session into a full credential exfiltration vector. API keys should be read-only deployment configuration, never returned by the API.

---

> **Improve this review?** If any feedback above seems incorrect or irrelevant to this repository, you can teach the reviewer to do better:
>
> 1. Add a `.agents/skills/custom-codereview-guide.md` file to your branch (or edit it if one already exists) with the `/codereview` trigger and the context the reviewer is missing.
> 2. Re-request a review — the reviewer reads guidelines from the PR branch, so your changes take effect immediately.
> 3. When your PR is merged, the guideline file goes through normal code review by repository maintainers.
>
> **Resolve with AI?** Install the [iterate skill](https://github.com/OpenHands/extensions/tree/main/skills/iterate) in your agent and run `/iterate` to automatically drive this PR through CI, review, and QA until it's merge-ready.
>
> Was this review helpful? React with 👍 or 👎 to give feedback.

# MusicLab — Agent Rules

## Mandatory Reading

Before making ANY code changes, read and follow [ARCHITECTURE.md](../ARCHITECTURE.md). It is the single source of truth for all coding standards.

## Key Rules

1. **Never create duplicate type definitions.** Types live in one place: `backend/**/schemas.py` for Python, `frontend/src/lib/types.ts` for TypeScript.
2. **Never set prefix/tags on APIRouter() directly.** Prefixes are set only in `main.py` via `app.include_router()`.
3. **Service layer must not import FastAPI types.** Services raise domain exceptions from `common/exceptions.py`.
4. **All Python files must start with** `from __future__ import annotations`.
5. **All catch blocks must log the exception**, never silently swallow errors.
6. **Table/column names in code must exactly match `schema.sql`.**
7. **CSS utility classes are global only** — never redefine `.mb-md`, `.error-msg`, etc. in component `<style>` blocks.
8. **Frontend props use `interface Props` pattern** — no generic `$props<{}>()` or inline types.
9. **All endpoints require auth** except `/api/health` and `/api/auth/login`.
10. **Pin all dependency versions** in `requirements.txt`.

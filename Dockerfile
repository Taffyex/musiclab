# ──────────────────────────────────────────────
# Stage 1: Build SvelteKit frontend
# ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ──────────────────────────────────────────────
# Stage 2: Python backend + static frontend
# ──────────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy frontend build output into static directory
COPY --from=frontend-builder /app/frontend/build ./static

# Create non-root user
RUN adduser --disabled-password --no-create-home appuser

# Create data directory for SQLite and set permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

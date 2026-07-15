# MusicLab 🎵

AI-powered music discovery and library management. Combines Last.fm listening history, LLM-driven recommendations, and Lidarr integration into a single self-hosted dashboard.

## Tech Stack

- **Backend:** Python / FastAPI / aiosqlite
- **Frontend:** SvelteKit (static build served by FastAPI)
- **LLM:** Anthropic Claude · OpenAI · Ollama (configurable)
- **Integrations:** Last.fm API, Lidarr, Discogs

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Run with Docker Compose
docker compose up -d

# 3. Open http://localhost:8000
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

See [PLAN.md](./PLAN.md) for full architecture details, data flow diagrams, and design decisions.

# HALFLIGHT

AI-driven persistent text RPG. A deterministic Python engine is the source of truth;
a local LLM parses free-text intent and narrates outcomes. See `HANDOFF.md` for the
full design and milestone plan.

## Requirements

- Python 3.12 (managed by `uv`)
- Docker Desktop (for Postgres + pgvector)
- llama.cpp `llama-server` on the host (chat + embedding), for M4 onwards

## Setup

```powershell
# 1. Install deps into a local .venv (Python 3.12 pinned in pyproject)
uv sync

# 2. Copy env file
Copy-Item .env.example .env

# 3. Start Postgres (pgvector/pgvector:pg16)
docker compose up -d

# 4. Run migrations (enables the vector extension)
uv run alembic upgrade head

# 5. Run the server
uv run uvicorn halflight.main:app --reload
```

Health check:

```powershell
curl http://localhost:8000/healthz    # -> {"status":"ok"}
```

## Tests

```powershell
uv run pytest          # all tests
uv run pytest -k engine
```

## Lint / types

```powershell
uv run ruff check .
uv run mypy server
```

## llama.cpp servers (M4+)

Run on the host so the GPU is directly accessible on Windows.

```powershell
# terminal 1 — chat model
cd C:\llama.cpp
.\llama-server.exe -m C:\models\Qwen_Qwen3.6-27B-Q4_K_M.gguf `
  -ngl 99 --ctx-size 16384 --host 127.0.0.1 --port 8080 --prompt-cache-all

# terminal 2 — embeddings (bge-m3)
.\llama-server.exe -m C:\models\bge-m3-Q8_0.gguf `
  --embedding --host 127.0.0.1 --port 8081
```

## Layout

- `server/halflight/` — application package (engine, ingest, gm, api)
- `migrations/` — Alembic migrations
- `vault/` — Obsidian vault (game canon), ingested into Postgres
- `web/` — terminal-style UI

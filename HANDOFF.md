# HALFLIGHT — Claude Code Handoff

**Owner:** Quenten
**Status:** New project, kickoff.
**Purpose of this doc:** Everything Claude Code needs to build HALFLIGHT. Paste this into Claude Code as the first message (or drop it as `HANDOFF.md` in the repo root and point Claude Code at it).

---

## 0. Elevator pitch

An AI-driven persistent text RPG in the vein of [NERVEJACK](https://nervejack.gg). Player types free-text actions; a deterministic Python engine resolves them (dice, state, permadeath); a local LLM (Qwen3.6 27B on a 4090 via llama.cpp) parses the intent and narrates the outcome. World lore lives in an Obsidian vault and is ingested into Postgres + pgvector for retrieval.

**Setting:** original dystopian off-world colony — inspired by the *tone* of the game *beta decay* (decaying frontier exoplanet, corporate arcologies, syndicate under-levels, failing terraforming). Do not reuse names, factions, or lore from that game — the setting is original.

**Hobby now, potentially productizable later.** Optimize for a working single-player loop on the owner's machine. No auth, no multi-tenant, no cloud.

---

## 1. Core design principle

**Engine is source of truth. LLM interprets and narrates.**

- LLM never decides hit/miss, damage, cost, item existence, or NPC alive/dead.
- LLM does two things per turn:
  1. Parse free text into structured action JSON (grammar-constrained decoding).
  2. Narrate the engine's `TurnResult` using retrieved lore and NPC memory.
- If retrieval finds nothing on a lore question, the narrator says the character doesn't know — never guesses. This is a hard prompt rule.

This makes hallucination structurally impossible for anything mechanical, and matches NERVEJACK's documented GM behavior.

---

## 2. Tech stack (decided, do not re-litigate)

- **Language:** Python 3.12
- **Web framework:** FastAPI (with SSE streaming for narration)
- **DB:** Postgres 16 with the `pgvector` extension
- **ORM:** SQLModel (Pydantic-integrated SQLAlchemy)
- **Migrations:** Alembic
- **LLM runtime:** llama.cpp `llama-server` (already installed at `C:\llama.cpp` on owner's machine, CUDA 13.3 build)
- **Model:** Qwen3.6 27B Instruct, Q4_K_M GGUF, at `C:\models\Qwen_Qwen3.6-27B-Q4_K_M.gguf`
- **Embeddings:** bge-m3 GGUF via a second llama.cpp `--embedding` server (grab a bge-m3 GGUF from HF; ~600MB)
- **Frontend:** minimal terminal-style HTML + HTMX (or plain fetch + SSE). No SPA framework.
- **Container:** Docker Compose for Postgres. llama.cpp runs on the host to keep GPU access simple on Windows.
- **Package manager:** `uv` (fast, modern; falls back to pip if unavailable).
- **OS:** Windows 11 for dev. Owner uses PowerShell.

---

## 3. Repo layout

```
halflight/
├── HANDOFF.md                    # this file
├── docker-compose.yml            # postgres + pgvector
├── pyproject.toml
├── .env.example
├── vault/                        # Obsidian vault (git-tracked)
│   ├── _templates/
│   ├── locations/
│   ├── npcs/
│   ├── factions/
│   ├── items/
│   ├── lore/
│   └── rules/
│       └── gm_style.md           # tone guide, banned outputs
├── server/
│   ├── halflight/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   ├── config.py             # env-based settings (pydantic-settings)
│   │   ├── db.py                 # engine, session
│   │   ├── models/               # SQLModel tables
│   │   ├── schemas/              # Pydantic request/response
│   │   ├── engine/               # deterministic game logic (NO LLM)
│   │   │   ├── actions.py        # Action union types
│   │   │   ├── resolver.py       # dice + rules
│   │   │   ├── state.py          # state mutation
│   │   │   └── turn.py           # orchestrates one turn
│   │   ├── ingest/               # vault -> DB
│   │   │   ├── parser.py         # frontmatter + body
│   │   │   ├── linter.py         # broken links, missing fields
│   │   │   ├── embedder.py       # chunks -> pgvector
│   │   │   └── cli.py            # `python -m halflight.ingest`
│   │   ├── gm/                   # LLM orchestration
│   │   │   ├── client.py         # llama.cpp HTTP client
│   │   │   ├── parser.py         # intent parsing (JSON-grammar)
│   │   │   ├── narrator.py       # narration prompt assembly
│   │   │   ├── retrieval.py      # merged lore+event chunk search
│   │   │   └── grammars/
│   │   │       └── action.gbnf
│   │   └── api/
│   │       ├── turn.py           # POST /turn (SSE)
│   │       ├── state.py          # GET /state
│   │       └── admin.py          # ingest trigger, debug
│   └── tests/
│       ├── test_engine.py        # engine playable without LLM
│       ├── test_ingest.py
│       └── fixtures/vault_mini/  # tiny vault for tests
└── web/
    └── index.html                # terminal UI
```

---

## 4. Milestone plan

Build in order. Do not skip ahead. Each milestone has a hard exit criterion — if it doesn't pass, do not start the next one.

### M0 — Bootstrap (session 1)

- [ ] `git init`, add `.gitignore` (Python, Windows, `.env`, `models/`, `venv/`)
- [ ] `pyproject.toml` with: fastapi, uvicorn, sqlmodel, alembic, psycopg[binary], pgvector, python-frontmatter, httpx, pydantic-settings, pytest, pytest-asyncio, ruff, mypy
- [ ] `docker-compose.yml` with a `pgvector/pgvector:pg16` container on port 5432
- [ ] `.env.example` with `DATABASE_URL`, `LLAMA_CHAT_URL=http://127.0.0.1:8080`, `LLAMA_EMBED_URL=http://127.0.0.1:8081`
- [ ] Alembic init + first migration enabling the `vector` extension
- [ ] `main.py` with a `/healthz` route
- [ ] README with dev commands

**Exit:** `docker compose up -d`, `uvicorn halflight.main:app --reload`, `curl localhost:8000/healthz` returns 200.

### M1 — Vault schema + seed content

Author templates and a minimal seed world *before* writing ingestion — the schema is the contract.

Frontmatter contracts (canonical — do not deviate):

**locations/*.md**
```yaml
---
id: loc_<slug>              # permanent, unique, snake_case
type: location
name: <display name>
district: <district_slug>
danger: 0                   # 0-5
connections: [loc_x, loc_y]
tags: [public, transit]
---
```

**npcs/*.md**
```yaml
---
id: npc_<slug>
type: npc
name: <display name>
faction: fac_<slug>         # or null
role: <freeform>
location: loc_<slug>        # home/default
disposition_default: 0      # -100..100
stats: {muscle: 10, nerve: 10, wits: 10, tech: 10, streetwise: 10, presence: 10}
hp: 15
schedule: {day: loc_x, night: loc_y}   # optional
alive: true
---
```

**factions/*.md**
```yaml
---
id: fac_<slug>
type: faction
name: <display name>
rivals: [fac_x]
allies: [fac_y]
territory: [loc_x, loc_y]
---
```

**items/*.md**
```yaml
---
id: itm_<slug>
type: item
name: <display name>
kind: weapon | consumable | key | misc
value: 100                  # credits
effects: {damage: 6}        # freeform, engine interprets by kind
---
```

**Rules for all note bodies:**
- Body = narrator flavor and lore. Free markdown.
- Wikilinks `[[loc_x]]` define graph relationships beyond frontmatter.
- Sections under a heading `## Secret` are excluded from retrieval until an engine event flips their `revealed` flag. Ingestion must detect and isolate these chunks.

Seed content to author (owner will write; Claude Code can draft):
- 10 locations in 1 district
- 10 NPCs (across 2 factions)
- 2 factions
- 15 items
- 5 lore notes
- 1 `rules/gm_style.md` (owner writes this himself — it's the game's voice)

**Exit:** vault lint script passes (unique ids, no broken wikilinks, required frontmatter present, no reserved id collisions).

### M2 — Ingestion

`python -m halflight.ingest` walks the vault:

- [ ] Parse frontmatter via `python-frontmatter`. Upsert into typed tables.
- [ ] Chunk note bodies by heading (~300 tokens/chunk, respect markdown boundaries).
- [ ] Detect `## Secret` sections; store as chunks with `revealed=false`.
- [ ] Embed non-secret chunks via bge-m3 embedding server; store in `lore_chunks(embedding VECTOR(1024))`.
- [ ] Hash each note; only re-embed changed notes.
- [ ] Emit a lint report on stderr (broken links, missing fields, duplicate ids). Non-zero exit on hard errors.

**Exit:** given the seed vault, `SELECT * FROM locations` returns 10 rows; `SELECT * FROM lore_chunks` returns dozens; a top-k similarity search for "who runs the tram hub" returns plausible chunks.

### M3 — Engine core, NO LLM

Pure Python. Fully unit-testable via structured JSON actions. **Do not touch the LLM in this milestone.**

Action model (Pydantic discriminated union):
```python
class Move(BaseModel):
    kind: Literal["move"]
    target: str  # location id

class Talk(BaseModel):
    kind: Literal["talk"]
    target: str  # npc id
    topic: str | None = None

class Attack(BaseModel):
    kind: Literal["attack"]
    target: str
    method: str | None = None

class Trade(BaseModel):
    kind: Literal["trade"]
    target: str
    item: str
    direction: Literal["buy", "sell"]

class UseItem(BaseModel):
    kind: Literal["use_item"]
    item: str
    target: str | None = None

class Investigate(BaseModel):
    kind: Literal["investigate"]
    target: str | None = None  # location/object/npc

class Custom(BaseModel):
    kind: Literal["custom"]
    description: str
    stat_hint: Literal["muscle","nerve","wits","tech","streetwise","presence"] | None = None

Action = Annotated[Move|Talk|Attack|Trade|UseItem|Investigate|Custom, Field(discriminator="kind")]
```

Resolver rules:
- Validation: target present in scene, connection exists, item owned. Invalid → `TurnResult` with `outcome=invalid, reason=...`.
- Skill checks: `d20 + stat_mod vs difficulty`. Difficulties on a coarse table (trivial 5, easy 10, medium 15, hard 20, very hard 25).
- Combat: attacker roll vs defender defense; damage = weapon base + margin/2 (tune later).
- `Custom`: engine assigns a plausibility class (allowed / hard / impossible) via simple heuristics + roll under the hinted stat.

`TurnResult` schema (fed to narrator, never contradicted):
```python
class StateChange(BaseModel):
    entity: str  # "player" or npc id
    field: str
    delta: Any

class SceneEvent(BaseModel):
    kind: str  # "attack_hit", "npc_died", "guard_alerted", "item_gained"
    detail: dict

class TurnResult(BaseModel):
    action: Action
    valid: bool
    reason: str | None
    roll: int | None
    difficulty: int | None
    outcome: Literal["success","failure","invalid","narrative_only"]
    state_changes: list[StateChange]
    scene_events: list[SceneEvent]
    significance: int  # 0-3, drives embedding of event
```

Event log: append every `TurnResult` to an `events` table with a monotonic `turn_no`.

**Exit:** `pytest -k engine` passes an integration test that walks the seed world, talks to an NPC, attacks, dies, without a model process running.

### M4 — LLM integration

Bring up llama.cpp. Owner has already downloaded model. Startup commands to put in README:

```powershell
# terminal 1 — chat model
cd C:\llama.cpp
.\llama-server.exe -m C:\models\Qwen_Qwen3.6-27B-Q4_K_M.gguf `
  -ngl 99 --ctx-size 16384 --host 127.0.0.1 --port 8080 `
  --prompt-cache-all

# terminal 2 — embeddings (bge-m3)
.\llama-server.exe -m C:\models\bge-m3-Q8_0.gguf `
  --embedding --host 127.0.0.1 --port 8081
```

Two calls per turn:

**Parse call** (`gm/parser.py`):
- Endpoint: `POST /completion`
- Body: `{ prompt, grammar: <GBNF for Action union>, temperature: 0.2, n_predict: 200 }`
- Grammar file `grammars/action.gbnf` covers all `kind` variants.
- On grammar parse failure (shouldn't happen with grammar) or logically nonsensical output: retry once at temp 0, else fall through to a `Custom` action.

**Narrator call** (`gm/narrator.py`):
- Endpoint: `POST /v1/chat/completions` (OpenAI-compatible)
- Streaming (`stream: true`), temp 0.8, ~250 tokens max.
- System prompt built from `vault/rules/gm_style.md` — **cached across turns** using llama.cpp's prompt cache.
- User prompt = context bundle (see §5).
- Hard rules injected: never contradict TurnResult; never invent items/credits/NPCs; if retrieval empty on a lore question, say character doesn't know; second-person, past tense, 100–250 words.

**Fact-check pass:** after narration, a cheap regex/keyword check that numeric outcomes weren't contradicted (e.g. narration says "your knife sinks in" but `outcome=failure`). On mismatch: regenerate once, then fall back to a terse factual paragraph.

**Log everything.** Every prompt + completion pair to `logs/turns/{run_id}/{turn_no}.json`. This is the future fine-tuning dataset.

**Exit:** manual 20-turn session in the browser with zero factual contradictions in narration.

### M5 — API + minimal UI

- `POST /turn` — takes `{run_id, text}`, streams narration via SSE, returns final state snapshot in a trailing event
- `GET /state?run_id=...` — full state
- `POST /admin/ingest` — triggers vault re-ingestion
- `web/index.html`: input box, streaming text area, status bar (HP / CR / time / location). HTMX SSE or plain `EventSource`. No build step.

**Exit:** playable from a browser on the same LAN (owner's phone).

### M6 — Memory layers

Add incrementally, in this order:

1. **Rolling episodic summary.** Background task; every 20 turns or on location change, compress oldest verbatim turns into a structured summary (`facts_established`, `promises_made`, `open_threads`). Keep last 6 turns verbatim.
2. **Event embedding.** Events with `significance >= 2` get a one-line factual description embedded into `event_chunks`. Retrieval merges `lore_chunks` and `event_chunks` with a recency boost on events.
3. **NPC memory.** `npc_memories(npc_id, event_id, how_known: witnessed|told|public, ts)`. Same-location NPCs get `witnessed`; retrieval into narrator context filters to memories relevant to the NPC currently in scene.
4. **Gossip propagation.** Cron-style task on world-clock tick: for each faction, propagate a subset of `witnessed` events to same-faction NPCs as `told`. Rate-limited to feel organic.
5. **Secrets reveal.** Engine events can flip `revealed=true` on secret chunks. Retrieval respects the flag.

### M7 — Iteration

Lifepath generator (engine tables + one narrator call), faction reputation effects, HEAT-equivalent (colony sec response), vault webhook hot-reload, eventual LoRA fine-tune on accumulated turn logs.

---

## 5. Per-turn context assembly (token budget ~6k)

```
[system: gm_style.md + hard rules]            ~1.5k  (prompt-cached)
[hard state: player + scene NPCs + location]  ~0.8k
[episodic: rolling summary]                   ~0.8k
[retrieval: top-6 merged lore+event chunks]   ~1.5k
[recent: last 6 turns verbatim]               ~1.2k
[TurnResult of current turn]                  ~0.2k
```

Chunk ranking: cosine similarity on player input + current scene. Event chunks get a recency boost (`score * (1 + 0.1 * log(recency))`). Filter chunks by `revealed=true` and by scene-relevance where applicable.

---

## 6. Data model (Postgres)

Sketch — Claude Code should refine and add indexes as needed.

```sql
-- Authored (from vault)
locations(id PK, name, district, danger, connections TEXT[], tags TEXT[], body_hash)
npcs(id PK, name, faction_id FK, role, home_location_id FK, disposition_default,
     stats JSONB, hp_max, schedule JSONB, body_hash)
factions(id PK, name, rivals TEXT[], allies TEXT[], territory TEXT[], body_hash)
items(id PK, name, kind, value, effects JSONB, body_hash)
lore_chunks(id PK, source_note_id, source_type, chunk_ix, body TEXT,
            embedding VECTOR(1024), is_secret BOOL, revealed BOOL DEFAULT false)

-- Runtime (per playthrough)
runs(id PK, character_name, archetype, started_at, ended_at, cause_of_death)
player_state(run_id PK/FK, hp, credits, location_id, stats JSONB, time_ticks)
inventory(run_id FK, item_id FK, quantity)
npc_state(run_id, npc_id, hp, alive, disposition, current_location, PK(run_id, npc_id))
faction_rep(run_id, faction_id, rep, PK(run_id, faction_id))
events(id PK, run_id FK, turn_no, action JSONB, result JSONB, significance,
       location_id, witnesses TEXT[], ts)
event_chunks(event_id PK/FK, description TEXT, embedding VECTOR(1024), ts)
summaries(run_id FK, up_to_turn, body JSONB)   -- structured summary
npc_memories(run_id, npc_id, event_id, how_known, ts, PK(run_id, npc_id, event_id))
```

Indexes: `events(run_id, turn_no)`, HNSW on both `embedding` columns, `npc_memories(run_id, npc_id)`.

---

## 7. Non-negotiables

- Vault is one-way. **Never write to vault from runtime.** Vault = canon, DB = what happened.
- Engine never calls the LLM. It only produces `TurnResult`.
- LLM never mutates state. It only produces text.
- Grammar-constrained decoding on every parse call. Not optional.
- Every prompt + completion is logged to disk.
- Any new dependency needs a one-line justification in the PR/commit message.
- Owner is Dutch, terse, hates fluff. Match that in commits and READMEs.

---

## 8. Owner environment (already set up)

- Windows 11, PowerShell, RTX 4090
- Driver 596.49, CUDA 13.2
- `C:\llama.cpp\` — llama.cpp b9940 CUDA 13.3 build + CUDA 13.3 runtime DLLs
- `C:\models\Qwen_Qwen3.6-27B-Q4_K_M.gguf` (once download completes)
- Postgres not yet installed → use Docker Compose

Not yet installed, Claude Code should set up:
- Python 3.12 (via uv or from python.org)
- `uv` (`pip install uv` or the standalone installer)
- Docker Desktop (already installed on this machine, verify with `docker --version`)
- bge-m3 GGUF for embeddings — grab from HF (e.g. `gpustack/bge-m3-GGUF`, Q8_0 quant, ~600MB)

---

## 9. First session for Claude Code

Do M0 in full, then stop and show the owner:
1. `curl localhost:8000/healthz` returning 200
2. `psql` (or a query via SQLModel) confirming `vector` extension is loaded
3. A working `pytest` invocation on an empty test file

Then propose a git commit message and wait for the go-ahead on M1.

**Do not attempt M1–M6 in one shot.** Small, verifiable steps. Owner will run commands and paste output.

---

## 10. Reference: NERVEJACK's documented behavior (target quality bar)

- GM can answer questions but can't change the character sheet.
- If GM doesn't know a rule or a fact not yet revealed in the run, it says so plainly rather than guess.
- Everything that changes state must happen through in-fiction play.
- Persistent world: dead NPCs stay dead, spent credits are gone, factions remember.

These are behavioral targets for the narrator prompt.

---

## 11. Working title

**HALFLIGHT.** Placeholder. Owner may rename.

# Architecture

SakThai is a small, layered Python package. Each layer has one job; keep them
separate.

```
                ┌─────────────────────────────────────────────┐
   sakthai run  │                   CLI (click)                │  sakthai mcp
   ───────────▶ │   cli/ — learn, recall, memory, run, mcp,    │ ◀───────────
                │         cycle, skills, extensions, dashboard  │
                └───────────────┬───────────────┬──────────────┘
                                │               │
                  ┌─────────────▼──┐      ┌──────▼───────────┐
                  │  agent/loop    │      │  mcp/server      │
                  │  (Claude/Gemini│      │  (JSON-RPC stdio)│
                  │   tool loop)   │      └──────┬───────────┘
                  └───────┬────────┘             │
                          │   shared tool registry (agent/tools.py)
                          └──────────────┬───────┘
                                         │
                            ┌────────────▼────────────┐
                            │   memory/store.py        │
                            │   MemoryStore (SQLite)   │
                            └────────────┬─────────────┘
                                         │
                                  ~/.sakthai/memory.db
```

## Layers

**`config.py`** — the single source of truth for paths and env-var names
(`sakthai_home`, `memory_db_path`, `sessions_dir`, `check_env`). Nothing else
hard-codes a path.

**`auth.py`** — credential resolution. Anthropic chain: `ANTHROPIC_API_KEY` →
`ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token. Google: the Gemini CLI OAuth
token. OpenAI/Ollama: `resolve_openai_credentials` resolves to `OPENAI_API_BASE` or `OLLAMA_HOST`. Use `resolve_anthropic_client()` rather than constructing a client.

**`memory/`** — `store.MemoryStore` is the only code that touches SQLite. It
holds *facts* and *observations*, with search, tagging, dedupe, consolidation,
stats, and snapshot import/export. `provider.SakThaiMemoryProvider` adapts the
store into a system-prompt block; `backup.py` makes timestamped copies.

**`learn/capture.py`** — the explicit write path: open store, add one fact,
close. Backs `sakthai learn`.

**`agent/`** — `tools.py` defines the tool registry (one schema + handler per
tool) shared by both the agent loop and the MCP server. `loop.run_agent`
injects `store.render_prompt_block()` into the system prompt and dispatches tool
calls against Claude, Gemini, OpenAI, or Ollama compatible backends. The client and store are injectable for testing.

**`mcp/server.py`** — a dependency-free JSON-RPC 2.0 stdio server.
`handle_request` is a pure function, so the protocol is unit-testable without a
process. It reuses the same tool registry as the loop.

**`cycle/`** — the six-stage Dream → Growth state machine, persisted as a single
fact in the store.

**`skills.py`** — parse, catalog, and validate `SKILL.md` files under `skills/`
and `library/`.

**`extensions/`** — clone skill/MCP bundles from git into `~/.sakthai`.

**`dashboard/`** — `data.py` builds an honest snapshot of the store (testable,
no UI deps); `app.py` renders it with Streamlit.

**`cloud/`** — a roadmap stub for Google ADK / Vertex AI deployment. `runtime.py`
describes a cloud agent (`CloudAgentSpec`), reports readiness (`cloud_status`),
and renders a deployment manifest, all without importing `google-adk` at module
load; `build_adk_agent` imports it lazily behind the optional `cloud` extra.
`tools.py` exposes the memory surface as native ADK function tools, going
through `MemoryStore` like every other runtime. See [`cloud.md`](cloud.md).

## Memory schema

```sql
facts(id, kind DEFAULT 'note', key, value NOT NULL,
      source_session, created_at, updated_at, tags)   -- tags: JSON array, NULL when empty

observations(id, summary NOT NULL, evidence_session_id,
             weight DEFAULT 1.0, confidence DEFAULT 0.5, created_at)
```

Schema changes are additive migrations in `_migrate_schema()` (ALTER TABLE only,
run under `BEGIN IMMEDIATE`).

## Conventions

- The test suite runs with no network and no GCP credentials.
- `config.py` owns all paths; new paths go there.
- `read_file` is sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`.
- `run_command` is opt-in via `SAKTHAI_SHELL_ALLOW`.

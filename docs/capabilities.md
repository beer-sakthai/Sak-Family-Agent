# Capabilities

## Tools

These are exposed both to the agent loop (`sakthai run`) and over MCP
(`sakthai mcp`). The registry lives in `personas/sakthai/sakthai/agent/tools.py`.

| Tool | What it does | Notes |
|------|--------------|-------|
| `learn` | Save a fact (value, kind, key) | The agent's write path into memory |
| `ingest_document` | Split a Markdown/CSV/text file into facts | Parse-only |
| `capture_lead` | Store a structured lead (name, phone, email, query) | — |
| `recall` | List recent facts + top observations | Read what's already known |
| `search` | Substring search over facts + observations | Targeted lookup |
| `search_sessions` | Content search over past session logs | Reads `~/.sakthai/sessions/`, not the store |
| `forget` | Delete a fact by id | — |
| `read_file` | Read a local text file | Sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`; 20k-char cap |
| `run_command` | Run a CLI command (no shell) | **Opt-in** via `SAKTHAI_SHELL_ALLOW`; 20k-char cap, 120s max |
| `send_telegram_message` | Send a Telegram message | Needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| `send_outlook_mail` | Send mail via Microsoft Graph | Needs `MS_GRAPH_CLIENT_ID` + `MS_GRAPH_REFRESH_TOKEN` |
| `read_outlook_mail` | List recent inbox messages | Same Graph credentials |
| `list_calendar_events` | List upcoming calendar events | Same Graph credentials |
| `create_calendar_event` | Create a calendar event | Same Graph credentials |
| `run_agent_loop` | Delegate a whole task to SakThai's agent loop | MCP-only (filtered out of the in-loop tool set to avoid recursion) |
| `family_recall` | Recall across every persona's memory shard | Read-only `FamilyMemoryView` |
| `family_search` | Search across every persona's memory shard | Read-only `FamilyMemoryView` |
| `delegate_to_persona` | Run a subtask as another Sak Family persona, in-process | Persona name is enum-constrained |

## Memory operations

`sakthai memory …` and the store API behind them:

- `show` / `stats` — list entries; aggregate counts, kinds, tags, time ranges.
- `search` — substring search (LIKE wildcards are escaped).
- `forget` / `forget-obs` — delete by id.
- `export` / `import` — portable JSON snapshot (also CSV / JSONL export).
- `backup` — timestamped copy of `memory.db`.
- `healthcheck` — SQLite `integrity_check`.
- `consolidate` — fold facts older than N seconds into one observation.
- `consolidate-sessions` — mine local session logs through an LLM and learn durable facts about the user (idempotent across runs).
- `deduplicate` — drop duplicate facts/observations (keyed and key-less).
- `family` — merged read-only view across every persona's shard (`--personas a,b,c`).
- `sync` / `pull` — git-backed JSONL export/import and HTTP backup. Both always
  target the unscoped `memory.db` and reject `--persona`.

All of these except `sync`/`pull` accept a group-level `--persona <name>` to act
on that persona's own shard at `~/.sakthai/<persona>/memory.db`.

## Providers

`run_agent` supports four providers, auto-detected from the model name and
available credentials (override with `--provider`):

- **anthropic** — Claude via the `anthropic` SDK (default model `claude-opus-4-8`).
- **google** — Gemini via `google-genai`.
- **openai** — any OpenAI-compatible gateway via `httpx` (`OPENAI_API_BASE` /
  `OPENAI_BASE_URL` + `OPENAI_API_KEY`).
- **ollama** — local models via Ollama (`OLLAMA_HOST`, default
  `http://127.0.0.1:11434`); no API key, **no cost**.

All are normalised to one response shape, so the loop logic is provider-agnostic.

## Sessions

Each `run_agent` call writes a JSON session log to `~/.sakthai/sessions/`
(task, model, messages, and the result with tool calls).

## Dashboard

There is **no `sakthai dashboard` command** — the CLI wiring and the in-package
frontend were both removed. What remains is `dashboard/data.py`, a KPI/lead/
revenue snapshot built from the memory store, served over HTTP by
`web/server.py` alongside the other API endpoints:

| Endpoint | Payload |
|---|---|
| `/health` | liveness; the only unauthenticated path |
| `/api/stages` | the `dashboard/data.py` snapshot |
| `/api/ecosystem` | ecosystem status |
| `/api/personas` · `/api/metrics` · `/api/sessions` · `/api/memory` · `/api/audit` · `/api/workflows` | the dashboard payloads built by `web/api.py`, shaped by `web/contracts.py` |

Every path except `/health` requires the bearer token from `sakthai web setup`.
The frontend that consumes these lives at `apps/sak_agent_dashboard/` (Next.js).

## Unified Agent Platform

The `sakthai.agent_platform` subsystem unifies advanced agent engineering and enterprise orchestration capabilities:

- **Accidental Data Loss Guardrails (`safety.py`)**: Real-time evaluation of destructive shell commands (`rm -rf`, `gsutil rm`, `bq rm`, `git reset --hard`, `git clean -f`) and raw SQL mutations (`DROP`, `TRUNCATE`, unconstrained `DELETE`) with HMAC-based authorization tokens.
- **Reactive Python Dependency Detection (`dep_manager.py`)**: Environment introspection adhering to a strict hierarchy (`uv` → `poetry` → `pipenv` → `conda` → `venv+pip`), preventing global package pollution.
- **Progressive Disclosure Customizations (`customizations.py`)**: Hierarchical instruction resolution (`AGENTS.md`, `GEMINI.md`, `.rules.md`) and lightweight frontmatter indexing for skills to minimize context usage.
- **Jules Task Delegation (`jules_worker.py`)**: GitHub remote resolution, asynchronous patch planning, and delegation session formatting.
- **Dual Agent Core Engine (`agent_engine.py`)**: Abstraction layer unifying Google Antigravity SDK (`LocalAgentConfig` / LiteRT) and Google ADK execution models with built-in safety interception.
- **Harness AI Agent Spec Exporter (`harness_exporter.py`)**: Deterministic canonical identifier generation (`ca_<slug>`) and declarative Harness v1 agent template and pipeline step export.


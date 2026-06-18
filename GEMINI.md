# SakThai Agent v2 — Project Context

Guidance for the Gemini CLI and Gemini-backed agents working in this repository.

## What this is

`sakthai-agent` **v2.0**: a personal learning agent with persistent SQLite
memory, a shared tool registry, a Claude/Gemini agent loop, and an MCP stdio
server. It is a **clean-room rewrite** of the original `SakThai-Agent` ("OG").
Treat the OG as a **read-only blueprint** — study it for intent, never copy its
code or layout. The OG's Google ADK / Vertex AI cloud agent is **not** part of
v2: there is no `app/` bundle, no cloud-sync step, and no cloud runtime here.

## Gemini runtime

Gemini is a first-class provider, not a bolt-on:

- `run_agent` auto-detects the provider from the model name and available
  credentials; force it with `--provider google`.
- Google auth uses the **Gemini CLI OAuth token** (resolved in `auth.py`); set
  `GOOGLE_*` env vars only if you route through your own project.
- `sakthai mcp` exposes the memory tools over MCP stdio, so the Gemini CLI can
  share the same `~/.sakthai/memory.db` as every other runtime.

## Getting started

```bash
cp .env.example .env            # ANTHROPIC_API_KEY for Claude; Gemini uses CLI OAuth
pip install -e ".[all]"         # dev + dashboard extras (Python >=3.11)
sakthai setup                   # validate .env and required env vars
sakthai doctor                  # report environment + memory health
```

## Common commands

| Task | Command |
|------|---------|
| Run the agent | `sakthai run "your task" --provider google\|openai\|ollama` |
| Save a fact | `sakthai learn "fact" (--kind --key --tag)` |
| Search memory | `sakthai recall "query"` / `sakthai memory search` |
| Inspect memory | `sakthai memory show` / `sakthai memory stats` |
| Serve MCP | `sakthai mcp` |
| The 6-stage cycle | `sakthai cycle status\|next\|set\|list` |
| Skills | `sakthai skills list\|show\|validate` |
| Dashboard | `sakthai dashboard` (`--export data.json` skips the UI) |
| Test | `python -m pytest tests/ -q` |
| Lint / format / types | `ruff check sakthai tests` · `ruff format --check sakthai tests` · `mypy sakthai` |

## How it fits together

One layered package; data flows CLI/MCP → agent loop → shared tool registry
(`agent/tools.py`) → `MemoryStore` (the only SQLite-touching code) → SQLite at
`~/.sakthai/memory.db`. The MCP server and the agent loop share that one tool
registry, so a tool added once is available to both. `config.py` owns every
path; the six-stage Dream → Growth cycle is persisted as a single fact. Full
detail: [`docs/architecture.md`](docs/architecture.md) and
[`docs/capabilities.md`](docs/capabilities.md).

## Conventions

- **Go through the seams.** SQLite access → `MemoryStore`; agent/MCP-visible
  actions → `agent/tools.py`. Don't bypass them.
- **Surgical edits.** Change only what the task needs; preserve surrounding
  style and formatting.
- **Hermetic tests.** The suite runs with no network and no GCP credentials —
  keep it that way (inject clients/stores).
- **Validate before proposing changes.** Run `ruff`, `mypy sakthai`, `bandit`,
  and `pytest`; CI gates `main` on Python 3.11 and 3.12.
- **Respect the sandbox.** `read_file` is limited to cwd + `~/.sakthai` +
  `SAKTHAI_READ_ALLOW`; `run_command` is opt-in via `SAKTHAI_SHELL_ALLOW`.
- **Persist learnings.** Use `sakthai learn` for durable user preferences and
  decisions; `recall` before starting related work.

## Key environment variables

- `ANTHROPIC_API_KEY` — Claude auth for `sakthai run` / `mcp` (Gemini uses CLI OAuth).
- `SAKTHAI_HOME` — override the `~/.sakthai` root (memory db, sessions, extensions).
- `SAKTHAI_READ_ALLOW` / `SAKTHAI_SHELL_ALLOW` — widen `read_file` paths / enable `run_command`.
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — for the `send_telegram_message` tool.
- `OLLAMA_HOST` — local Ollama server address (defaults to `http://localhost:11434`).
- `OPENAI_API_BASE` / `OPENAI_BASE_URL` — target gateway URL for OpenAI-compatible models.
- `OPENAI_API_KEY` — key required by the OpenAI-compatible gateway (defaults to `nokey`).

# Sak-Family-Agent — Project Context

Guidance for the Gemini CLI and Gemini-backed agents working in this repository.

## What this is

`sakthai-agent` **v2.0**: A personal learning agent ecosystem (persistent SQLite, shared tool
registry, Claude/Gemini/OpenAI/Ollama agent loop, MCP stdio server) with a
multi-persona family of AI agents — the Sak Family.

**Clean-room rewrite** of "OG" SakThai-Agent. OG is a **read-only blueprint** (study intent,
do not copy code/layout).
No Google ADK/Vertex AI cloud agent, no `app/` bundle, no cloud-sync, no cloud runtime.

## Repository layout

```
Sak-Family-Agent/
├── sakthai/                 # Core Python package
│   ├── agent/               #   Agent loop + providers (anthropic, gemini, openai)
│   ├── cli/                 #   Click CLI (learn, recall, run, mcp, cycle, …)
│   ├── memory/              #   MemoryStore (SQLite, WAL mode)
│   ├── mcp/                 #   JSON-RPC 2.0 stdio MCP server + outbound client
│   ├── cycle/               #   6-stage Dream → Growth state machine
│   ├── dashboard/           #   Streamlit data layer + app
│   ├── extensions/          #   Clone skill/MCP bundles from git
│   ├── lead/                #   Customer lead capture (ServiceQuoteBot)
│   ├── learn/               #   Explicit fact-write path
│   ├── telegram/            #   Telegram bot integration
│   ├── web/                 #   Embedded web server
│   ├── auth.py              #   Credential resolution (Anthropic, Google, OpenAI)
│   ├── config.py            #   Single source of truth for paths & env vars
│   ├── hf.py                #   Hugging Face Hub operations (info, download)
│   ├── sakking_skills.py    #   Import SakKing learned skills into skills/
│   ├── sandbox.py           #   read_file / run_command sandboxing
│   └── skills.py            #   SKILL.md parsing, catalog, validation
├── personas/                # 7 persona overlays (sakthai, sakking, saksee, …)
├── skills/                  # 70+ bundled and learned skills
├── docs/                    # Architecture, capabilities, integrations, runtimes
├── dashboard/               # Vite + Tailwind standalone web dashboard
├── product/                 # Business strategy, monetization, MVP plans
├── infra/                   # hermes-agents deployment, pw-poc, training space
├── packages/                # agent-self-evolution (separate dependency set)
├── services/                # HuggingFace dataset publishing
├── training/                # HF jobs, model serving configs
├── scripts/                 # compose_persona.py, export_agent_repo.py, etc.
├── tests/                   # Hermetic pytest suite (≥85% coverage)
├── library/                 # Reference corpus
├── assets/                  # Images and branding
└── scratch/                 # Orphan / temp files
```

## Gemini runtime

- Auto-detects provider; force via `--provider google`.
- Google auth: `GEMINI_API_KEY` / `GOOGLE_API_KEY` env var, **or** the Gemini CLI
  OAuth token (`~/.gemini/oauth_creds.json`).
- `sakthai mcp` exposes memory over stdio, sharing `~/.sakthai/memory.db`.

## Getting started

```bash
cp .env.example .env      # ANTHROPIC_API_KEY for Claude; Gemini uses env var or CLI OAuth
uv sync --all-extras      # install all dependencies (Python >=3.11)
uv run sakthai setup      # validate .env and required env vars
uv run sakthai doctor     # report environment + memory health
```

## Common commands

| Task | Command |
|------|---------|
| Run the agent | `sakthai run "your task" --provider google\|openai\|ollama` |
| Run (fast, skip cycle) | `sakthai run "task" --fast` |
| Run (caveman mode) | `sakthai run "task" --caveman lite\|full\|ultra` |
| Save a fact | `sakthai learn "fact" (--kind --key --tag)` |
| Search memory | `sakthai recall "query"` / `sakthai memory search` |
| Inspect memory | `sakthai memory show` / `sakthai memory stats` |
| Serve MCP | `sakthai mcp` |
| The 6-stage cycle | `sakthai cycle status\|next\|set\|list` |
| Skills | `sakthai skills list\|show\|validate` |
| Sessions | `sakthai sessions list\|show\|prune` |
| Extensions | `sakthai extensions install\|list` |
| HuggingFace Hub | `sakthai hf info\|download <repo_id>` |
| Dashboard (Streamlit) | `sakthai dashboard` (`--export data.json` skips the UI) |
| System info | `sakthai status` / `sakthai tools` |
| Test | `uv run pytest tests/ -q` |
| Lint / format / types | `ruff check sakthai tests` · `ruff format --check sakthai tests` · `mypy sakthai` |
| Security scan | `uv run bandit -c pyproject.toml -r sakthai` |
| Mutation testing | `make mutation` (local-only, slow) |
| Compose personas | `make compose-personas` |
| Export agent repos | `make export-agent-repos` |
| Deploy runtime | `make deploy-runtime` |

## How it fits together

Data flow: CLI/MCP → agent loop → shared tool registry (`agent/tools.py`) →
`MemoryStore` → SQLite (`~/.sakthai/memory.db`).

One shared tool registry. `config.py` owns paths. 6-stage Dream→Growth cycle is persisted
as a single fact. Providers (Anthropic, Gemini, OpenAI/Ollama) live in
`agent/providers/` and are selected at runtime.

The **Sak Family** (6 personas + ServiceQuoteBot) share the core package but
each has a persona overlay in `personas/` with its own `SOUL.md`, skills, and
`CLAUDE.md`. `make compose-personas` merges shared + overlay skills;
`make export-agent-repos` materializes standalone repo snapshots.

Details: [`docs/architecture.md`](docs/architecture.md),
[`docs/capabilities.md`](docs/capabilities.md),
[`docs/runtimes.md`](docs/runtimes.md),
[`docs/integrations.md`](docs/integrations.md).

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
- **Plan first.** Always read and update `PLAN.md` before starting work. Mark
  tasks in-progress → done with date.
- **No duplication.** One source of truth per topic — link, don't copy.

## Key environment variables

- `ANTHROPIC_API_KEY` — Claude auth for `sakthai run` / `mcp`.
- `ANTHROPIC_AUTH_TOKEN` — Bearer token alternative to `ANTHROPIC_API_KEY`.
- `GEMINI_API_KEY` / `GOOGLE_API_KEY` — Gemini provider API key (alternative to CLI OAuth).
- `GEMINI_HOME` — override the `~/.gemini` root for OAuth token lookup.
- `SAKTHAI_HOME` — override the `~/.sakthai` root (memory db, sessions, extensions).
- `SAKTHAI_READ_ALLOW` / `SAKTHAI_SHELL_ALLOW` — widen `read_file` paths / enable `run_command`.
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — for the `send_telegram_message` tool.
- `OLLAMA_HOST` — local Ollama server address (defaults to `http://localhost:11434`).
- `OPENAI_API_BASE` / `OPENAI_BASE_URL` — target gateway URL for OpenAI-compatible models.
- `OPENAI_API_KEY` — key required by the OpenAI-compatible gateway (defaults to `nokey`).
- `HF_TOKEN` — Hugging Face Hub auth token for `sakthai hf` commands.
- `CLAUDE_CONFIG_DIR` — override the `~/.claude` root for Claude CLI token lookup.

# SakThai — a personal learning agent (chat CLI)

SakThai (`@sakthai_agent_bot`) is a personal, tool-using AI agent with
**persistent memory**. It runs entirely from the terminal: an interactive chat
REPL, a one-shot task runner, and an MCP server — all sharing the same memory
and the same set of tools. It is provider-agnostic (Anthropic, Google Gemini,
any OpenAI-compatible endpoint, or a local model via Ollama) and defaults to a
fine-tuned SakThai model you can serve locally, for free and offline.

> 📖 **Why this exists — [read the story](STORY.md).** SakThai and the Sak
> Family began as Beer's fresh start: six companions, each carrying one of six
> values — Dream, Hope, Care, Joy, Trust, and Growth. This repo is the
> standalone home for the SakThai companion.

## What it is

- **A chat companion with memory.** Unlike a stateless chatbot, SakThai keeps a
  persistent SQLite memory at `~/.sakthai/memory.db`, so facts you teach it and
  observations it records carry across sessions.
- **A tool-using agent.** It can read files, run commands (opt-in), capture and
  recall facts, ingest documents into memory, and more — the same tools are
  available whether you chat, run a one-shot task, or drive it over MCP.
- **Provider-agnostic.** Point it at Claude, Gemini, an OpenAI-compatible
  gateway, or a local Ollama model with a single flag.
- **Its own fine-tuned model.** The default backend is the fine-tuned
  `sakthai` model, served locally by Ollama — no API key, no network.

## Who it's for

- **Beer (Nanthasit Burankum)** — SakThai is first and foremost Beer's personal
  learning agent and supportive companion. If you are changing agent identity,
  support posture, or memory rules, read [`USER.md`](USER.md) first.
- **Anyone who wants a private, local-first AI agent** with durable memory and a
  clean terminal UI — no cloud account required if you run the local model.
- **Developers** who want a small, hackable, provider-agnostic agent loop and
  MCP server to build on.

## Why this repo exists

This is the trimmed, standalone home for the SakThai chat CLI — the core agent
package plus SakThai's persona overlay. It exists so the companion can be
installed and run on its own, with the Hugging Face weights as the durable
backup of the trained model. Non-chat pieces (web dashboard, media assets,
workspace docs) intentionally live in the `beer-sakthai/Sak-Family-Agent`
monorepo, not here.

## Install

Requires **Python 3.11+**. [`uv`](https://docs.astral.sh/uv/) is recommended
but `pip` works too.

```bash
# clone, then from the repo root:
uv venv && uv pip install -e ".[dev]"     # or: pip install -e ".[dev]"
sakthai --help                             # verify the install
sakthai doctor                             # check environment, paths, credentials
```

## Quick start

```bash
sakthai chat          # interactive REPL (persona "sakthai")
```

`sakthai chat` opens a full-screen terminal UI — a welcome card, boxed input,
per-turn status bar, and streaming replies. Type `/exit` or press `Ctrl+D` to
leave; `Ctrl+C` cancels a reply in progress. In-REPL slash commands:

| command | what it does |
|---|---|
| `/help` | list the commands |
| `/tools` | show the tools the agent can call |
| `/skills` | show available skills |
| `/memory` | show recent facts in memory |
| `/goal <text>` | pin a session goal that steers replies (`/goal` alone clears it) |
| `/clear` | clear the screen and conversation history |
| `/exit` | end the session |

Continuity across sessions comes from persistent memory in `~/.sakthai`
(override the data dir with `SAKTHAI_HOME`).

## What it can do — commands

Run `sakthai <command> --help` for details on any of these.

| command | purpose |
|---|---|
| `chat` | interactive multi-turn chat REPL with a Sak Family persona |
| `run "TASK"` | run a one-shot task through the agent loop |
| `mcp` | serve the memory + tools over MCP (stdio JSON-RPC) for other agents |
| `learn "…"` | add a fact (or a file of facts) to persistent memory |
| `recall "QUERY"` | recall facts and observations matching a query |
| `memory` | inspect and manage persistent memory |
| `skills` | discover and inspect skills |
| `tools` | list the built-in agent/MCP tools |
| `sessions` | manage past agent sessions |
| `cycle` | track and advance the 6-stage Dream → Growth cycle |
| `hf` | Hugging Face Hub operations |
| `extensions` | install and manage SakThai extensions from git |
| `eval` | inspect local-model evaluation / MLOps metrics |
| `doctor` / `status` / `setup` | check environment, paths, memory, and credentials |

**Built-in agent tools** (available in `chat`, `run`, and over `mcp`): `learn`,
`recall`, `search`, `forget`, `ingest_document`, `capture_lead`, `read_file`,
`run_command`, `send_telegram_message`, `run_agent_loop`. `read_file` is
sandboxed to the current directory + `~/.sakthai` (extend with
`SAKTHAI_READ_ALLOW`); `run_command` is disabled unless `SAKTHAI_SHELL_ALLOW`
is set.

## Choosing a model / backend

`sakthai chat` defaults to the fine-tuned **`sakthai`** model served locally by
Ollama. The trained weights live on Hugging Face as **merged** models (ready to
serve, no adapter merge needed):

- [`Nanthasit/sakthai-context-1.5b-merged`](https://hf.co/Nanthasit/sakthai-context-1.5b-merged) — better quality
- [`Nanthasit/sakthai-context-0.5b-merged`](https://hf.co/Nanthasit/sakthai-context-0.5b-merged) — lighter, for low-RAM machines

**A) Local via Ollama (offline, free — the default).** Build the `sakthai`
Ollama model from the Hub, then just `sakthai chat`. The merged repos ship a
prebuilt quantized GGUF, so setup is a single ~1 GB download — no torch or
llama.cpp needed:

```bash
scripts/setup_local_model.sh              # 1.5B (default); or: setup_local_model.sh 0.5b
export OLLAMA_HOST=http://127.0.0.1:11434
sakthai chat
```

**B) Cloud via the Hugging Face router (no local resources).**

```bash
export OPENAI_BASE_URL=https://router.huggingface.co/v1
export OPENAI_API_KEY=hf_xxx              # free token: https://huggingface.co/settings/tokens
sakthai chat --provider openai --model Nanthasit/sakthai-context-1.5b-merged
```

**C) Any other provider** via flags:

```bash
sakthai chat --provider anthropic --model claude-opus-4-8   # needs ANTHROPIC_API_KEY
sakthai chat --provider google                              # needs GEMINI_API_KEY
```

Export the relevant API keys in your shell — the CLI reads them from the
environment (a `.env` file is **not** loaded automatically). `sakthai doctor`
reports which credentials it can see.

> Ollama networking tip: use `http://127.0.0.1:11434`, not `localhost`, to avoid
> IPv6 resolution issues.

## Architecture (one package, three ways in)

```
CLI / MCP  →  run_agent (agent loop)  →  ToolRegistry  →  BUILTIN_TOOLS  →  MemoryStore  →  SQLite (~/.sakthai/memory.db)
```

- **`sakthai chat`** — interactive REPL (`sakthai/agent/chat.py`, `ui.py`)
- **`sakthai run "task"`** — one-shot agent loop (`sakthai/agent/loop.py`)
- **`sakthai mcp`** — inbound MCP stdio server (`sakthai/mcp/server.py`)

All three share the same tool registry and the same `MemoryStore` seam, so a
tool added once appears everywhere. Providers (Anthropic / Gemini /
OpenAI-compatible) live behind a normalized boundary in
`sakthai/agent/providers/`.

## Layout

- `sakthai/` — core agent package: memory, tools, agent loop, providers, MCP server, CLI
- `library/` — the shared skill library (`SKILL.md` files rendered into the system prompt)
- `personas/shared/skills/` — shared skills used by this persona
- `personas/sakthai/` — persona SOUL, config, overlay skills, and the `agent-self-evolution` package
- `scripts/` — helpers, incl. `setup_local_model.sh` (build the local model)
- `tests/` — hermetic unit tests
- `data/` — sample memory snapshot
- `.claude/skills/run-sakthai-chat-cli/` — offline smoke/driver for agents

## Development

```bash
uv sync --all-extras                     # install deps from uv.lock
python -m pytest tests/ -q               # full hermetic test suite
ruff check sakthai tests                 # lint
ruff format --check sakthai tests        # formatting
mypy sakthai                             # strict type checking
bandit -c pyproject.toml -r sakthai      # security lint
```

Tests are hermetic (no network, no credentials); coverage floor is 85% with
branch coverage. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the quality bar
and [`CLAUDE.md`](CLAUDE.md) for architecture and conventions.

To launch and drive the app from a clean machine (or verify a change without
credentials), use the bundled driver:

```bash
python3 .claude/skills/run-sakthai-chat-cli/driver.py smoke   # 7-step offline verification
```

## Repository boundary

SakThai works only in `beer-sakthai/sakthai-chat-cli` and
`beer-sakthai/Sak-Family-Agent`. Do not read from, write to, or administer any
other GitHub repository unless Beer explicitly grants a one-off exception.

## License & contributing

This is a personal project; suggestions are welcome. See
[`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md),
and [`SECURITY.md`](SECURITY.md).

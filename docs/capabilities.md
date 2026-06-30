# Capabilities

## Tools

These are exposed both to the agent loop (`sakthai run`) and over MCP
(`sakthai mcp`). The registry lives in `sakthai/agent/tools.py`.

| Tool | What it does | Notes |
|------|--------------|-------|
| `learn` | Save a fact (value, kind, key) | The agent's write path into memory |
| `recall` | List recent facts + top observations | Read what's already known |
| `search` | Substring search over facts + observations | Targeted lookup |
| `forget` | Delete a fact by id | — |
| `read_file` | Read a local text file | Sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`; 20k-char cap |
| `run_command` | Run a CLI command (no shell) | **Opt-in** via `SAKTHAI_SHELL_ALLOW`; 20k-char cap, 120s max |
| `send_telegram_message` | Send a Telegram message | Needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| `run_agent_loop` | Delegate a whole task to SakThai's agent loop | MCP-only (filtered out of the in-loop tool set to avoid recursion) |

## Memory operations

`sakthai memory …` and the store API behind them:

- `show` / `stats` — list entries; aggregate counts, kinds, tags, time ranges.
- `search` — substring search (wildcards are treated literally).
- `forget` / `forget-obs` — delete by id.
- `export` / `import` — portable JSON snapshot (also CSV / JSONL export).
- `backup` — timestamped copy of `memory.db`.
- `healthcheck` — SQLite `integrity_check`.
- `consolidate` — fold facts older than N seconds into one observation.
- `consolidate-sessions` — mine local session logs through an LLM and learn durable facts about the user (idempotent across runs).
- `deduplicate` — drop duplicate facts/observations (keyed and key-less).

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

`sakthai dashboard` serves a Streamlit view of the store; `--export <file>.json`
writes the same snapshot as JSON without needing Streamlit (handy for feeding an
external front-end or other tooling).

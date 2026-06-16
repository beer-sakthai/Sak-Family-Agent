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

## Memory operations

`sakthai memory …` and the store API behind them:

- `show` / `stats` — list entries; aggregate counts, kinds, tags, time ranges.
- `search` — substring search (LIKE wildcards are escaped).
- `forget` / `forget-obs` — delete by id.
- `export` / `import` — portable JSON snapshot (also CSV / JSONL export).
- `backup` — timestamped copy of `memory.db`.
- `healthcheck` — SQLite `integrity_check`.
- `consolidate` — fold facts older than N seconds into one observation.
- `deduplicate` — drop duplicate facts/observations (keyed and key-less).

## Providers

`run_agent` supports two providers, auto-detected from the model name and
available credentials (override with `--provider`):

- **anthropic** — Claude via the `anthropic` SDK (default model `claude-opus-4-8`).
- **google** — Gemini via `google-genai`.

Both are normalised to one response shape, so the loop logic is provider-agnostic.

## Sessions

Each `run_agent` call writes a JSON session log to `~/.sakthai/sessions/`
(task, model, messages, and the result with tool calls).

## Dashboard

`sakthai dashboard` serves a Streamlit view of the store; `--export <file>.json`
writes the same snapshot as JSON without needing Streamlit (handy for feeding an
external front-end or other tooling).

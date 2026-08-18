# GEMINI.md

Context file for **Gemini CLI** working in the Sak-Family-Agent monorepo.

This file is deliberately thin. The repository already keeps one set of
instructions for coding agents, and duplicating them here would guarantee they
drift. Gemini CLI's `@` import syntax pulls them in verbatim instead — edit the
imported files, never a copy.

## Imported instructions

@./AGENTS.md

@./CLAUDE.md

@./docs/OPERATING_CONTRACT.md

## Gemini-CLI-specific notes

Everything above applies as written. These are the few things that are true for
Gemini CLI and not for the other agents:

- **The package is not at the repo root.** `import sakthai` resolves to
  `personas/sakthai/sakthai/` via the editable install. Run `uv sync --all-extras`
  before anything else, and prefer `uv run <cmd>` over a bare `python`.
- **Shell is approval-gated, not free.** `.gemini/settings.json` leaves
  `general.defaultApprovalMode` at `default`, so `run_shell_command` asks before
  it runs. Do not switch the project setting to `yolo` to get past a prompt.
- **The repo's own MCP server is already wired.** `.gemini/settings.json`
  registers `sakthai` (the stdio server from `sakthai mcp`), which exposes the
  same 14 built-in tools the agent loop uses — memory (`learn`, `recall`,
  `search`, `forget`), `read_file`, `run_command`, and the Graph/Telegram tools.
  Reach for those before writing throwaway scripts against `memory.db`.
- **Do not edit `~/.sakthai/memory.db` directly.** Every SQLite access goes
  through `MemoryStore`; the MCP tools above are the supported path.
- **Guardrail edits must be synced across all six personas** or
  `tests/test_persona_guardrails_parity.py` fails CI. See the guardrails section
  of `CLAUDE.md` for the file list.

## Before you hand work back

Run the same gates CI runs (from `CLAUDE.md` → Commands):

```bash
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest tests/ -q
```

Coverage floor is 96% over the `sakthai` package, and green CI is the bar for
`main`.

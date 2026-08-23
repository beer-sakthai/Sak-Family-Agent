---
name: SakKing-sak-family-agent
description: ">-   Cheatsheet for developing in the Sak-Family-Agent monorepo. Covers persona   registration patterns, SOUL.md structure, lint gotchas, build commands, and   the 6-agent family architecture. Activate when working in /home/beern/Sak-Family-Agent."
---

# Sak-Family-Agent Developer Skill

## Repo Quick Facts
- **Core package**: `personas/sakthai/sakthai/` (NOT repo root — no root-level `sakthai/`)
- **Import resolution**: Package is editable-installed — standalone scripts need `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`
- **6 active personas**: sakking, sakthai, saksee, saksit, sakjules, saktan
- **Shared memory brain**: `~/.sakthai` — all personas read/write here

## Build & Verification Commands
```bash
uv sync --all-extras                                          # install full environment
make test                                                     # full pytest suite (~1,800 tests, ≥85% coverage target)
uv run ruff check <file>                                      # lint ONLY your changed files
uv run mypy personas/sakthai/sakthai                          # strict type checking
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai   # security scan
```

> ⚠️ Do NOT use `make lint` to verify your changes — it has 55 pre-existing Ruff
> errors in unrelated files and will always exit non-zero. Use
> `uv run ruff check <your-file>` instead.

## Adding a New Persona — 3 Required Locations

### 1. `personas/sakthai/sakthai/config.py` — register the name
```python
# The six Sak Family personas `sakthai chat --persona` can address.
PERSONA_NAMES: tuple[str, ...] = ("sakking", "sakthai", "saksee", "saksit", "sakjules", "saktan")
```

### 2. `personas/sakthai/sakthai/agent/chat.py` — label + color
```python
PERSONA_LABELS: dict[str, str] = {
    ...,
    "saktan": "SakTan",
}
PERSONA_COLORS: dict[str, str] = {
    ...,
    "saktan": "bright_blue",   # pick an unused rich color
}
```

### 3. `personas/<name>/SOUL.md` — identity file
Must contain these sections in this order:
1. `## We are one family — and becoming more` — shared family preamble
2. `## Identity` — full name, siblings list with handles, default model
3. `## Say who I am — every reply` — the one-line opener (e.g. `SakTan · Keeper of Operations & Daily Flow.`)
4. `## Character & Craft` — specialty, concrete repo surface, lane boundary (what they DON'T do)
5. `## Charge` — charge states table (Optimal 80-100% / Active 50-79% / Low 20-49% / Critical 0-19%)
6. `## Principles` — 4 numbered principles
7. `## Tone` — including token economy reminder

### .gitignore check
Before creating `personas/<name>/`, check `.gitignore` — removed personas may be explicitly ignored.
Remove the ignore rule first if needed.

### Quick verification after adding a persona:
```bash
uv run python -c "
from personas.sakthai.sakthai.config import PERSONA_NAMES
from personas.sakthai.sakthai.agent.chat import PERSONA_LABELS, PERSONA_COLORS
from pathlib import Path
name = 'saktan'
assert name in PERSONA_NAMES
assert name in PERSONA_LABELS
assert name in PERSONA_COLORS
assert Path(f'personas/{name}/SOUL.md').stat().st_size > 500
print('✅ All checks passed!')
"
```

## 6-Agent Family Roster

| Persona | Role | SOUL Opener | Terminal Color |
|---------|------|-------------|----------------|
| sakthai | Lead & ML/Code Orchestrator | `SakThai · Lead & ML/Code Orchestrator.` | cyan |
| sakjules | Automation & CI/CD Master | `SakJules · Master of Automation & CI/CD.` | bright_red |
| sakking | UI & Skill Rollup Master | per SOUL.md | bright_magenta |
| saksee | Live Web Automation Driver | per SOUL.md | green |
| saksit | Content Creation Specialist | per SOUL.md | yellow |
| saktan | Keeper of Operations & Daily Flow | `SakTan · Keeper of Operations & Daily Flow.` | bright_blue |

All personas share `~/.sakthai` memory and keep separate live sessions.

## Skill Overlay & Persona Export
```bash
# Materialise a persona's full composed skill tree
python scripts/compose_persona.py <name> --out /tmp/<name>-composed

# Export persona to a standalone repo
python scripts/export_agent_repo.py <name> --out build/agent-repos/<name>
```

## Commit Style
Conventional prefixes: `feat:`, `refactor:`, `fix:`, `docs:`, `test:`
PRs must include: short summary, motivation, and commands used to verify.

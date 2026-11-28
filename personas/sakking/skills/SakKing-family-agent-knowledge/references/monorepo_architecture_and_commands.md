# Sak Family Agent Monorepo Architecture & Commands Reference

This reference details the monorepo directory layout, core development commands, testing guidelines, and persona relationships for `Sak-Family-Agent`.

---

## 1. Quick Command Reference

| Command | Purpose |
|:---|:---|
| `uv sync --all-extras` | Install full local Python environment |
| `make test` | Run pytest suite across `tests/` |
| `make lint` | Run ruff formatting and lint checks |
| `uv run mypy personas/sakthai` | Strict type checking on core package |
| `uv run bandit -c pyproject.toml -r personas/sakthai` | Security scan on core package |
| `python3 scripts/diagnose_personas.py` | Full 6-persona end-to-end diagnostic check |
| `python3 scripts/sync_personas.py --check` | Verify byte-for-byte package parity across personas |
| `uv run sakthai eval audit` | 5-pillar evaluation audit across all personas |
| `uv run sakthai mcp list` | Inspect configured MCP servers |

---

## 2. Monorepo Directory Architecture

```
Sak-Family-Agent/
├── apps/sak_agent_dashboard/    # Next.js web dashboard & workflow engine
├── personas/                    # 6 distinct agent personas
│   ├── sakthai/                 # Lead & Hugging Face Master (canonical core)
│   ├── sakking/                 # General Assistant & Runner (Deputy 1)
│   ├── saktan/                  # Operations & Daily Flow (Deputy 2)
│   ├── saksee/                  # Web / Browser Specialist (Deputy 3)
│   ├── sakjules/                # GitHub, CI/CD & Automation Master
│   ├── saksit/                  # Social / Content Specialist
│   └── shared/                  # Shared skills and self-evolution
├── tests/                       # Pytest test suite (>=96% coverage floor)
├── scripts/                     # Operational & maintenance utilities
└── docs/                        # Architecture, user profiles, security docs
```

---

## 3. Persona Topology & Specialization Matrix

1. **SakThai**: Lead authority on model lifecycle, Hugging Face Hub, PEFT/LoRA, dataset management.
2. **SakKing**: First Deputy; fast CLI execution, TDD runner, multi-agent dispatch, emergency Hub proxy.
3. **SakTan**: Second Deputy; daily briefings, ops daemon, local Ollama execution, rate-limit tally.
4. **SakSee**: Third Deputy; web scraping, Playwright automation, Chrome DevTools, Web Sentinel.
5. **SakJules**: CI/CD automation master, GitHub workflows, release orchestration, PR gatekeeper.
6. **SakSit**: Social media broadcasting, brand storytelling, editorial evaluation, media presets.

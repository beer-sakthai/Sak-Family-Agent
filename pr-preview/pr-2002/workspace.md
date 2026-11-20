# House of Sak Workspace Layout & Developer Guide

This document describes the repository layout, development toolchain, testing setup, and MCP details for the `Sak-Family-Agent` monorepo.

---

## 📂 Repository Layout

The monorepo contains the following primary directories:

| Path | Description |
| :--- | :--- |
| `personas/sakthai/` | Core Python package source (`sakthai`), installed editably (agent, cli, cycle, memory, mcp, team, web) |
| `personas/<name>/` | Persona overlays, identity (`SOUL.md`), skills, evolution, and configurations |
| `personas/shared/skills/` | Universal shared skills available across all six personas (19 skills) |
| `apps/sak_agent_dashboard/` | Unified Next.js 15+ dashboard embedding the durable workflow engine (`workflow_engine/`) |
| `tests/` | Comprehensive pytest suite (3,086 unit tests across Python 3.11 & 3.12, $\ge 96\%$ coverage) |
| `docs/` | Architecture, operations, security policies, wiki hub, and formal Superpowers specifications |
| `scripts/` | Development, maintenance, and synchronization tooling |
| `infra/` | Deployment runbooks, VM systemd agents, and container sandboxes |
| `services/` | ServiceQuoteBot, inference gateways, and external integrations |
| `training/` | Fine-tuning recipes, LoRA configurations, and dataset publishing scripts |

Standalone persona repository snapshots can be exported via `make export-agent-repos` or `python scripts/export_agent_repo.py <persona> --out <dir>`.

---

## ⚡ Development & Testing Commands

House of Sak uses `uv` for fast, deterministic Python environment management:

```bash
# Install full local Python environment with all optional dependencies
uv sync --all-extras

# Run full pytest suite (enforces >=96% coverage floor)
make test

# Run Ruff linter and formatter checks
make lint

# Run strict static type checking on the core package
uv run mypy personas/sakthai

# Run security vulnerability scan
uv run bandit -c pyproject.toml -r personas/sakthai

# Run offline persona diagnostic
uv run python scripts/diagnose_personas.py
```

---

## 🔌 Configured MCP Servers

MCP configurations are stored in `~/.sakthai/mcp.json` (or persona configs under `personas/<name>/config/mcp.json`). External stdio servers and remote HTTP/SSE endpoints can be registered there or dynamically loaded from extension directories (`~/.sakthai/extensions/`).

During runtime, tools are automatically discovered, filtered against configured `tools` allowlists, and prefixed with `<server_name>__` to prevent namespace collisions.

Developers can inspect, probe, and list MCP tools using:
```bash
sakthai mcp list [--persona <name>] [--json]
sakthai mcp ping [<server_name>] [--persona <name>]
sakthai mcp tools [--persona <name>]
```

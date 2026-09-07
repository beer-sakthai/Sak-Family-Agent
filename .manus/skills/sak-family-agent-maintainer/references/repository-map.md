# Sak-Family-Agent Repository Map

Use this reference after reading the root `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, and component-local guidance.

| Area | Location | Primary responsibility |
|---|---|---|
| Core runtime | `personas/sakthai/sakthai/` | Agent loop, providers, memory, MCP, CLI, web API, tools, guardrails, and sandboxing. |
| Personas | `personas/{sakthai,saksee,sakjules,sakking,saksit,saktan}/` | Persona-specific configuration, skills, memory overlays, and self-evolution material. |
| Shared knowledge | `personas/shared/`, `library/` | Shared skill pools and curated reusable skills. |
| Python tests | `tests/` | Runtime, CLI, memory, security, integration, and tooling tests. |
| Dashboard | `apps/sak_agent_dashboard/` | Next-based dashboard and Vitest/ESLint checks. Read its `package.json` and lockfile. |
| Training | `training/` | Dataset preparation, LoRA jobs, evaluation, and serving-adjacent training assets. |
| Services and infrastructure | `services/`, `infra/` | Endpoints, deployment, VM agents, and operational configuration. |
| Documentation | `docs/`, component `README.md` files | Architecture, audits, plans, security, operations, and feature documentation. |
| Automation | `.github/workflows/` | CI, secret scanning, CodeQL, Bandit, OSSAR, dependency audits, evaluations, and maintenance. |

## Canonical Python commands

Read `Makefile` and `pyproject.toml` before running broad commands. The core baseline commonly includes:

```bash
uv sync --all-extras
make test
make lint
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
```

The CI workflow runs Ruff checks/format verification, strict mypy, Bandit, and pytest with an explicit coverage floor. Do not infer the current test count or coverage from this reference; obtain fresh results.

## Canonical dashboard commands

Run from `apps/sak_agent_dashboard/` using the package manager declared by the repository metadata:

```bash
npm ci
npm test
npm run lint
npm run build
```

If dependencies require a newer Node version than the sandbox provides, report the limitation and use the GitHub checks as the authoritative remote verification.

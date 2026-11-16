# House of Sak — Sak Family Agent

<p align="center">
  <img src="docs/images/house-of-sak-hero.jpg" alt="House of Sak — Sak Family Agent Command Center: Six companion robots collaborating in a high-tech minimalist environment" width="100%">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/banner-dark.svg">
    <img alt="House of Sak — Sak Family Agent Banner" src="docs/images/banner-light.svg" width="100%">
  </picture>
</p>

---

## ⚡ System Status Bar

<p align="center">
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml?query=branch%3Amain"><img alt="CI" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/apps.yml?query=branch%3Amain"><img alt="Apps" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/apps.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml?query=branch%3Amain"><img alt="Sub-project tests" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml?query=branch%3Amain"><img alt="Pylint" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml/badge.svg?branch=main"></a>
  <a href=".github/workflows/ci.yml"><img alt="Coverage: at least 96%, enforced in CI" src="https://img.shields.io/badge/coverage-%E2%89%A596%25%20enforced-16A34A"></a>
  <br>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/repository-security-quality.yml?query=branch%3Amain"><img alt="Security and quality" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/repository-security-quality.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/codeql.yml?query=branch%3Amain"><img alt="CodeQL" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/codeql.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml?query=branch%3Amain"><img alt="Secret Scan" src="https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml/badge.svg?branch=main"></a>
  <a href="https://securityscorecards.dev/viewer/?uri=github.com/beer-sakthai/Sak-Family-Agent"><img alt="OpenSSF Scorecard" src="https://api.securityscorecards.dev/projects/github.com/beer-sakthai/Sak-Family-Agent/badge"></a>
  <br>
  <img alt="Version 2.0.0" src="https://img.shields.io/badge/version-2.0.0-2563EB">
  <img alt="Python 3.11 | 3.12" src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB?logo=python&amp;logoColor=white">
  <img alt="6 personas" src="https://img.shields.io/badge/personas-6-7C3AED">
  <img alt="480 skills" src="https://img.shields.io/badge/skills-480-10B981">
  <a href="LICENSE"><img alt="License: custom IP license" src="https://img.shields.io/badge/license-custom%20IP%20license-4B5563"></a>
</p>

| Subsystem | Scope / Target | Live Status | Architectural Invariant |
| :--- | :--- | :---: | :--- |
| **Core Loop** | Local-first tool loop (`agent/loop.py`) | `🟢 ACTIVE` | Provider-agnostic retries, preflight & streaming |
| **Personas** | 6 Family Agents (`personas/<name>/`) | `🟢 6/6 ONLINE` | `SakThai` · `SakSee` · `SakJules` · `SakKing` · `SakSit` · `SakTan` |
| **Skills Catalog** | 480 On-Disk Skills (461 overlay + 19 shared) | `🟢 STANDARDIZED`| Structured `Sak<Agent>-<domain>-<topic>` taxonomy |
| **Memory Store** | SQLite per Persona (`~/.sakthai/`) | `🟢 SYNCED` | Sharded persistence & multi-agent `sakthai memory family` |
| **Test Quality** | 2,811 Unit Tests across Python 3.11 & 3.12 | `🟢 PASS (≥96%)` | Enforced strict coverage floor (`--cov-fail-under=96`) |
| **Security Gates** | Guardrails, Secret Scan, CodeQL & Bandit | `🛡️ ENFORCED` | Safe execution, credential isolation & automated scanning |

> **Six personas, one shared runtime.**
> House of Sak is a local-first, provider-agnostic AI agent workspace combining a durable SQLite memory store, an extensible tool loop, Model Context Protocol (MCP) support, persona-specific skills, multi-agent coordination, and an interactive Next.js dashboard.
> The ecosystem revolves around the six-stage growth cycle: **Dream → Hope → Care → Joy → Trust → Growth**.

---

## What is included

- **SakThai core agent** — Python 3.11+ package with a provider-agnostic tool loop, retries, streaming, usage tracking, and dry-run preflight.
- **Persistent memory** — SQLite-backed facts and observations stored under `~/.sakthai`, with semantic search, tagging, consolidation, versioned JSON snapshots ([format](data/README.md)), and sync helpers.
- **Multiple providers** — Anthropic, Google Gemini, OpenAI-compatible endpoints, Ollama, gateways, and Hugging Face inference providers.
- **MCP** — dependency-light stdio server, remote HTTP/SSE client support, resource and prompt exposing, plus discovery, tool allowlisting, and namespaced connections to external MCP servers.
- **Six personas** — SakThai, SakSee, SakJules, SakKing, SakSit, and SakTan, each with its own identity, curated skills (480 on-disk skills under the searchable `Sak<Agent>-<domain>-<topic>` taxonomy), default model, and memory shard.
- **Team and client workflows** — declarative multi-persona pipelines and ServiceQuoteBot client workspace provisioning.
- **Unified Agent Platform** — core integration subsystems (`sakthai.agent_platform`) for accidental data loss prevention (`DataLossGuardrail`), reactive python dependency manager detection & isolated execution runners (`wrap_with_isolated_runner`), progressive disclosure skills rendering (`render_skills_progressive_summary`), Jules remote task delegation, dual Antigravity/ADK execution engine with model selection presets (`ModelTier`), and Harness AI agent pipeline spec generation.
- **Dashboard** — Next.js frontend backed by the SakThai HTTP API for personas, metrics, sessions, memory, audit data, and workflows.
- **Security and quality gates** — guardrails for tools and file access, strict typing, linting, secret scanning, CodeQL, Bandit, and automated tests.

---

## The Six Personas

<table>
  <tr>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/sakthai.svg" width="112" alt="SakThai, the lead: a cyan robot wearing a headset, with a family-hub badge of six linked nodes"><br><b>SakThai</b><br><sub>lead</sub></td>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/saksee.svg" width="112" alt="SakSee, the web and browser specialist: an amber robot with one wide scanning eye, with a globe badge"><br><b>SakSee</b><br><sub>web &amp; browser</sub></td>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/sakjules.svg" width="112" alt="SakJules, the GitHub, CI/CD and automation master: a violet robot with a gear antenna, with a branch-and-check badge"><br><b>SakJules</b><br><sub>GitHub &amp; CI/CD</sub></td>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/sakking.svg" width="112" alt="SakKing, the general assistant and runner: a blue robot wearing a crown, with a lightning-bolt badge"><br><b>SakKing</b><br><sub>assistant &amp; runner</sub></td>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/saksit.svg" width="112" alt="SakSit, the social and content specialist: a pink robot with a wide smile, with a speech-bubble badge"><br><b>SakSit</b><br><sub>social &amp; content</sub></td>
    <td align="center" valign="top" width="16%"><img src="docs/images/personas/saktan.svg" width="112" alt="SakTan, daily ops and rhythm: a calm emerald robot with a sun antenna, with a clock badge"><br><b>SakTan</b><br><sub>daily ops &amp; rhythm</sub></td>
  </tr>
</table>

| Persona | Role & Domain Specialty | Skills | Default Model |
| :--- | :--- | :---: | :--- |
| **SakThai** (lead) | Main Lead & Hugging Face Master (MLOps, hub, spaces) | **170** skills | `deepseek-ai/DeepSeek-V4.1-Flash` |
| **SakSee** | Web & Browser Specialist (Playwright, scraping, web UI) | **105** skills | `deepseek-ai/DeepSeek-V4.1-Flash` |
| **SakJules** | Master of Automation, GitHub & CI/CD Pipelines | **56** skills | `deepseek-ai/DeepSeek-V4.1-Flash` |
| **SakKing** | General Assistant, Runner & Primary Coder (TDD) | **59** skills | `Qwen/Qwen3-Coder-30B-A3B-Instruct` |
| **SakSit** | Social, Brand & Content Specialist | **45** skills | `deepseek-ai/DeepSeek-V4-Flash` |
| **SakTan** | Daily Ops, Daemon Watchdog & System Rhythm | **26** skills | `sakthai` on local Ollama |

> The six personas collectively host **480 on-disk skills** (461 persona overlays + 19 universal shared skills) adhering to a standardized frontmatter schema and the searchable `Sak<Agent>-<domain>-<topic>` taxonomy.

Every persona directory (`personas/<name>/`) carries the **6 core working files** — `SOUL.md` (identity, charge system v6, and self-evaluation v9 rubric), `PLAN.md` (v7 task decomposition and routing), `CYCLE.md` (v8 6-stage execution and v9 `CYCLE EVAL: <name>` rubric), `MEMORY.md` (active memory and lessons), `HANDOFF.md` (cross-persona handoff contract), and `BACKPACK.md` (domain toolbelt and skills inventory) — along with `config/config.yaml`, `config/workspace.yaml`, `config/mcp.json`, and its own DSPy/GEPA self-evolution engine (`personas/<name>/evolution/`).

`sakthai run --persona <name>` loads that persona's `SOUL.md`, skills, MCP servers, and memory shard (`~/.sakthai/<name>/memory.db`), and runs on its default model unless you pass `--provider` or `--model`. The first five run through the Hugging Face router and require `HF_TOKEN`. SakTan requires no external API key: it operates locally via Ollama at `127.0.0.1:11434` (configurable via `OLLAMA_HOST`).

### Multi-Agent Coordination & Deputy Chain

Each persona maintains its own isolated memory shard, and `sakthai memory family` reads across all six concurrently. Sibling agents coordinate work through durable handoffs: when SakThai exhausts charge, **SakKing** steps in as first deputy, followed by **SakTan**, then **SakSee**.

---

## Dashboard Overview

The Next.js dashboard in [`apps/sak_agent_dashboard`](apps/sak_agent_dashboard) provides visual telemetry and system management:

**Overview** — run totals, system pulse, and real-time persona cards:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/dashboard-overview-dark.png">
  <img alt="Dashboard overview with sample data: KPI strip (546 runs, 97.9% success), system pulse cards, and persona cards for SakKing, SakThai and SakSee" src="docs/images/dashboard-overview-light.png">
</picture>

**System** — live snapshot of personas, skills catalog, tools, CLI commands, and test suites:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/dashboard-system-dark.png">
  <img alt="Dashboard System view: repository totals, the layered architecture from entry points to SQLite, and the six persona cards with their roles, models and skill counts" src="docs/images/dashboard-system-light.png">
</picture>

---

## Architecture

Every entry point shares one unified tool registry, guardrail policy, and persistent memory store. Detailed architecture documentation is available in [`docs/architecture.md`](docs/architecture.md).

```mermaid
flowchart TD
    DASH["Dashboard<br/>Next.js, read-only"]
    WEB["Web API<br/>web/server.py, bearer token"]
    CLI["CLI<br/>sakthai run · chat · memory · team"]
    LOOP["Agent loop<br/>agent/loop.py"]
    MCP["MCP stdio server<br/>sakthai mcp"]
    GUARD["Guardrail policy<br/>checks every tool call"]
    TOOLS["Shared tool registry<br/>agent/tools.py"]
    STORE["MemoryStore<br/>memory/store.py"]
    HOME[("~/.sakthai<br/>memory.db per persona · sessions · eval log")]
    PROV["Model providers<br/>Anthropic · Gemini · OpenAI-compatible · Ollama · Hugging Face"]
    EXT["External MCP servers"]

    DASH -- HTTP --> WEB
    DASH -. direct reads .-> HOME
    WEB --> STORE
    CLI --> LOOP
    CLI --> MCP
    LOOP <--> PROV
    LOOP --> GUARD --> TOOLS
    MCP --> TOOLS
    TOOLS <--> EXT
    TOOLS --> STORE --> HOME
```

---

## Quick Start

### Prerequisites

- Python **3.11 or newer**
- [`uv`](https://docs.astral.sh/uv/)
- Node.js **22 or newer** (for the Next.js dashboard)

### Setup & Installation

```bash
cp .env.example .env
# Edit .env with your credentials (ANTHROPIC_API_KEY, HF_TOKEN, etc.)
uv sync --all-extras
```

### Essential Commands

```bash
sakthai status                                             # check environment and runtime health
sakthai doctor --json                                      # comprehensive system diagnostics
sakthai run "summarize docs/architecture.md"               # run default agent instruction
sakthai run "review latest memory" --persona sakking       # run instruction as SakKing
sakthai chat --persona sakthai                             # start interactive chat session
sakthai memory family --tag deputy-chain                   # search family-wide memory notes
sakthai eval personas                                      # verify all 6 personas contracts & rubrics
sakthai eval summary --all-personas                        # aggregate runtime evals across all shards
sakthai mcp                                                # launch stdio MCP server (default serve)
sakthai mcp list                                           # list configured external MCP servers
sakthai mcp ping [name]                                    # ping configured MCP servers
sakthai mcp tools                                          # list tools exposed by external MCP servers
sakthai platform skills                                    # progressive disclosure of available skills
sakthai platform antigravity "Inspect repo" --tier pro     # run Antigravity agent with model tier
sakthai platform export-harness --name "ReviewBot" --task "Review PR" # export Harness v1 pipeline agent spec
agent-workflow list                                        # list registered durable agent workflows
```

### Run the Dashboard

```bash
# Start Next.js dashboard and Python API concurrently:
make dashboard-dev

# Run standalone dashboard:
cd apps/sak_agent_dashboard && npm ci && npm run dev
```

---

## Repository Layout

```text
personas/sakthai/              Canonical installable Python package
personas/<name>/               Persona overlays, skills, and configuration
apps/sak_agent_dashboard/      Next.js dashboard
apps/agent_workflow_framework/ Standalone durable workflow execution framework & CLI
services/                      Service integrations and supporting services
tests/                         Pytest test suite (2,811 unit tests)
docs/                          Architecture, operations, security, and user guides
scripts/                       Repository and maintenance tooling
.github/workflows/             CI, security, evaluation, and maintenance workflows
```

---

## Development & Verification

Install dependencies and run validation checks:

```bash
uv sync --all-extras
make test                                      # run full pytest suite (enforces >=96% coverage)
make lint                                      # run Ruff linter & formatter checks
uv run mypy personas/sakthai                   # run strict type checker
uv run bandit -c pyproject.toml -r personas/sakthai  # run security vulnerability scanner
uv run pytest tests/test_persona_structure_parity.py tests/test_repo_hygiene.py
```

Additional repository tooling:

```bash
make compose-personas                          # build composed skill trees
make export-agent-repos                         # export standalone persona repository snapshots
make contract-types                             # regenerate dashboard API TypeScript types
uv run python scripts/diagnose_personas.py     # offline validation of all six personas
```

---

## Security and Privacy

Do not commit API keys, refresh tokens, memory databases, or client data. Use `.env` for local credentials.

- **Guardrail Execution**: `run_command` requires `SAKTHAI_SHELL_ALLOW`. Child processes do not inherit credentials. `read_file` is strictly jailed to allowable paths.
- **Local Web API**: Binds exclusively to loopback by default; all endpoints require bearer tokens.
- **Continuous Secret Scanning**: `gitleaks`, `Bandit`, `CodeQL`, and OpenSSF Scorecard enforce zero credential leakage on every commit and PR.

Vulnerabilities should be reported according to [`SECURITY.md`](SECURITY.md).

---

## License

This repository is **not open-source software**. It is distributed under the [House of Sak Intellectual Property License](LICENSE), copyright © 2026 Beer (`beer-sakthai`). Viewing and personal, non-commercial study are permitted; commercial use, redistribution, modification, deployment, and machine-learning training require explicit written permission.

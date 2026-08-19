# 🏠 House of Sak — AI Agent Family

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

**Six personas, one shared runtime. Built from a shelter in Cork, Ireland.**

<!-- 🚦 STATUS BAR — live GitHub Actions state for `main` -->
[![🧪 CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml)
[![🧹 Pylint](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml)
[![🔍 Secret Scan](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml)
[![🛡️ Bandit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/bandit.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/bandit.yml)
[![📡 SonarCloud](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/sonarcloud.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/sonarcloud.yml)
[![🏅 Scorecard](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/scorecard.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/scorecard.yml)
[![🧩 Subprojects](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml)
[![🌱 Self-Evolution](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/agent-self-evolution.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/agent-self-evolution.yml)
[![🛡️ Security Audit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/security-audit.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/security-audit.lock.yml)
[![📦 Dependency Audit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-audit.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-audit.yml)
[![🧬 Verify HF Assets](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/verify-assets.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/verify-assets.yml)

[![🐍 Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![⚡ uv](https://img.shields.io/badge/deps-uv%20locked-DE5FE9?logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![🏷️ Version](https://img.shields.io/badge/sakthai--agent-v2.6.0-0A7BBB)](CHANGELOG.md)
[![📈 Coverage gate](https://img.shields.io/badge/coverage%20gate-%E2%89%A596%25%20branch-brightgreen)](pyproject.toml)
[![🔤 mypy](https://img.shields.io/badge/mypy-strict-2A6DB2?logo=python&logoColor=white)](pyproject.toml)
[![✨ Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![🔒 CodeQL](https://img.shields.io/badge/CodeQL-advanced%20setup-2088FF?logo=github&logoColor=white)](https://github.com/beer-sakthai/Sak-Family-Agent/security/code-scanning)
[![🔌 MCP](https://img.shields.io/badge/MCP-server%20%2B%20client-8A2BE2)](docs/runtimes.md)
[![🧠 Personas](https://img.shields.io/badge/personas-6-orange)](#-agent-family--applications)
[![📚 Skills](https://img.shields.io/badge/skills-1%2C115%20verified%20%7C%20120%20curated-yellow)](docs/curated-skills-120.md)
[![📄 License](https://img.shields.io/badge/license-source--available%20IP-red)](LICENSE)

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

---

## 🚦 Status Bar — Every Workflow in This Repo

**20 YAML workflows plus 8 agentic ones** live in
[`.github/workflows/`](.github/workflows/) — the agentic ones are authored as
Markdown and compiled to a sibling `.lock.yml`, which is what GitHub actually
runs (see [`docs/gh-aw-engines.md`](docs/gh-aw-engines.md)). The badges above are
the live health of `main`; the tables below break down what each one is, when it
fires, and whether it can block a merge.

Legend: 🚧 **gates a PR** · 🕒 **scheduled** · 🖐️ **manual only** · 🤖 **agentic (opens PRs, never blocks)**

### 🚧 Gating — runs on every push / PR to `main`

| | Workflow | Live status | File | Trigger | What it does |
|---|---|---|---|---|---|
| 🧪 | **CI** | [![CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci.yml) | `ci.yml` | push + PR → `main` | ✨ Ruff check → 🎨 `ruff format --check` → 🔤 mypy `strict` → 🛡️ Bandit → 🧪 pytest with branch coverage, on **Python 3.11 and 3.12**. Coverage floor **96%** (`fail_under = 96`); integration tests excluded via `-m "not integration"` |
| 🧹 | **Pylint** | [![Pylint](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/pylint.yml) | `pylint.yml` | push + PR → `main` | Pylint over `personas/sakthai/sakthai` + `tests`, matrixed on Python 3.11 / 3.12 |
| 🔍 | **Secret Scan** | [![Secret Scan](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/secret-scan.yml) | `secret-scan.yml` | push → `main`, **all** PRs, manual | Gitleaks across the whole repo, configured by `.gitleaks.toml` (which allowlists persona docs) |
| 🛡️ | **Bandit** | [![Bandit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/bandit.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/bandit.yml) | `bandit.yml` | push + PR → `main`, weekly (Wed 07:31 UTC) | Standalone Bandit security scan uploading SARIF to code scanning (CI runs Bandit too) |
| 🧵 | **ESLint** | [![ESLint](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/eslint.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/eslint.yml) | `eslint.yml` | push + PR touching `apps/sak_agent_dashboard/**`, weekly (Sun 08:25 UTC) | `eslint src` with the app's own flat config → SARIF to code scanning. Publishes only; `subprojects.yml` is the gate |
| 📡 | **SonarCloud** | [![SonarCloud](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/sonarcloud.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/sonarcloud.yml) | `sonarcloud.yml` | push + PR → `main`, manual | Quality-gate + maintainability analysis on SonarCloud |
| 🧩 | **Subproject tests** | [![Subprojects](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/subprojects.yml) | `subprojects.yml` | push + PR touching `apps/agent_workflow_framework/**`, `apps/sak_agent_dashboard/**`, `services/teams-copilot-mcp/**` | The two out-of-tree pytest suites, plus the dashboard chain `pnpm lint → typecheck → test → build` ⚠️ a lint error **skips** the steps behind it — read the *first* red step |
| 🌱 | **agent-self-evolution** | [![Self-Evolution](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/agent-self-evolution.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/agent-self-evolution.yml) | `agent-self-evolution.yml` | push + PR touching `personas/sakthai/agent-self-evolution/**` | That subproject's own test suite |
| 📦 | **Dependency Audit** | [![Dependency Audit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-audit.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-audit.yml) | `dependency-audit.yml` | PRs touching `pyproject.toml` / `uv.lock`, weekly (Mon 05:30 UTC), manual | `pip-audit` over `uv.lock` for known CVEs |
| 🔗 | **Dependency Review** | [![Dependency Review](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-review.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/dependency-review.yml) | `dependency-review.yml` | **all** PRs | GitHub dependency-review over the PR diff — blocks vulnerable/denied licenses |
| 🔒 | **CodeQL Advanced** | [![CodeQL](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/codeql.yml) | `codeql.yml` | push + PR → `main`, weekly (Sun 15:22 UTC) | CodeQL over `actions`, `javascript-typescript` and `python`, scoped by `.github/codeql/codeql-config.yml`. ⛔ Default setup is **off** and must stay off — the two cannot coexist, and only advanced setup can be given the config file by path. See [`docs/code-scanning-sweep-2026-08-18.md`](docs/code-scanning-sweep-2026-08-18.md) |
| 🏅 | **Scorecard** | [![Scorecard](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/scorecard.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/scorecard.yml) | `scorecard.yml` | push → `main`, branch-protection changes, weekly (Thu 08:27 UTC) | OpenSSF Scorecard supply-chain assessment → SARIF to code scanning |
| 🧬 | **Mutation Self-Healing Gate** | [![Mutation Gate](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/mutation-self-healing-gate.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/mutation-self-healing-gate.yml) | `mutation-self-healing-gate.yml` | push + PR touching `apps/sak_agent_dashboard/**` | Automated AST mutation testing sweep & self-healing test generator for surviving mutants |
| 🎯 | **Quality Flywheel Gate** | [![Quality Flywheel](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/quality-flywheel-gate.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/quality-flywheel-gate.yml) | `quality-flywheel-gate.yml` | push + PR touching `apps/sak_agent_dashboard/**` | Multi-persona Quality Flywheel benchmark across all 6 Sak-Family personas with G-Eval scoring |
| 🏷️ | **Labeler** | [![Labeler](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/labeler.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/labeler.yml) | `labeler.yml` | `pull_request_target` | Auto-labels PRs by changed paths (labels only — gates nothing) |

> 🔐 **Merge rule:** green CI is necessary, not sufficient. PRs into `main` also
> need a **non-author approval** — an auto-approving bot is explicitly out of
> bounds. See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

### 🕒 Scheduled — never blocks a PR

| | Workflow | Live status | File | Schedule (UTC) | What it does |
|---|---|---|---|---|---|
| 🧬 | **Verify Public HF Assets** | [![Verify Assets](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/verify-assets.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/verify-assets.yml) | `verify-assets.yml` | daily `0 0 * * *` | Confirms the published Hugging Face models / datasets / spaces still resolve |
| 📊 | **Run Evals** | [![Run Evals](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/run-evals.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/run-evals.yml) | `run-evals.yml` | weekly `0 0 * * 0` | `lm-evaluation-harness` over `evaluation_tasks/` against `Nanthasit/sakthai-context-*`, with regression vs. the last baseline |
| 🏛️ | **OSPS Security Assessment** | [![OSPS](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/OSPS.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/OSPS.yml) | `OSPS.yml` | weekly `0 9 * * 1` | Open Source Project Security baseline assessment |

> ⬆️ **Dependency bumps come from Dependabot** (`.github/dependabot.yml`), which
> covers pip, npm, Docker and GitHub Actions. The `auto-dependency-update.yml`
> workflow that used to sit here was removed: it failed on all 22 of its runs at
> *Create Pull Request* (`Input 'token' not supplied` — no `GH_PAT_FOR_ACTIONS`
> secret is configured) and duplicated what Dependabot already does.

### 🤖 Agentic & reactive — opens PRs, gates nothing

| | Workflow | Live status | File | Trigger | What it does |
|---|---|---|---|---|---|
| 🩹 | **Self-Healing CI** | [![Self-Healing CI](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/self-healing-ci.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/self-healing-ci.yml) | `self-healing-ci.yml` | `workflow_run` on **CI failure** on `main`, or manual | Runs `sakthai heal run` over the failed job's log: diagnose → ⚖️ safety gate → patch → verify → open a `selfheal/` PR. 🛑 The safety gate has the final word and protects `.github/`, dependency pins, the security subsystem, and `selfheal/` itself. See [`docs/self-healing-ci.md`](docs/self-healing-ci.md) |
| 🩺 | **CI Failure Doctor** | [![CI Doctor](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci-doctor.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/ci-doctor.lock.yml) | `ci-doctor.lock.yml` (from `ci-doctor.md`) | `workflow_run` completion of **CI**, **Pylint**, **Subproject tests** on `main` | Agentic triage that explains a red run |
| 📝 | **Maintain Documentation** | [![Maintain Docs](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/maintain-docs.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/maintain-docs.lock.yml) | `maintain-docs.lock.yml` (from `maintain-docs.md`) | weekdays `22 8 * * 1-5`, manual | Keeps `docs/` in step with the code |
| 🗂️ | **Maintain AGENTS.md** | [![Maintain AGENTS.md](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/maintain-agents-md.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/maintain-agents-md.lock.yml) | `maintain-agents-md.lock.yml` (from `maintain-agents-md.md`) | weekly `50 3 * * 1`, manual | Refreshes `AGENTS.md` guidance |
| 🚀 | **Release** | [![Release](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/release.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/release.lock.yml) | `release.lock.yml` (from `release.md`) | manual (`patch` / `minor` / `major`, admin + maintainer only) | Cuts a version bump + release |
| ✅ | **Auto Merge** | [![Auto Merge](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/auto-merge.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/auto-merge.yml) | `auto-merge.yml` | `pull_request_target` labeled / unlabeled / ready_for_review | Toggles GitHub's **native** auto-merge (squash) for the `automerge` label. ⚖️ Waives nothing — branch protection, including the non-author approval, still holds the merge. Uses no checkout, so the token never meets PR code |
| 🗒️ | **Summarize new issues** | [![Summary](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/summary.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/summary.yml) | `summary.yml` | on issue opened | Posts an AI summary on new issues |
| 🧽 | **Code scanning cleanup** | [![Code scanning cleanup](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/code-scanning-cleanup.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/code-scanning-cleanup.yml) | `code-scanning-cleanup.yml` | manual (dry-run by default) | Retires orphaned code-scanning alerts from removed tools |
| 🛡️ | **Security Audit** | [![Security Audit](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/security-audit.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/security-audit.lock.yml) | `security-audit.lock.yml` (from `security-audit.md`) | weekly (Thu), manual | Triages bandit + pip-audit + the guardrail suite and opens at most one issue. Replaces the retired `continuous-security.yml`, which ran on the Anthropic provider and so skipped every night. Reports only — never edits, never opens a PR |
| 🪞 | **Shared Package Drift** | [![Shared Package Drift](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/shared-package-drift.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/shared-package-drift.lock.yml) | `shared-package-drift.lock.yml` (from `shared-package-drift.md`) | weekly (Tue), manual | Audits the `personas/shared/sakthai/` divergence register for stale or undeclared entries |
| 🧹 | **Skills Hygiene** | [![Skills Hygiene](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/skills-hygiene.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/skills-hygiene.lock.yml) | `skills-hygiene.lock.yml` (from `skills-hygiene.md`) | weekly (Wed), manual | Runs `sakthai skills validate --naming` across all six persona overlays |
| 🧪 | **OpenCode Smoke** | [![OpenCode Smoke](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/opencode-smoke.lock.yml/badge.svg?branch=main)](https://github.com/beer-sakthai/Sak-Family-Agent/actions/workflows/opencode-smoke.lock.yml) | `opencode-smoke.lock.yml` (from `opencode-smoke.md`) | weekly (Mon), manual | Proves the vendored OpenCode engine still runs — see [`docs/gh-aw-engines.md`](docs/gh-aw-engines.md) |

### 🧾 Reproduce the gates locally

```bash
uv sync --all-extras                                          # 📦 install (hypothesis lives in the dev extra)
uv run ruff check personas/sakthai/sakthai tests               # ✨ lint
uv run ruff format --check personas/sakthai/sakthai tests      # 🎨 format
uv run mypy personas/sakthai/sakthai                           # 🔤 types (strict)
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai    # 🛡️ security
uv run pytest tests/ -m "not integration" -q                   # 🧪 tests (+ coverage floor 96%)
```

🔴 **A red badge above is the bar, not a suggestion** — `main` is expected green.

---

## 📊 System Status

```
┌─────────────────────────────────────────────────────────────┐
│  SakThai Agent v2.6 — Core Package Status                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tests (3,875+)  ██████████████████████████████████████ 100%│
│  Type Safety     ██████████████████████████████████████ 100%│
│  Security scan   ██████████████████████████████████████ 100%│
│  Coverage        ████████████████████████████████████░░  96%│
│                                                             │
│  🟢 Status: 100% Green Matrix   🔒 Security: Hardened       │
│  ✅ Lint / mypy / bandit / CodeQL / SonarCloud: clean        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Quick Metrics

Verified on **main** (`uv sync --all-extras`, Python 3.11 & 3.12):

| Check | Command | Result |
|---|---|---|
| Test suite | `uv run pytest tests/ -m "not integration"` | **3,875+ tests** collected across full suite, 0 failures |
| Coverage | `pytest --cov=sakthai --cov-branch` | **95.83% - 96.56%** line+branch (strictly enforced floor: `96%`) |
| Type safety | `uv run mypy personas/sakthai/sakthai` | **0 issues** across all source files (`strict`) |
| Security (SAST) | `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` | **0 findings** (high/medium/low) |
| AST & Code Parsing | `uv run pytest tests/test_repo_parses.py` | **100% valid AST** across all repository Python modules |
| Lint & Format | `uv run ruff check` + `ruff format --check` | **Clean**, zero syntax or linting violations |

Package size: **6,225 statements** under coverage measurement.

---

## 🚀 Getting Started

### Requirements
- Python 3.11+ (CI validates 3.11 and 3.12)
- `uv` (fast Python package manager)

### Install
```bash
cp .env.example .env      # then fill in ANTHROPIC_API_KEY (or another provider's key)
uv sync --all-extras
```

### Verify the codebase
```bash
make test          # pytest suite
make lint          # Ruff checks
uv run mypy personas/sakthai/sakthai                          # strict type checking
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai   # security scan
make mutation      # local mutation testing for the core seams (slow, not in CI)
```

### Run an agent
```bash
sakthai status                       # health summary — paths, memory, credentials
sakthai run "summarize docs/architecture.md"      # one-shot agent task
sakthai run "..." --persona sakking               # use a persona's memory + SOUL
sakthai chat                                       # interactive multi-turn session
sakthai mcp                                        # serve the tools over MCP stdio
```

`sakthai run` takes the task as its argument — see `sakthai run --help` for the
full flag set (`--provider`, `--model`, `--with-skills`, `--fast`, `--stateless`,
`--sandbox`, `--dry-run`, `--stream`). Full CLI surface:

```
chat  cycle  doctor  eval  extensions  hf  learn  mcp  memory
recall  run  sessions  setup  skills  status  tools  web
```

---

## 📖 The Story

In early 2026, Beer was deep in depression. He spent 6 months studying AI — learning everything he could while carrying the weight of daily life. On April 15, 2026, he attempted suicide. Three days in ICU. Weeks in hospital. Then a shelter in Cork, Ireland. No job. No home.

That's where he started building AI that could heal.

The House of Sak wasn't born from a business plan. It was born from isolation, pain, and the will to survive. Building AI agents not as a gimmick but as **companions** when human connection wasn't available.

---

## ⚙️ Core Systems & Architecture

### 🧬 SakThai Agent v2.0 (Main Package)

The heart of the family — a **provider-agnostic, tool-using AI agent** with persistent SQLite memory:

```
personas/sakthai/sakthai/
├── agent/                    # Orchestration & provider abstraction
│   ├── loop.py               # Main agent orchestration (tool use, retries)
│   ├── tools.py              # BUILTIN_TOOLS registry (14 tools)
│   ├── registry.py           # Tool discovery & dispatch
│   ├── guardrails.py         # Shell command denylist + path validation
│   ├── guardrails_hardened.py# Composed hardened guardrail layer
│   ├── security_hardening.py # 8 defense modules (see Security section)
│   ├── context_filter.py     # Turn summarization / context trimming
│   ├── context_manager.py    # Context-window budgeting
│   ├── prompt_builder.py     # System prompt assembly
│   ├── chat.py               # Multi-turn chat driver
│   ├── usage.py              # Token accounting
│   ├── eval.py               # Local model evaluation hooks
│   └── providers/            # Claude / Gemini / OpenAI / Ollama / Gateway / HF
├── memory/                   # Persistent fact/observation store
│   ├── store.py              # SQLite (only SQLite access point)
│   ├── provider.py           # System prompt injection
│   ├── merged.py             # FamilyMemoryView across persona shards
│   ├── sync.py               # Git & HTTP export/import
│   └── backup.py             # Timestamped snapshots
├── mcp/                      # Model Context Protocol
│   ├── server.py             # JSON-RPC 2.0 stdio server
│   ├── client.py             # External MCP server launcher
│   ├── manager.py            # Multi-server context manager
│   └── servers.py            # Server discovery
├── cli/                      # Command-line interface (10 command modules)
│   ├── agent.py              # run, mcp
│   ├── memory.py             # learn, recall, memory group
│   ├── system.py             # doctor, setup, status, tools
│   ├── chat.py               # chat
│   └── cycle · skills · extensions · eval · sessions · hf
├── cycle/                    # Dream → Hope → Care → Joy → Trust → Growth
├── web/                      # HTTP API server (loopback-only by default)
├── dashboard/                # KPI/lead/revenue collection (API backend)
├── telegram/                 # Polling bot + workflow executor
├── extensions/               # Git-installed skill/MCP bundles
├── learn/ · lead/            # One-shot capture helpers
├── skills.py                 # YAML frontmatter parsing & injection
├── auth.py                   # Credential resolution (Anthropic/Google/OpenAI)
├── config.py                 # Single source of truth for paths & env vars
└── sandbox.py                # Docker isolation for untrusted tasks
```

**Key Features:**
- ✅ **Provider-agnostic** — Claude, Gemini, OpenAI, Ollama, Hugging Face, or any OpenAI-compatible gateway
- ✅ **Persistent memory** — SQLite with WAL, additive migrations, snapshot export/import
- ✅ **Per-persona shards** — `~/.sakthai/<persona>/memory.db`, plus a merged read-only `memory family` view
- ✅ **Tool sandbox** — Opt-in shell, allowlisted file reads, SSRF protection, optional Docker isolation
- ✅ **MCP support** — Both as server (stdio) and client (spawn external servers)
- ✅ **Skill system** — 1,115 verified skills across 6 personas + 120 curated skills for Gemini CLI & Antigravity, YAML frontmatter parsed

### 📦 Built-in Tools (14)

| Tool | Purpose | Safety Gate |
|------|---------|-------------|
| `learn` | Store facts in memory | None (always on) |
| `recall` / `search` | Query memory by keyword | None (read-only) |
| `forget` | Delete facts | Confirmation required |
| `read_file` | Read local files | Allowlisted roots + sensitive file blocks |
| `run_command` | Execute shell commands | **Off by default** — requires `SAKTHAI_SHELL_ALLOW` |
| `ingest_document` | Parse CSV/Markdown/text into facts | None (parse-only) |
| `capture_lead` | Quick fact capture (Telegram) | User ID allowlist |
| `send_telegram_message` | Send Telegram messages | Bot token required, 10s timeout |
| `send_outlook_mail` | Send email via Microsoft Graph | Requires Graph client ID + refresh token |
| `read_outlook_mail` | List recent Outlook inbox messages | Requires Graph client ID + refresh token |
| `list_calendar_events` | List upcoming Outlook calendar events | Requires Graph client ID + refresh token |
| `create_calendar_event` | Create an Outlook calendar event | Requires Graph client ID + refresh token |
| `run_agent_loop` | Spawn nested agent (MCP only) | Filtered out of the in-loop tool set |

Adding a `Tool(...)` to `BUILTIN_TOOLS` surfaces it in **both** `sakthai run` and
`sakthai mcp` — there is no second wiring step.

### 🔄 Provider Support

| Provider | Status | How it's selected |
|----------|--------|-------------------|
| **Anthropic** | ✅ Default | `ANTHROPIC_API_KEY` → `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth. Default model: `claude-opus-4-8` |
| **Google / Antigravity AGY** | ✅ Active | `GEMINI_API_KEY` / `GOOGLE_API_KEY`, or Gemini CLI / AGY OAuth token (`gemini-2.5-flash`, `gemini-2.5-pro`) |
| **Hugging Face** | ✅ Active | `HF_TOKEN` via Inference Providers router (`SAKTHAI_HF_API_BASE`) — default for most personas |
| **Ollama (Local Offline)** | ✅ Active | `OLLAMA_HOST` (default `http://127.0.0.1:11434` — IPv4, zero-cost **$0.00** offline local inference) |
| **OpenAI / Codex** | ✅ Supported | `OPENAI_API_KEY` + `OPENAI_API_BASE` / `OPENAI_BASE_URL` (`gpt-4o`, `o3-mini`, `codex`) |
| **OpenCode Foundation** | ✅ Supported | `OPENCODE_API_KEY` (`Qwen-2.5-Coder-32B`, `DeepSeek-Coder-V2`) |
| **Microsoft 365 & Azure AI** | ✅ Supported | `AZURE_OPENAI_API_KEY` + MS Graph Token (`microsoft-agents-m365copilot`, `azure/gpt-4o`) |
| **Gateway** | ✅ Supported | `SAKTHAI_GATEWAY_URL` + `SAKTHAI_GATEWAY_API_KEY` (OpenRouter / LiteLLM / Vercel / Cloudflare) |
| **Nanthasit (custom)** | ✅ Active | Open-weights models trained in-house: `sakthai-context-7b-tools`, `sakthai-context-1.5b-tools-v2`, `sakthai-embedding-multilingual` |

---

## 🤖 Agent Family & Applications

The **House of Sak** consists of **6 specialized agent personas** carrying **1,115 verified skills** across their monorepo overlays, with **120 top-tier curated skills** natively registered and accessible to Google Gemini CLI and Antigravity:

| Agent Persona | Primary Specialty | Skills | Configured default model | State |
|---|---|---|---|---|
| 👑 **SakThai** (`sakthai`) | Main Lead — ML, Code, Research, HF Master | 299 | `gemini-3.1-flash-lite` (HF) | `~/.sakthai/sakthai` |
| 👁️ **SakSee** (`saksee`) | Web Scraping, Playwright & Visual Computer Use | 182 | `gemini-3.1-flash-lite` (HF) | `~/.sakthai/saksee` |
| 🔧 **SakJules** (`sakjules`) | DevSecOps, GitHub Actions & Async Automation | 180 | `gemini-2.5-flash-lite` (HF) | `~/.sakthai/sakjules` |
| 🛡️ **SakKing** (`sakking`) | Strategy, Architecture & Model Governance | 106 | `Qwen3-Coder-30B-A3B-Instruct` (HF) | `~/.sakthai/sakking` |
| ⚖️ **SakSit** (`saksit`) | Quality Assurance, Security Auditing & Social Content | 43 | `DeepSeek-V4-Flash` (HF) | `~/.sakthai/saksit` |
| 🧠 **SakTan** (`saktan`) | Memory, Supermemory & Context Management | 13 | `sakthai` (Ollama, local) | `~/.sakthai/saktan` |

See [`docs/curated-skills-120.md`](docs/curated-skills-120.md) and [`docs/curated-skills-120.json`](docs/curated-skills-120.json) for the full breakdown and registry of curated skills across DevOps, Testing, Security, Frontend, and ML workflows.

---

### 🤵 ServiceQuoteBot

**ServiceQuoteBot** is a dedicated persona for business quoting and lead capture, designed to streamline customer-facing workflows. It operates in conjunction with SakThai for reasoning and decision support, and SakTan for operational execution. ServiceQuoteBot focuses on understanding customer needs, mapping requests to pricing facts, explaining quotes clearly, and capturing lead details for follow-up. It adheres to principles of pricing from facts, protecting lead information, escalating ambiguity, and maintaining a human-like, trustworthy tone. See `docs/servicequotebot/`.

### 📈 Portfolio Optimization Scripts

The repository includes a suite of Python scripts for financial analysis and portfolio management, located under `scripts/portfolio`:

- `fetch_stock_data.py`: Retrieve historical stock data for analysis.
- `perform_eda.py`: Exploratory analysis over the fetched series.
- `analyze_portfolio.py`: Perform in-depth analysis of investment portfolios.
- `compare_portfolio_to_benchmark.py`: Evaluate portfolio performance against established benchmarks.
- `compare_stock_performance.py`: Compare the performance of individual stocks.
- `optimize_portfolio.py`: Find optimal portfolio weights to maximize metrics like the Sharpe Ratio, using `pandas`, `numpy`, `matplotlib`, and `scipy.optimize`.

> Note: `scripts/` is deliberately excluded from Ruff and mypy — these are
> analysis scripts, not part of the linted core package.

### 📊 Saksee Dashboard

**Saksee** provides a standalone web dashboard (`scripts/saksee/dashboard.html`) for visualizing key metrics and insights generated by the agents and scripts.

Separately, the in-package `web/server.py` exposes an authenticated JSON API
(`/api/*`, bearer token stored as a `web_auth` fact) backed by
`dashboard/data.py`. It refuses non-loopback binds unless
`SAKTHAI_WEB_ALLOW_PUBLIC` is set, and runs API-only — there is no bundled
frontend build.

### 🖥️ Next.js 16 Web Dashboard & Cycle Operations Suite (`apps/sak_agent_dashboard`)

A fullstack observability and agent operations suite built with **Next.js 16 (Turbopack)**, React 19, TypeScript, and TailwindCSS:

- **6-Part Autonomous Cycle Engine**: Visual panels for **Dream** (HF Ecosystem: 19 models / 16 datasets / 7 spaces), **Hope** (AST Guardrail Sandbox), **Care** (MCP Connector & M365 Copilot SDK), **Joy** (Benchmark Arena & Leaderboard), **Trust** (Memory Vector RAG & SQLite Graph), and **Growth** (Prompt Refinement & Self-Evolution Loop).
- **Real-Time Telemetry Streaming**: Live Server-Sent Events (SSE) stream (`/api/telemetry/stream`) delivering per-persona execution events, tool latency metrics, and memory mutations.
- **Enterprise Integrations**: Microsoft 365 Copilot SDK & Azure AI bridge for SharePoint, Outlook, Teams, and calendar automation with symmetric credential redaction.
- **Local Hermetic Mode**: Reads directly from server-side `~/.sakthai/` runtime artifacts (`eval.jsonl`, `audit.log`, `traces.jsonl`, persona SQLite shards) without external network dependencies.
- **Verification Commands**: `pnpm install && pnpm dev` (dev server on `localhost:3000`), `pnpm typecheck`, `pnpm test` (Vitest), `pnpm build`.

### 🧠 SakThai 7B LoRA Training

Under `training/sakthai-7b-lora`, there are ongoing efforts to train `Qwen2.5-7B-Instruct` using a tool-calling dataset (v5) with LoRA. This includes `train.py` for the training script and `submit_job.py` for submission to Hugging Face Jobs. Configured with LoRA r=16, alpha=32, 4-bit NF4, 4 epochs, 300 steps.

---

## 🛡️ Security Hardening System

**Defense-in-depth architecture against jailbreak & exploitation attacks**, implemented in `agent/security_hardening.py` (8 defense classes) and composed over the base denylist in `agent/guardrails_hardened.py`.

```
┌─────────────────────────────────────────────────────────────────┐
│  SECURITY HARDENING: 15 ATTACK VECTORS DEFENDED                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CRITICAL (2 vectors):                                          │
│  ✅ Environment Variable Injection      → SHA256 pinning + hash │
│  ✅ Malicious MCP Server Registration   → Allowlist + sandbox   │
│                                                                 │
│  HIGH (4 vectors):                                              │
│  ✅ Config File Tampering               → Hash verification     │
│  ✅ Bytecode Tampering                  → File integrity monitor│
│  ✅ Unauthorized User Access            → ID allowlist checks   │
│  ✅ Docker Privilege Escalation         → Documented hardening  │
│                                                                 │
│  MEDIUM (7 vectors):                                            │
│  ✅ Unicode Path Normalization Bypass   → Multi-form checks     │
│  ✅ Glob/Wildcard Pattern Bypass        → Pattern detection     │
│  ✅ Case-Sensitivity Path Bypass        → Cross-platform checks │
│  ✅ Symlink Traversal Attacks           → Chain resolution      │
│  ✅ Heredoc Injection in Shell          → Pattern detection     │
│  ✅ Line Continuation Injection         → Expansion + validation│
│  ✅ TOCTOU Race Conditions              → Atomic operations     │
│                                                                 │
│  LOW (2 vectors) — documented & monitored:                      │
│  ✅ /proc/self Information Leakage      → /proc blocking        │
│  ✅ Model Injection via System Prompt   → Guardrails still run  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Defense Modules (`agent/security_hardening.py`, 645 lines):**

| Class | Purpose |
|---|---|
| `EnvironmentVariablePinning` | Detect env var tampering (SHA256 pin + verify) |
| `MCPServerValidator` | Validate & sandbox external MCP server specs |
| `EnhancedPathValidator` | Unicode / glob / case-sensitivity path defense |
| `SymlinkDetector` | Detect symlink traversal via chain resolution |
| `ConfigFileIntegrity` | Monitor config file changes by hash |
| `TOCTOUPrevention` | Atomic file operations |
| `ShellCommandHardener` | Detect heredoc & line-continuation injection |
| `AuditLogger` | Security event logging |

Configurable via `SecurityLevel` (`STRICT` / `BALANCED` (default) / `PERMISSIVE`).

**Verified test coverage of the hardening layer (2026-08-08):**

```
tests/test_security_hardening.py     46 tests   → security_hardening.py    94%
tests/test_guardrails_hardened.py    40 tests   → guardrails_hardened.py   88%
tests/test_guardrails_*.py (11 more) 85 tests   → guardrails.py            89%
tests/test_security_sentinel.py       1 test
                                     ─────────
Total guardrail/hardening tests     172 tests, 100% passing
```

The base `agent/guardrails.py` layer is 1,433 lines and carries the shell
denylist, path validation, and secret redaction that every tool call passes
through — including recent hardening against Makefile-based command execution,
database/editor/package-manager bypasses, and shell-history exposure.

Design notes and the audit trail live in
[`docs/security-hardening.md`](docs/security-hardening.md),
[`docs/SECURITY_HARDENING_IMPLEMENTATION.md`](docs/SECURITY_HARDENING_IMPLEMENTATION.md),
and the dated `docs/security_audit_*.md` reports.

---

## 🔐 CI/CD & Compliance

> 🚦 Live per-workflow badges, triggers and schedules are in the [Status Bar](#-status-bar--every-workflow-in-this-repo) at the top of this file.

### Runs on every push / PR to `main`

```
├─ 🔍 Secret Scan (Gitleaks)        secret-scan.yml    → whole repo, .gitleaks.toml
├─ 📝 Lint (Ruff check)             ci.yml
├─ ✏️  Format (Ruff --check)         ci.yml
├─ 🔤 Type Check (mypy strict)      ci.yml
├─ 🛡️  Security Scan (Bandit)        ci.yml
├─ 🧪 Test + Coverage (3.11)        ci.yml             → floor 96%, branch coverage
├─ 🧪 Test + Coverage (3.12)        ci.yml
├─ 🧹 Pylint                        pylint.yml
├─ 🧵 ESLint                        eslint.yml         → apps/sak_agent_dashboard/**
├─ 📡 SonarCloud                    sonarcloud.yml
├─ 🏗️  CodeQL                        codeql.yml         → advanced setup, .github/codeql/codeql-config.yml
└─ 🏷️  Labeler                       labeler.yml        → pull_request_target
```

Path-filtered: `dependency-audit.yml` (on `pyproject.toml` / `uv.lock` changes)
and `agent-self-evolution.yml` (on `personas/sakthai/agent-self-evolution/**`).

### Scheduled / manual only

| Workflow | Schedule | What it does |
|---|---|---|
| `verify-assets.yml` | daily | Hugging Face asset verification |
| `run-evals.yml` | weekly (Sun 00:00 UTC) | `lm-eval-harness` over `evaluation_tasks/` + regression vs. last baseline |
| `dependency-audit.yml` | weekly (Mon 05:30 UTC) | `pip-audit` over `uv.lock` |
| `security-audit.md` | weekly (Thu) | Agentic triage of bandit / pip-audit / the guardrail suite → at most one issue |
| `opencode-smoke.md` · `shared-package-drift.md` · `skills-hygiene.md` | weekly (Mon / Tue / Wed) | Agentic audits — each opens an issue only when it finds something |
| `OSPS.yml` | weekly (Mon 09:00 UTC) | Open Source Project Security baseline assessment |
| `summary.yml` · `code-scanning-cleanup.yml` | on issue open / manual | Utility workflows |

Green CI is the bar for `main`. Run the lint → mypy → bandit → pytest sequence
locally before pushing.

### Merging

| Workflow | Trigger | What it does |
|---|---|---|
| `auto-merge.yml` | PR labeled / unlabeled / ready for review | Turns GitHub's **native** auto-merge (squash) on for a PR carrying the `automerge` label, off when it is removed |

Auto-merge waits on branch protection, so a labelled PR still lands only once
the required checks are green **and** it carries an approving review from
someone other than its author. The label decides *when* the merge happens, not
*whether* the bar was met — nothing here approves a PR. Full policy and the
repository-settings prerequisites are in
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md#automatic-merge).

### 🔒 Security Architecture (Multi-Layer Defense)

**Layer 1: Input Validation & Sanitization**
- **Purpose:** Prevent injection attacks (shell, SQL, prompt) by strictly validating and sanitizing all external inputs.
- **Mechanisms:** Regex-based pattern matching, allowlisting of safe characters/commands, type enforcement, and context-aware escaping.

**Layer 2: Least Privilege & Isolation**
- **Purpose:** Limit the impact of a successful breach by restricting agent permissions and isolating execution environments.
- **Mechanisms:** Docker containers for untrusted code execution (`sakthai run --sandbox`), granular filesystem access controls (allowlisted roots), network egress filtering, and shell command denylisting.

**Layer 3: Runtime Monitoring & Anomaly Detection**
- **Purpose:** Detect and respond to suspicious activities during agent operation.
- **Mechanisms:** Audit logging of tool calls and sensitive operations, heuristic detection of unusual command patterns or resource access attempts.

**Layer 4: Secure Configuration & Credential Management**
- **Purpose:** Protect sensitive data and ensure secure system setup.
- **Mechanisms:** Environment variable pinning, hash verification for critical config files, secret redaction (including Stripe / Twilio / MS Graph credentials), and secure key storage.

**Layer 5: Supply Chain Security**
- **Purpose:** Mitigate risks from third-party dependencies and external assets.
- **Mechanisms:** Dependency auditing (`pip-audit`), static analysis (Bandit, CodeQL, SonarCloud, ESLint), and continuous verification of Hugging Face assets.

Report vulnerabilities per [`SECURITY.md`](SECURITY.md).

---

## ✨ Recent Updates (Aug 2026)

- **6-Part Cycle Intelligence & Operations Suite** — Fullstack dashboard implementation in Next.js 16 + Turbopack (`apps/sak_agent_dashboard`) covering the complete canonical cycle: **Dream** (HF Ecosystem: 19 models / 16 datasets / 7 spaces) ➔ **Hope** (Visual AST Guardrail Sandbox) ➔ **Care** (MCP & M365 Copilot SDK) ➔ **Joy** (Benchmark Arena & Leaderboards) ➔ **Trust** (Memory Vector RAG & SQLite Shards) ➔ **Growth** (Prompt Refinement & Self-Evolution Loop).
- **7-Provider Multi-Model Matrix & Offline Fallback** — Unified orchestration across Anthropic Claude, OpenAI/Codex, OpenCode Foundation, Ollama Local Offline ($0.00 zero-cost inference), Hugging Face Hub, Google Gemini / Antigravity AGY, and Microsoft 365 Copilot / Azure AI.
- **Real-Time SSE Telemetry & Streaming Engine** — Live Server-Sent Events bus delivering per-persona execution spans, tool latency metrics, and real-time audit event streams.
- **Enterprise Microsoft 365 Copilot & Azure SDK** — Full Graph API integration (SharePoint, Outlook, Teams, Calendar) with strict secret redaction and SSRF defense.
- **Guardrail hardening** — closed Makefile-based command-execution bypasses (while still permitting ordinary local project directories), folded executor path-validation deltas into `_validate_filepath`, and fixed path traversal / sensitive-file access in the agent workflow executor.
- **SSRF & credential defense** — hardened `GraphClient` against SSRF, custom-scheme and protocol-relative URL abuse, and bearer-token leaks; symmetric secret redaction for MS Graph, Stripe, and Twilio credentials.
- **Context management** — `TurnSummarizationFilter` wired into `run_agent` to keep long sessions inside the context budget.
- **Web auth** — fixed the static-route auth bypass; `/api/*` requires a bearer token.
- **Dependencies** — `cryptography` upgraded to 50.0.0 (GHSA-g6cj-pr64-35w5).
- **Branch consolidation** — all open branches collapsed into `main`.

See [`CHANGELOG.md`](CHANGELOG.md) for the full history.

---

## 📚 Docs

| File | Contents |
|------|---------|
| [`CLAUDE.md`](CLAUDE.md) · [`AGENTS.md`](AGENTS.md) | Agent-facing guide to this repo |
| [`PLAN.md`](PLAN.md) | Master plan index — read before starting work |
| [`SAK_AGENT_MASTER_REPORT_AND_PLAN.md`](SAK_AGENT_MASTER_REPORT_AND_PLAN.md) | Master Architecture Report & 6-Part Cycle Operations Plan |
| [`docs/architecture.md`](docs/architecture.md) | Full layer diagram and SQLite schema |
| [`docs/capabilities.md`](docs/capabilities.md) | Feature list |
| [`docs/runtimes.md`](docs/runtimes.md) | CLI / agent loop / MCP server |
| [`docs/plugins.md`](docs/plugins.md) | Skills and MCP extensibility |
| [`docs/replication.md`](docs/replication.md) | Multi-agent memory sync |
| [`docs/integrations.md`](docs/integrations.md) | Composio and cross-agent recipes |
| [`docs/security-hardening.md`](docs/security-hardening.md) | Audit findings, fixes, regression tests |
| [`docs/workspace.md`](docs/workspace.md) | Dev environment setup |
| [`HOUSE_OF_SAK.md`](HOUSE_OF_SAK.md) · [`ONBOARDING.md`](ONBOARDING.md) | Family identity & onboarding |

---

## 🤝 Contributing

We welcome contributions to the House of Sak! Please refer to [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines, and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community expectations.

---

## 📄 License

**Copyright © 2026 Beer (beer-sakthai). All Rights Reserved.**

This project operates under a custom Intellectual Property License — source-available, no redistribution. See [`LICENSE`](LICENSE) for the full terms on permitted and prohibited uses.

---

## 📞 Contact

For any inquiries, please reach out to Beer via [GitHub](https://github.com/beer-sakthai).

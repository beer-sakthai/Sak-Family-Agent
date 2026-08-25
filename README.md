# 🏠 House of Sak — AI Agent Family

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

**Six personas, one shared runtime. Built from a shelter in Cork, Ireland.**

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

---

## 📊 System Status

```
┌─────────────────────────────────────────────────────────────┐
│  Repository Metrics                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  💾 Repo Size: 10M                                          │
│  📂 Files: 4461                                             │
│  🌳 Git Tree (Commits): 1                                   │
│  📚 Docs/Articles: 63                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│  SakThai Agent v2.0 — Core Package Status                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tests (1,978)   ██████████████████████████████████████ 100%│
│  Type Safety     ██████████████████████████████████████ 100%│
│  Security scan   ██████████████████████████████████████ 100%│
│  Coverage        ████████████████████████████████████░░  97%│
│                                                             │
│  🟢 Status: Production Ready   🔒 Security: Hardened        │
│  ✅ Lint / mypy / bandit: clean                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Quick Metrics

Verified locally on **2026-08-08** (`uv sync --all-extras`, Python 3.12):

| Check | Command | Result |
|---|---|---|
| Test suite | `uv run pytest tests/ -m "not integration"` | **1,978 tests** collected across 95 files, 0 failures, 1 skipped |
| Coverage | `pytest --cov=sakthai --cov-branch` | **96.56%** line+branch (floor: `fail_under = 96`) |
| Type safety | `uv run mypy personas/sakthai/sakthai` | **0 issues** across 69 source files (`strict`) |
| Security | `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` | **0 findings** (high/medium/low) |
| Lint | `uv run ruff check` + `ruff format --check` | All checks passed, 166 files formatted |

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
- ✅ **6-stage cycle** — Dream → Hope → Care → Joy → Trust → Growth state machine
- ✅ **Skill system** — 31 curated + 3 shared + 823 persona skills, YAML frontmatter parsed

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
| **Google** | ✅ Active | `GEMINI_API_KEY` / `GOOGLE_API_KEY`, or Gemini CLI OAuth token |
| **Hugging Face** | ✅ Active | `HF_TOKEN` via the Inference Providers router (`SAKTHAI_HF_API_BASE`) — the configured default for most personas |
| **Ollama** | ✅ Active | `OLLAMA_HOST` (default `http://127.0.0.1:11434` — IPv4 on purpose) |
| **OpenAI-compatible** | ✅ Supported | `OPENAI_API_KEY` + `OPENAI_API_BASE` / `OPENAI_BASE_URL` |
| **Gateway** | ✅ Supported | `SAKTHAI_GATEWAY_URL` + `SAKTHAI_GATEWAY_API_KEY` (OpenRouter / LiteLLM / Vercel / Cloudflare) |
| **Nanthasit (custom)** | ✅ Active | Open-weights models trained in-house: `sakthai-context-7b-tools`, `sakthai-context-1.5b-tools-v2`, `sakthai-embedding-multilingual` |

---

## 🤖 Agent Family & Applications

The **House of Sak** consists of **6 specialized agent personas** carrying **823 skills** in their monorepo overlays (counted as `SKILL.md` files, excluding `.archive/`):

| Agent Persona | Primary Specialty | Skills | Configured default model | State |
|---|---|---|---|---|
| 👑 **SakThai** (`sakthai`) | Main Lead — ML, Code, Research, HF Master | 299 | `gemini-3.1-flash-lite` (HF) | `~/.sakthai/sakthai` |
| 👁️ **SakSee** (`saksee`) | Web Scraping, Playwright & Visual Computer Use | 182 | `gemini-3.1-flash-lite` (HF) | `~/.sakthai/saksee` |
| 🔧 **SakJules** (`sakjules`) | DevSecOps, GitHub Actions & Async Automation | 180 | `gemini-2.5-flash-lite` (HF) | `~/.sakthai/sakjules` |
| 🛡️ **SakKing** (`sakking`) | Strategy, Architecture & Model Governance | 106 | `Qwen3-Coder-30B-A3B-Instruct` (HF) | `~/.sakthai/sakking` |
| ⚖️ **SakSit** (`saksit`) | Quality Assurance, Security Auditing & Social Content | 43 | `DeepSeek-V4-Flash` (HF) | `~/.sakthai/saksit` |
| 🧠 **SakTan** (`saktan`) | Memory, Supermemory & Context Management | 13 | `sakthai` (Ollama, local) | `~/.sakthai/saktan` |

Each persona ships `/skills/` (prefixed `Sak<Name>-`) and `/config/`
(`config.yaml`, `mcp.json`, `gateway_voice_mode.json`). Five of the six symlink
the shared `personas/shared/sakthai/` package; **SakThai's copy is the one
actually installed and run**.

Shared skill pools on top of the per-persona overlays: `personas/shared/skills/`
(3 skills, byte-identical across personas) and the root `library/` (31 curated
skills across 11 categories).

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

### Runs on every push / PR to `main`

```
├─ 🔍 Secret Scan (Gitleaks)        secret-scan.yml    → whole repo, .gitleaks.toml
├─ 📝 Lint (Ruff check)             ci.yml
├─ ✏️  Format (Ruff --check)         ci.yml
├─ 🔤 Type Check (mypy strict)      ci.yml
├─ 🛡️  Security Scan (Bandit)        ci.yml
├─ 🧪 Test + Coverage (3.11)        ci.yml             → floor 96%, branch coverage
├─ 🧪 Test + Coverage (3.12)        ci.yml
├─ 🧹 Pylint                        pylint.yml         → on: push
├─ 🤖 OSSAR Scan                    ossar.yml
├─ 📡 SonarCloud                    sonarcloud.yml
├─ 🏗️  CodeQL                        GitHub default setup (no workflow file — adding one would conflict)
└─ 🏷️  Labeler                       labeler.yml        → pull_request_target
```

Path-filtered: `dependency-audit.yml` (on `pyproject.toml` / `uv.lock` changes)
and `agent-self-evolution.yml` (on `personas/sakthai/agent-self-evolution/**`).

### Scheduled / manual only

| Workflow | Schedule | What it does |
|---|---|---|
| `continuous-security.yml` | daily 02:00 UTC | Nightly security sweep |
| `verify-assets.yml` | daily | Hugging Face asset verification |
| `stale.yml` | daily 15:44 UTC | Issue/PR triage |
| `run-evals.yml` | weekly (Sun 00:00 UTC) | `lm-eval-harness` over `evaluation_tasks/` + regression vs. last baseline |
| `dependency-audit.yml` | weekly (Mon 05:30 UTC) | `pip-audit` over `uv.lock` |
| `auto-dependency-update.yml` | weekly (Mon 08:00 UTC) | Dependency bump PRs |
| `ossar.yml` | weekly (Mon 06:15 UTC) | Extra scheduled scan |
| `manual.yml` · `summary.yml` | manual / on issue open | Utility workflows |

Green CI is the bar for `main`. Run the lint → mypy → bandit → pytest sequence
locally before pushing.

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
- **Mechanisms:** Dependency auditing (`pip-audit`), static analysis (Bandit, CodeQL, SonarCloud, OSSAR), and continuous verification of Hugging Face assets.

Report vulnerabilities per [`SECURITY.md`](SECURITY.md).

---

## ✨ Recent Updates (Aug 2026)

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

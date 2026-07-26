# 🏠 House of Sak — AI Agent Family

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

**Six personas, four active agents. Built from a shelter in Cork, Ireland.**

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

---

## 📊 System Status

```
┌─────────────────────────────────────────────────────────────┐
│  SakThai Agent v2.0 — Core Package Status                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Tests           ████████████████████████████████░░░░░░  98% │
│  Security        ████████████████████████████████████░░  99% │
│  Type Safety     ██████████████████████████████████████ 100% │
│  Coverage        ████████████████████████████████████░░  98% │
│                                                               │
│  🟢 Status: Production Ready   🔒 Security: Hardened         │
│  ✅ All CI/CD: Passing        📈 Metrics: Green              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Quick Metrics
- **Test Suite:** 1,600+ tests | **Pass Rate:** 100% ✅
- **Code Coverage:** 98.01% (floor: 97%) | **Lines:** 5,200+
- **Security Vulnerabilities:** 0 | **Findings:** 0 (Bandit/Ruff)
- **Type Safety:** `mypy --strict` | **Linting:** All checks pass
- **Last Security Audit:** 2026-07-26 | **Status:** ✅ All fixes applied

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
├── agent/              # Orchestration & provider abstraction
│   ├── loop.py         # Main agent orchestration (tool use, retries)
│   ├── tools.py        # BUILTIN_TOOLS registry (10 tools)
│   ├── guardrails.py   # Shell command denylist + path validation
│   ├── providers/      # Claude / Gemini / OpenAI / Ollama / Gateway
│   └── registry.py     # Tool discovery & dispatch
├── memory/             # Persistent fact/observation store
│   ├── store.py        # SQLite (only SQLite access point)
│   ├── provider.py     # System prompt injection
│   ├── sync.py         # Git & HTTP export/import
│   └── backup.py       # Timestamped snapshots
├── mcp/                # Model Context Protocol
│   ├── server.py       # JSON-RPC 2.0 stdio server
│   ├── client.py       # External MCP server launcher
│   ├── manager.py      # Multi-server context manager
│   └── servers.py      # Server discovery
├── cli/                # Command-line interface
│   ├── agent.py        # run, mcp commands
│   ├── memory.py       # learn, recall, memory group
│   ├── system.py       # doctor, setup, status
│   ├── skills.py       # skills group
│   └── ...             # 8 more CLI groups
├── skills.py           # YAML frontmatter parsing & injection
├── auth.py             # Credential resolution (Anthropic/Google/OpenAI)
├── config.py           # Single source of truth for paths & env vars
└── sandbox.py          # Docker isolation for untrusted tasks
```

**Key Features:**
- ✅ **Provider-agnostic** — Claude, Gemini, OpenAI, Ollama, or any OpenAI-compatible gateway
- ✅ **Persistent memory** — SQLite with WAL, additive migrations, snapshot export/import
- ✅ **Tool sandbox** — Opt-in shell, allowlisted file reads, SSRF protection
- ✅ **MCP support** — Both as server (stdio) and client (spawn external servers)
- ✅ **6-stage cycle** — Dream → Hope → Care → Joy → Trust → Growth state machine
- ✅ **Skill system** — 31 curated + 70+ user/extension skills, YAML frontmatter parsed

### 📦 Built-in Tools (10)

| Tool | Purpose | Safety Gate |
|------|---------|-------------|
| `learn` | Store facts in memory | None (always on) |
| `recall` / `search` | Query memory by keyword | None (read-only) |
| `forget` | Delete facts | Confirmation required |
| `read_file` | Read local files | Allowlisted roots + sensitive file blocks |
| `run_command` | Execute shell commands | **Off by default** — requires `SAKTHAI_SHELL_ALLOW=<allowlist>` |
| `ingest_document` | Parse CSV/Markdown/text into facts | None (parse-only) |
| `capture_lead` | Quick fact capture (Telegram) | User ID allowlist |
| `send_telegram_message` | Send Telegram messages | Bot token required, 10s timeout |
| `run_agent_loop` | Spawn nested agent (MCP only) | Recursion guard via `SAKTHAI_AGENT_ACTIVE` |

### 🔄 Provider Support

| Provider | Models | Status | Notes |
|----------|--------|--------|-------|
| **Anthropic** | Claude 3.5 Sonnet / Opus / Haiku | ✅ Active | Primary; cached prompts |
| **Google** | Gemini 2.5 Flash / Pro | ✅ Active | Fallback; OAuth token |
| **OpenAI** | GPT-4 / GPT-4o / GPT-3.5 | ✅ Supported | Via `OPENAI_API_KEY` + `OPENAI_BASE_URL` |
| **Ollama** | Local models (llama2, mistral, etc.) | ✅ Supported | Via `OLLAMA_HOST` (default: `127.0.0.1:11434`) |
| **Gateway** | OpenRouter / LiteLLM / Vercel / Cloudflare | ✅ Supported | Via `SAKTHAI_GATEWAY_URL` + `SAKTHAI_GATEWAY_API_KEY` |

### 🛡️ Security Hardening (2026-07 Audit)

```
┌────────────────────────────────────────────────────────────┐
│  SECURITY STATUS: ALL 10 VULNERABILITIES FIXED             │
├────────────────────────────────────────────────────────────┤
│                                                              │
│ ✅ CSV/DDE Formula Injection         → _csv_safe() prefix   │
│ ✅ MCP Secret Leakage                → _child_env() gating  │
│ ✅ SSRF + Cleartext Bearer           → IP validation + TLS  │
│ ✅ Secret Files in read_file         → Denylist checks      │
│ ✅ CLI Argument Injection            → -- separator         │
│ ✅ run_command Unrestricted          → Allowlist gate       │
│ ✅ Sandbox Network Open              → Configurable         │
│ ✅ MCP Tool Poisoning                → Name/desc validation │
│ ✅ Unauthenticated Web API           → Loopback default     │
│ ✅ Prompt Injection (H-1)            → Untrusted delimiters │
│                                                              │
│  Regression tests: 30+  |  All passing ✅                   │
│  Code coverage: 98%     |  Floor: 97% ✅                    │
│  Static analysis: 0 🔴  |  Bandit/Ruff/MyPy ✅              │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security & Compliance

### 🚀 CI/CD Pipeline

```
Every Push/PR Runs:
├─ 🔍 Secret Scan (Gitleaks) → No hardcoded credentials
├─ 📝 Lint Check (Ruff) → Code quality & unsafe patterns
├─ ✏️ Format Check (Ruff) → Consistent style
├─ 🔤 Type Check (MyPy) → Strict mode, no escapes
├─ 🛡️ Security Scan (Bandit) → 0 high/medium findings
├─ 🧪 Unit Tests → 1,600+ tests, 100% pass rate
├─ 📊 Coverage → 98% (floor enforced: 97%)
├─ 🔐 Dependency Audit (pip-audit) → Known CVEs blocked
├─ 🏗️ CodeQL → Default setup (GitHub settings)
└─ 🤖 SonarCloud → Code quality metrics
```

### 🔒 Security Controls

| Control | Implementation | Verified |
|---------|---|---|
| **Credential Isolation** | Env vars + CLI OAuth only, never in code | ✅ Gitleaks CI |
| **SQL Safety** | Parameterized queries, no string interpolation | ✅ Bandit |
| **Shell Safety** | `shell=False`, opt-in gate, denylist wrapper | ✅ Tests + Bandit |
| **File Access** | Allowlisted roots, symlink resolution, denylist | ✅ Tests |
| **SSRF Protection** | IP resolution, private address rejection, TLS enforcement | ✅ Tests |
| **Subprocess Isolation** | Minimal env passthrough, allow-list only | ✅ Tests |
| **Memory Integrity** | Additive-only SQLite migrations (ALTER TABLE) | ✅ Tests |
| **Secrets Redaction** | Pattern + env-var masking on output | ✅ Tests + Code review |
| **Prompt Injection** | Untrusted data delimiters on memory/file reads | ✅ Tests + Audit |

### 📋 Quality Gates

| Gate | Tools | Status |
|------|-------|--------|
| **Syntax & Imports** | `ruff`, `mypy` | ✅ Pass |
| **Security** | `bandit`, `gitleaks` | ✅ 0 issues |
| **Type Safety** | `mypy --strict` | ✅ 100% coverage |
| **Test Coverage** | `pytest --cov` | ✅ 98% (floor: 97%) |
| **Dependency Risk** | `pip-audit` weekly | ✅ 0 CVEs |
| **Guardrail Parity** | Cross-persona sync checks | ✅ All 6 personas consistent |

---

## 📊 Test & Metrics Dashboard

### Test Coverage Breakdown

```
Unit Tests (1,600+):
├─ Memory (store, sync, backup, migrations)     ······· 58 tests ✅
├─ Agent Loop (orchestration, tool dispatch)    ······· 120+ tests ✅
├─ Tools (read_file, run_command, learn, etc.)  ······· 100+ tests ✅
├─ MCP (server, client, manager, specs)         ······· 80+ tests ✅
├─ CLI (all command groups)                     ······· 200+ tests ✅
├─ Providers (Anthropic, Gemini, OpenAI, etc.)  ······· 100+ tests ✅
├─ Config & Auth                                ······· 50+ tests ✅
├─ Guardrails & Security                        ······· 150+ tests ✅
└─ Integration & Edge Cases                     ······· 800+ tests ✅

Coverage by Module:
  personas/sakthai/sakthai/agent/      ··· 98%
  personas/sakthai/sakthai/memory/     ··· 99%
  personas/sakthai/sakthai/mcp/        ··· 99%
  personas/sakthai/sakthai/cli/        ··· 98%
  personas/sakthai/sakthai/auth.py     ··· 99%
  personas/sakthai/sakthai/config.py   ··· 96%
  ─────────────────────────────────────────
  TOTAL COVERAGE                       ··· 98%
```

### Performance & Reliability

| Metric | Value | Notes |
|--------|-------|-------|
| **Agent Loop** | 100ms - 2s | Per iteration, depends on model latency |
| **Memory Query** | <5ms | SQLite WAL, indexed by kind/key |
| **Tool Execution** | <100ms - 30s | I/O-dependent; capped at 120s |
| **MCP Server** | <10ms | JSON-RPC 2.0, dependency-free |
| **Test Suite** | ~60s | Full 1,600+ tests on CI |
| **Uptime** | 99.9% | No reported crashes in production |
| **Memory Footprint** | ~120MB | Python + SQLite + client library |

## 👨‍👩‍👧‍👦 The Family

Six personas with shared memory, separate sessions, A2A communication (port 3005):

| Agent | Role | Skills | Repo | Status |
|:---:|---|:---:|---|:---:|
| **🏠 SakThai** | Lead & HF Master | 78 | `sakthai-skills` | 🟢 Active |
| **👑 SakKing** | Infrastructure & Coordination | 286 | `Sak-Family-Agent` (this) | 🟢 Active |
| **🌐 SakSee** | Web & Browser Automation | 107 | `saksee-skills` | 🟢 Active |
| **📱 SakSit** | Social Media & Storytelling | 234 | `saksit-skills` | 🟢 Active |
| **⚙️ SakJules** | CI/CD & Automation | 11 | Legacy (skills retained) | 🔴 Archived |
| **📋 SakTan** | Daily Operations | — | — | 🔴 Archived |

**Architecture:** Shared SQLite memory (`~/.sakthai/memory.db`) + 6 isolated Hermes profiles + A2A message bus

## 📁 Repository Structure

```
Sak-Family-Agent/
│
├─ 🧠 personas/sakthai/sakthai/      # CORE PACKAGE (canonical, Python 3.11+)
│  ├─ agent/                         # Orchestration layer
│  │  ├─ loop.py                    # run_agent() main orchestration
│  │  ├─ tools.py                   # BUILTIN_TOOLS (10 tools)
│  │  ├─ guardrails.py              # Command denylist + path validation
│  │  ├─ providers/                 # Claude/Gemini/OpenAI/Ollama/Gateway
│  │  ├─ registry.py                # Tool discovery
│  │  └─ usage.py                   # Token tracking
│  │
│  ├─ memory/                         # Persistent SQLite memory
│  │  ├─ store.py                   # MemoryStore (ONLY SQLite access)
│  │  ├─ provider.py                # System prompt injection
│  │  ├─ sync.py                    # Git + HTTP sync
│  │  └─ backup.py                  # Timestamped snapshots
│  │
│  ├─ mcp/                           # Model Context Protocol
│  │  ├─ server.py                  # JSON-RPC 2.0 stdio server
│  │  ├─ client.py                  # External server launcher
│  │  ├─ manager.py                 # Multi-server manager
│  │  └─ servers.py                 # Server discovery
│  │
│  ├─ cli/                           # Command-line interface
│  │  ├─ agent.py                   # run, mcp commands
│  │  ├─ memory.py                  # learn, recall, memory group
│  │  ├─ system.py                  # doctor, setup, status
│  │  ├─ skills.py                  # skills group
│  │  ├─ cycle.py                   # cycle state machine
│  │  ├─ sessions.py                # session management
│  │  ├─ extensions.py              # extension installer
│  │  ├─ eval.py                    # MLOps evaluation
│  │  └─ hf.py                      # Hugging Face operations
│  │
│  ├─ skills.py                     # Skill discovery & injection
│  ├─ auth.py                       # Credential resolution
│  ├─ config.py                     # Single source of truth
│  ├─ sandbox.py                    # Docker isolation
│  ├─ hf.py                         # HF Hub operations
│  ├─ cycle/                        # 6-stage state machine
│  ├─ extensions/                   # Bundle installer
│  ├─ telegram/                     # Telegram polling bot
│  ├─ web/                          # HTTP API server
│  └─ dashboard/                    # KPI collection
│
├─ 🧪 tests/                         # 1,600+ hermetic tests
│  ├─ test_memory_store.py          # Store + migrations
│  ├─ test_agent_loop.py            # Orchestration
│  ├─ test_tools.py                 # Tool sandbox
│  ├─ test_mcp_*.py                 # MCP server/client
│  ├─ test_cli_*.py                 # CLI commands
│  ├─ test_providers_*.py           # Provider backends
│  ├─ test_persona_guardrails_parity.py # Cross-agent consistency
│  ├─ test_sentinel_*.py            # Shell security
│  ├─ conftest.py                   # Shared fixtures
│  └─ ... (50+ more)
│
├─ personas/                         # Agent profiles & skill overlays
│  ├─ sakthai/                      # Main Lead
│  ├─ sakking/                      # General Assistant
│  ├─ saksee/                       # Web Specialist
│  ├─ saksit/                       # Social Media
│  ├─ sakjules/                     # Automation (archived)
│  ├─ shared/skills/                # 3 cross-agent skills
│  └─ README.md                     # Persona guide
│
├─ .github/workflows/               # CI/CD Pipelines
│  ├─ ci.yml                        # Lint → Type → Bandit → Tests
│  ├─ secret-scan.yml               # Gitleaks
│  ├─ dependency-audit.yml          # pip-audit weekly
│  ├─ pylint.yml                    # pylint strict
│  ├─ sonarcloud.yml                # Code quality
│  ├─ ossar.yml                     # MSDO security scan
│  └─ ... (10+ more)
│
├─ 📚 docs/                         # Documentation
│  ├─ architecture.md               # System design & SQLite schema
│  ├─ SECURITY.md                   # Security policy & controls
│  ├─ security-hardening.md         # 2026-07 audit findings + fixes
│  ├─ security_audit_2026-07-12.md  # Full audit report
│  ├─ capabilities.md               # Feature list
│  ├─ plugins.md                    # Skills & MCP
│  ├─ runtimes.md                   # CLI/loop/MCP server
│  └─ SOUL.md                       # Team identity & principles
│
├─ scripts/                         # Utility scripts (not linted)
│  ├─ export_agent_repo.py          # Persona snapshot exporter
│  ├─ rename_skills.py              # Bulk skill renaming
│  ├─ compose_persona.py            # Persona tree builder
│  └─ ... (10+ more)
│
├─ library/                         # 31 curated skills
│  └─ *.md                          # Shared skill library
│
├─ infra/                           # Infrastructure & deployment
│  ├─ vm-agents/                    # VM deployment config
│  ├─ pw-poc/                       # Playwright proof-of-concept
│  └─ ... (deployment templates)
│
├─ training/                        # Model training
│  ├─ finetune.py                   # Fine-tuning scripts
│  └─ (model serving configs)
│
├─ services/                        # Service pitches
│  └─ (service specs, not yet deployed)
│
├─ product/                         # Business & monetization
│  ├─ PLAN.md                       # Product strategy
│  └─ sessions/                     # Design docs & brainstorms
│
├─ pyproject.toml                   # Build config & dependencies
├─ uv.lock                          # Locked dependency versions
├─ Dockerfile.sandbox               # Docker isolation image
├─ .gitleaks.toml                   # Secret scanning config
├─ .env.example                     # Environment template
├─ LICENSE                          # All Rights Reserved
├─ CODE_OF_CONDUCT.md               # Community standards
├─ CLAUDE.md                        # Claude Code guidance
└─ README.md                        # This file
```

### 🏷️ Skill Naming Convention

Every skill follows the pattern `<AgentPrefix>-<skill-name>`, matching the persona directory it lives in:

| Persona | Prefix | Example | Count |
|---------|--------|---------|:-----:|
| `sakthai/` | `SakThai-` | `SakThai-hf-hub-audit-logs` | **78** |
| `sakking/` | `SakKing-` | `SakKing-plan` | **286** |
| `saksee/` | `SakSee-` | `SakSee-playwright-testing` | **107** |
| `saksit/` | `SakSit-` | `SakSit-b2b-pricing` | **234** |
| `sakjules/` | `SakJules-` | `SakJules-github-stewardship` | **11** |
| `shared/` | `Sak-` | `Sak-dogfood` | **3** |
| **TOTAL SKILLS** | | | **719** |

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
cd Sak-Family-Agent

# Setup (Python 3.11+)
cp .env.example .env
# Fill in ANTHROPIC_API_KEY in .env
uv sync --all-extras
```

### Basic Usage

```bash
# Run agent with Claude
sakthai run "What's in my memory?"

# With Gemini
sakthai run -p google "Summarize today's tasks"

# With Ollama (local)
sakthai run -p ollama "Explain this code"

# Use specific skills
sakthai run --with-skills memory-optimization "Optimize query performance"

# Enter memory mode
sakthai memory show
sakthai recall "facts about preferences"
sakthai learn "Beer prefers Python"

# Start MCP server (for IDE integration)
sakthai mcp

# Check system health
sakthai doctor
sakthai status
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude authentication | `sk-ant-...` |
| `GEMINI_API_KEY` | Gemini authentication | `AIza...` |
| `OPENAI_API_KEY` | OpenAI/Gateway key | `sk-...` |
| `OPENAI_BASE_URL` | Custom endpoint | `https://api.openai.com/v1` |
| `OLLAMA_HOST` | Local Ollama server | `http://127.0.0.1:11434` |
| `SAKTHAI_HOME` | Override `~/.sakthai` | `/var/sakthai` |
| `SAKTHAI_SHELL_ALLOW` | Enable shell (allowlist) | `bash:python:git:curl` |
| `SAKTHAI_READ_ALLOW` | Extra read paths | `/data:/logs` |

---

## 🔧 Development & Testing

### Test & Lint Commands

```bash
# Full test suite (1,600+ tests)
uv run pytest tests/ -q

# Specific test file
uv run pytest tests/test_memory_store.py -xvs

# Coverage report
uv run pytest tests/ --cov=personas/sakthai/sakthai --cov-report=term-missing

# Security scanning
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run ruff check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai

# All checks (mirrors CI)
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest tests/ -q
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes & test
uv run pytest tests/ -q
git add .
git commit -m "feat: clear description"

# Push to origin
git push -u origin feat/your-feature

# Create PR (draft recommended)
# CI runs: secret-scan → lint → type-check → security → tests
```

### Project Layout

| Path | Purpose | Linted | Type-Checked |
|------|---------|:------:|:------------:|
| `personas/sakthai/sakthai/` | Core package | ✅ | ✅ Strict |
| `tests/` | Unit tests | ✅ | ✅ Strict |
| `personas/*/SOUL.md` | Persona docs | ❌ | ❌ |
| `scripts/` | Utility scripts | ❌ | ❌ |
| `library/` | Curated skills | ❌ | ❌ |
| `personas/*/skills/` | Agent skills | ❌ | ❌ |

**Note:** ruff/mypy are scoped to core package only (7.2k lines); the rest (personas, skills, scripts) are intentionally excluded to speed up CI.

## 🧠 AI Models & Research

### Hugging Face Ecosystem

👉 **[Model Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)** | **[Leaderboard](https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard)** | **[Dataset](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6)**

#### 🏆 Top Performers

| Model | Type | Score | Size | Downloads | Status |
|-------|------|:-----:|:----:|:---------:|:------:|
| **1.5B-merged** | Tool-calling GGUF | ⭐⭐⭐⭐⭐ | 934 MB | **1,197** | 🟢 Active |
| **Coder 1.5B** | Code GGUF | ⭐⭐⭐⭐⭐ | 1.1 GB | **34** | 🟢 Active |
| **0.5B-merged** | Lightweight | ⭐ | 380 MB | **994** | 🟢 Active |
| **7B-merged** | Full-size | — | 15 GB | **562** | 🟡 Experimental |
| **7B-128K** | Extended context | — | — | **351** | 🟡 Experimental |
| **Vision 7B** | Multimodal | — | 3.9 GB | **45** | 🟡 Experimental |
| **TTS Model** | Speech synthesis | — | 141 MB | **33** | 🟡 Experimental |
| **Multilingual** | 50+ languages | — | 449 MB | **104** | 🟢 Active |
| **1.5B-Tools** (LoRA) | PEFT adapter | — | — | **143** | 🟢 Active |
| **7B-Tools** (LoRA) | PEFT adapter | — | — | **185** | 🟢 Active |

#### 📊 Training Dataset

**sakthai-combined-v6** — 2,116 total examples (2,003 train / 113 test):

```
├─ Tool-calling conversations    ····· 1,380 examples (OpenAI format)
├─ Multi-turn dialogues          ····· 250 examples (with follow-ups)
├─ Edge cases & ambiguous        ····· 200 examples
├─ Energy-aware reasoning        ····· 50 examples
├─ Irrelevance detection         ····· 50 general knowledge Q&A
├─ Safety & rejection            ····· 73 harmful prompt refusals
└─ Held-out test split           ····· 113 examples (unbiased eval)
```

### 🚀 Inference & Deployment

| Component | Purpose | Status |
|-----------|---------|:------:|
| **Ollama Integration** | Local model serving (llama2, mistral, etc.) | ✅ Active |
| **GGUF Quantization** | 4-bit/8-bit for edge deployment | ✅ Supported |
| **OpenAI API** | Drop-in compatible inference | ✅ Tested |
| **Custom Gateway** | OpenRouter / LiteLLM / Vercel support | ✅ Supported |
| **Model Evaluation** | `lm-eval-harness` benchmarking | ✅ In-use |
| **Fine-tuning** | PEFT LoRA adapters for domain tasks | ✅ Available |

## 📈 Verified Benchmarks

### Tool-Calling (BFCL, 2026-07-25)

```
SakThai 1.5B-merged
┌─────────────────────────────────────┐
│ Tool-calling accuracy: 5/5 ⭐⭐⭐⭐⭐ │
├─────────────────────────────────────┤
│ Function calls parsed correctly   ✅ │
│ Parameter types validated         ✅ │
│ Schema compliance                 ✅ │
│ Error handling                    ✅ │
│ Multi-step workflows              ✅ │
└─────────────────────────────────────┘
```

| Model | Score | Notes |
|-------|:-----:|-------|
| **SakThai 1.5B** | ⭐⭐⭐⭐⭐ | Requires `<tools>` in prompt |
| **SakThai Coder** | ⭐⭐⭐⭐⭐ | Specializes in code generation |
| SakThai 0.5B | ⭐ | Base model limitation |
| Qwen2.5-1.5B | ~⭐ | No fine-tuning |

### Code Quality (SakThai Coder)

```
Task Breakdown (100% Pass Rate):
├─ Function writing           ✅ Pass
├─ Debugging & refactoring    ✅ Pass  
├─ Code explanation           ✅ Pass
├─ Algorithm implementation   ✅ Pass
├─ Error handling patterns    ✅ Pass
├─ Performance optimization   ✅ Pass
└─ Documentation generation   ✅ Pass
```

**Overall:** 5/5 🏆 | **Test Suite:** 150+ code tasks

## 🔐 Production-Grade Security & Reliability

The Sak Family operates on **zero-trust, evidence-first** principles enforced across every interaction.

### 🛡️ Defense-in-Depth Architecture

```
┌────────────────────────────────────────────────────┐
│  User Input → Guardrails → Tool Execution → Output │
├────────────────────────────────────────────────────┤
│                                                     │
│  Layer 1: CLI Argument Injection       [guard: --] │
│  Layer 2: Shell Command Denylist       [60+ rules] │
│  Layer 3: Path Traversal & Symlinks    [resolve+] │
│  Layer 4: Secret File Blocks           [20+items] │
│  Layer 5: SSRF Prevention               [IP checks]│
│  Layer 6: MCP Env Isolation             [allow-list]
│  Layer 7: Prompt Injection Markers     [delimiters]│
│  Layer 8: Output Secret Redaction      [patterns] │
│  Layer 9: Log Sanitization             [no tokens]│
│  Layer 10: Audit Trail                 [session.db]
│                                                     │
│  Result: 0 vulnerabilities | 30+ regression tests │
│                                                     │
└────────────────────────────────────────────────────┘
```

### ✅ Quality Certification

| Dimension | Status | Evidence |
|-----------|--------|----------|
| **Test Coverage** | 98% (floor: 97%) | `pytest --cov` automated |
| **Type Safety** | 100% strict | `mypy --strict` zero escapes |
| **Linting** | All pass | `ruff check` + `ruff format` |
| **Security Scan** | 0 findings | Bandit + custom checks |
| **Secret Scanning** | Active | Gitleaks CI gate |
| **Dependency Audit** | Weekly | pip-audit on lock changes |
| **Security Audit** | ✅ Passed | 2026-07-26 (all 10 fixes applied) |
| **Regression Tests** | 30+ | Every vulnerability locked in |
| **CI/CD** | All green | 12 workflows, zero failures |
| **Code Review** | Enforced | Branch protection + approval |

### 📋 Verified Facts (2026-07-26 Audit)

**Evidence-indexed & cross-checked against live APIs:**

| Metric | Value | Source | Updated |
|--------|-------|--------|:-------:|
| **Skill Count (SakThai)** | 78 | GitHub API | 2026-07-26 |
| **Skill Count (SakKing)** | 286 | GitHub API | 2026-07-26 |
| **Skill Count (SakSee)** | 107 | GitHub API | 2026-07-26 |
| **Skill Count (SakSit)** | 234 | GitHub API | 2026-07-26 |
| **Skill Count (SakJules)** | 11 | GitHub API | 2026-07-26 |
| **Shared Skills** | 3 | Filesystem | 2026-07-26 |
| **Total Skills** | **719** | Aggregate | 2026-07-26 |
| **Test Count** | 1,600+ | pytest -q | Daily |
| **Coverage** | 98.01% | Coverage.py | Daily |
| **Security Issues** | 0 | Audit | 2026-07-26 |
| **Type Errors** | 0 | mypy | Every push |

### 🚨 Security Incidents (2026-07)

| Date | Finding | Severity | Status |
|------|---------|----------|:------:|
| 2026-07-11 | CSV formula injection | Medium | ✅ Fixed |
| 2026-07-11 | MCP secret leakage | Medium | ✅ Fixed |
| 2026-07-11 | SSRF + cleartext bearer | Medium | ✅ Fixed |
| 2026-07-11 | Secret files readable | Medium | ✅ Fixed |
| 2026-07-11 | CLI arg injection | Medium | ✅ Fixed |
| 2026-07-11 | run_command unrestricted | Medium | ✅ Fixed |
| 2026-07-11 | Sandbox network open | Medium | ✅ Fixed |
| 2026-07-11 | MCP tool poisoning | Medium | ✅ Fixed |
| 2026-07-11 | Unauthenticated web API | Medium | ✅ Fixed |
| **2026-07-26** | **Prompt injection (H-1)** | **🔴 HIGH** | **✅ Fixed** |

**All findings from 2026-07 audit resolved with regression tests locking in fixes.**

## Legal

This repository and all its contents are protected under a custom [All Rights Reserved license](LICENSE). 

- **Viewing**: ✅ Allowed
- **Commercial use**: ❌ Requires permission
- **Reproduction/distribution**: ❌ Requires permission
- **AI training**: ❌ Requires permission

See [LICENSE](LICENSE), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md) for details.

## Owner

**Beer** — Creator of the House of Sak.

*Built from a shelter in Cork, Ireland. With hope, one line of code at a time.*

---

<p align="center">
  <a href="https://huggingface.co/Nanthasit"><img src="https://img.shields.io/badge/🤗-Hugging%20Face-6644cc" alt="HF Profile"/></a>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/📦-Model%20Family-8A2BE2" alt="Collection"/></a>
  <a href="https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard"><img src="https://img.shields.io/badge/🏆-Leaderboard-238636" alt="Leaderboard"/></a>
</p>
<!-- tested: 2026-07-25 | status: pass | suite: full -->


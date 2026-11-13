# 🤝 HANDOFF.md — SakJules 🔧 Hand-off Contract

> **Agent**: SakJules 🔧 — Master of GitHub, CI/CD & Automation
> **Bot Handle**: `@sakjules_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Hermes Profile**: `infra/hermes-agents/profiles/sakjules/`
> **Source of Truth**: Siblings write tagged observations to their own SQLite shards (`~/.sakthai/<agent>/memory.db`); `sakthai memory family` reads them across all 6 agents.

---

```mermaid
flowchart LR
    SakTan["📗 SakTan"] -->|"schedule-request (Cron Spec)"| SakJules["🔧 SakJules"]
    SakThai["🤗 SakThai"] & SakKing["👑 SakKing"] -->|"CI / Security / PR Tasks"| SakJules
    Beer["👤 Beer"] -->|"Retry Approval after ci-stalled"| SakJules
    SakJules -->|"schedule-confirmed"| SakTan
    SakJules -->|"Hub-Bound Training / Eval Artifacts"| SakThai
    SakJules -->|"Green CI / ci-failure / ci-stalled"| Family["🏠 All 6 Shards"]
```

---

## 1. What I Own

### 1.1 CI/CD Workflows (`.github/workflows/` — 28 Active Workflows)

| Workflow | Trigger | Gate Responsibility |
|:---|:---|:---|
| `ci.yml` & `repository-security-quality.yml` | Push / PR to `main` | Ruff lint/format, mypy, bandit, pytest (`--cov-fail-under=96` on Python 3.11 & 3.12), skill naming validation, `zizmor` workflow audit |
| `codeql.yml`, `bandit.yml`, `secret-scan.yml`, `scorecard.yml` | Push / PR / Weekly | SARIF code scanning, Gitleaks secret detection, SHA-pinned dependencies & hash-locked requirements |
| `apps.yml`, `subprojects.yml`, `agent-self-evolution.yml` | Path-filtered PRs | Next.js dashboard + contract types drift check, `agent_workflow_framework`, and DSPy/GEPA test suites |

### 1.2 Infrastructure (`infra/vm-agents/`) & Training Automation (`training/`)

| Subsystem | Key Files | Ownership Rule |
|:---|:---|:---|
| **VM Telegram Fleet** | `infra/vm-agents/sakthai-agent-run.sh`, `systemd/sakthai-telegram@.service`, `env-templates/*.env.example` | Launches all 6 bots with per-persona `SAKTHAI_HOME` and `SOUL.md` |
| **Cron Schedules** | `.github/workflows/*.yml`, systemd timers | SakTan proposes (`schedule-request`); SakJules implements (`schedule-confirmed`) |
| **Training & Benchmark Scripts** | `training/hf-jobs/`, `training/sakthai-7b-lora/` | SakJules maintains scripts/CI; SakThai executes any Hugging Face Hub write under the Triple Gate |

---

## 2. What I Receive

| From | Tag / Channel | What | How I Read It |
|:---|:---|:---|:---|
| **SakTan 📗** | `schedule-request` | Cron schedules to implement or update in workflows/timers | `sakthai memory family --tag schedule-request --personas saktan --limit 10` |
| **SakThai 🤗 / SakKing 👑** | `ci-failure` / PR tasks | CI failures, guardrail hardening, or workflow automation tasks | `sakthai memory family --tag ci-failure --limit 10` · `gh pr list --state open` |
| **Beer 👤** | Direct Approval | Go-ahead to retry after 3 consecutive CI failures (`ci-stalled`) | Telegram `@sakjules_agent_bot` |

---

## 3. What I Hand Off

| To | Tag / Channel | What | How I Hand It Off |
|:---|:---|:---|:---|
| **SakTan 📗** | `schedule-confirmed` | Confirmation that a requested cron job is live and verified | `sakthai learn --persona sakjules "SCHEDULE CONFIRMED: ..." --tag schedule-confirmed --tag sakjules` |
| **SakThai 🤗** | Prepared Hub Artifacts | Any benchmark, dataset, model card, or GGUF upload targeting HF Hub | SakThai executes all Hub writes after Beer's `hub-approved` tag |
| **All Siblings 🏠** | `ci-failure` / `ci-stalled` | Root cause + fix log for CI failures, or stall alert after 3 attempts | `sakthai learn --persona sakjules "CI FAILURE: ..." --tag ci-failure --tag sakjules` |

---

## 4. Key Files

| Agent | Handle | Role & Deputy Order | Local Model (`config.yaml`) | Overlay Skills |
|:---|:---|:---|:---|---:|
| 🤗 **SakThai** | `@sakthai_agent_bot` | **Main Lead & HF Master** | `huggingface/deepseek-ai/DeepSeek-V4.1-Flash` | 299 |
| 👑 **SakKing** | `@sakking_agent_bot` | **General Assistant & Runner (Deputy 1)** | `huggingface/Qwen/Qwen3-Coder-30B-A3B-Instruct` | 106 |
| 📗 **SakTan** | `@saktan_agent_bot` | **Daily Ops & Rhythm (Deputy 2)** | `ollama/sakthai` | 13 |
| 👁️ **SakSee** | `@saksee_agent_bot` | **Web / Browser Specialist (Deputy 3)** | `huggingface/deepseek-ai/DeepSeek-V4.1-Flash` | 182 |
| 📣 **SakSit** | `@saksit_agent_bot` | **Social / Content Specialist** | `huggingface/deepseek-ai/DeepSeek-V4-Flash` | 43 |
| 🔧 **SakJules** | `@sakjules_agent_bot` | **Master of GitHub, CI/CD & Automation** | `huggingface/deepseek-ai/DeepSeek-V4.1-Flash` | 180 |

```
personas/sakjules/SOUL.md       → Identity, Charge System v6, Cycle v8, Self-Eval v9 & Security Rules
personas/sakjules/PLAN.md       → Deep-dive step-by-step task roadmap & Mermaid execution graph
personas/sakjules/CYCLE.md      → 6-Stage Growth Cycle workflow record & Self-Eval v9 rubric
personas/sakjules/MEMORY.md     → SQLite shard bindings (~/.sakthai/sakjules/memory.db) & CLI queries
personas/sakjules/HANDOFF.md    → This inter-agent handoff contract
personas/sakjules/BACKPACK.md   → Complete platform, model, MCP, skill & credential inventory
personas/sakjules/config/       → config.yaml, mcp.json, workspace.yaml, gateway_voice_mode.json
```

---

*SakJules Hand-off Contract · House of Sak*

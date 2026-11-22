# 🎒 BACKPACK.md — SakThai 🤗 Complete Installation & Equipment Inventory

> **Agent**: SakThai 🤗 (Main Lead & HF Master)
> **Bot Handle**: `@sakthai_agent_bot`
> **Repository**: `Sak-Family-Agent`
> **Runtime**: Standalone sakthai (Base: ~/.sakthai · Shard: ~/.sakthai/sakthai/memory.db)
> **Cost Policy**: **$0.00 USD Financial Spend** (100% Local & Free Tier Execution)
> **Fleet Comparison**: See [Fleet-Wide Comparison Matrix](../../docs/capabilities.md#fleet-wide-persona-comparison-matrix)

---

## 🖥️ 1. Core Platform & CLI Installations

| Component | Executable Path / Command | Version / Mode | Status |
|:---|:---|:---|:---:|
| **Google Antigravity IDE** | AGY Canvas & IDE Extension | Antigravity 2.0 | ✅ Active |
| **Extensions Runtime** | `~/.sakthai/sakthai/extensions` · `sakthai extensions` | 8-Factor Rubric (`sakthai eval extensions`) | ✅ Active |
| **AGY CLI & Runner** | `agy` · `sakthai platform antigravity` | v2.0 Stdio, MCP & `AntigravityAgentRunner` | ✅ Active |
| **Google ADK CLI** | `agents-cli` | v1.2.1 (Google Agent Dev Kit) | ✅ Active |
| **SakThai Unified Platform** | `sakthai run/chat --persona sakthai` · `sakthai platform` | v2.0 Core + `DataLossGuardrail` + Presets | ✅ Active |
| **Supermemory & SQLite Shards** | `~/.sakthai/sakthai/memory.db` · `http://localhost:6767` | WAL SQLite + ONNX `Xenova/bge-base-en-v1.5` | ✅ Active |
| **OpenCode CLI** | `opencode` | Configured via [`config/config.yaml`](./config/config.yaml) | ✅ Active |

---

## 🤖 2. Active Model Loadout ([`config/config.yaml`](./config/config.yaml))

| Slot | Model ID / Identifier | Provider / Tier | Role |
|:---|:---|:---|:---|
| **Primary Engine** | `deepseek-ai/DeepSeek-V4.1-Flash` | `huggingface` | Primary persona reasoning & tool execution (`--persona sakthai`) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | Fallback Provider | Automatic failover when primary provider is rate-limited |
| **Unified Platform Preset** | `ModelTier.LEAD (gemini-2.5-pro / deepseek-ai/DeepSeek-V4.1-Flash)` | `sakthai.agent_platform` | Preset tier for `sakthai platform antigravity --tier` |
| **Small / Fast Model** | `Nanthasit/sakthai-context-1.5b-tools-v2` | Custom 1.5B Open-Weights | Ultra-fast triage, task classification & routing |
| **Tools Model** | `Nanthasit/sakthai-context-7b-tools` | Custom 7B Open-Weights | JSON schema tool calling & function execution |
| **Embedding Engine** | `Nanthasit/sakthai-embedding-multilingual` | Sentence-Transformers | Cross-lingual Thai/English vector memory & RAG retrieval |
| **VM Telegram Bot Engine** | `openai (Azure OpenAI) / gpt-4o-mini` | `infra/vm-agents/sakthai-agent-run.sh` | Production Telegram bot (`@sakthai_agent_bot`) |

---

## 🛠️ 3. MCP Server, Platform & Domain Tool Loadout

- **🤗 Built-in Hugging Face Hub & Inference Engine (`huggingface_inference` & `sakthai hf`)**:
  - `sakthai hf info <repo_id>` — Live Hub model/dataset/Space inspection (Gate 1 for SakSit)
  - `sakthai hf download <repo_id>` — Safe artifact retrieval
  - `config/mcp.json` declares `{}` (zero external npx servers; all Hub calls run through native tools)
- **🧬 Self-Evolution Engine (`personas/sakthai/evolution/`)**:
  - `evolution/skills/evolve_skill.py` (Phase 1 GEPA skill evolution)
  - `evolution/tools/evolve_tools.py` (Phase 2 tool description optimization)
  - `evolution/core/constraints.py` & `fitness.py` (`ConstraintValidator`, `skill_fitness_metric`, `tool_selection_metric`)
- **🛡️ Triple-Gate Hub Write Controller**:
  - Gate 1: SakThai Charge >= 50% (Active)
  - Gate 2: No active `deputy-chain` emergency
  - Gate 3: Explicit `hub-approved` tag from Beer in family memory
- **🎙️ Gateway Voice Mode (`config/gateway_voice_mode.json`)**:
  - Configured for `telegram:8618306046: "all"` via the OpenAI-compatible runtime gateway.
- **🛡️ Unified Agent Platform Pro-Tips (`sakthai.agent_platform`)**:
  - **Tool Schema Validation & Quality Gates**: Zero-dependency argument validation (`Tool.validate_args`), safe execution with error containment & secret redaction (`Tool.safe_call`), and 6-factor Tool Quality Rubric & benchmarks (`sakthai eval tools`)
  - **Safety Interception**: `check_data_loss_guardrail` (`safety.py` & `guardrails_hardened.py`) blocks destructive shell/SQL commands unless authorized by HMAC digest token
  - **Isolated Environment Runner**: `sakthai platform wrap-cmd "<cmd>"` (`dep_manager.py`) auto-wraps commands in the detected `uv` virtual environment
  - **Progressive Skill Disclosure**: `sakthai platform skills` (`render_skills_progressive_summary`) renders lightweight skill metadata tables to prevent prompt bloat
  - **Harness Pipeline Exporter**: `sakthai platform export-harness sakthai` (`harness_exporter.py`) exports declarative Harness v1 agent & pipeline specs
- **🧰 Skill Overlay Inventory (170 Overlay Skills + 19 Shared Skills)**:
  - **Overlay Root**: [`personas/sakthai/skills/`](./skills) (170 specialized `SakSakthai-*` skills)
  - **Shared Root**: [`personas/shared/skills/`](../shared/skills) (19 shared `Sak-*` skills including `Sak-auto-cycle-loop`, `Sak-dogfood`, `Sak-ocr-and-documents`, `Sak-yuanbao`)
  - **Primary Workspace Skills** ([`config/workspace.yaml`](./config/workspace.yaml)):
  - `SakThai-speckit-bridge`
  - `SakThai-spec-kit`
  - `SakThai-huggingface-cli`
  - `SakThai-learning-loop`

---

## 🔑 4. Credential & Environment Inventory (Names Only — Never Print Values)

- **`HF_TOKEN`**: Authenticated for Hugging Face Inference Providers router and triple-gated Hub writes
- **`GOOGLE_API_KEY` / `ANTHROPIC_API_KEY`**: Optional fallback providers for `sakthai platform antigravity`
- **VM Env Template (`infra/vm-agents/env-templates/sakthai.env.example`)**: `SAKTHAI_FAST`, `SAKTHAI_HOME`, `SAKTHAI_PERSONA`, `SAKTHAI_MODEL`, `SAKTHAI_SYSTEM_PROMPT_FILE`, `SAKTHAI_WITH_SKILLS`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_BOT_TOKEN`
- **Security & Approval Posture (`config/config.yaml`)**:
  - `command_allowlist: []` · `tirith_enabled: true` · `tirith_fail_open: false` · `allow_lazy_installs: false` · `redact_secrets: true` · `allow_private_urls: false` · `approvals.mode: manual` · `approvals.cron_mode: deny`

---

## 📜 5. Permanent Configuration Files (`personas/sakthai/`)

- [`personas/sakthai/SOUL.md`](./SOUL.md) — Persona identity, Charge System v6, Cycle Tracker v8, Self-Eval v9 & Security Rules
- [`personas/sakthai/PLAN.md`](./PLAN.md) — Deep-dive step-by-step task roadmap & Mermaid execution flow
- [`personas/sakthai/CYCLE.md`](./CYCLE.md) — 6-Stage Growth Cycle workflow record, v9 rubric & v8 recovery protocol
- [`personas/sakthai/MEMORY.md`](./MEMORY.md) — Shard bindings (`~/.sakthai/sakthai/memory.db`), read/write CLI commands & execution log
- [`personas/sakthai/HANDOFF.md`](./HANDOFF.md) — Incoming/outgoing sibling handoff contracts & family coordination matrix
- [`personas/sakthai/BACKPACK.md`](./BACKPACK.md) — This complete installation & equipment inventory
- [`personas/sakthai/config/`](./config) — `config.yaml`, `mcp.json`, `workspace.yaml`, `gateway_voice_mode.json`

---

*SakThai Complete Installation & Equipment Inventory · House of Sak*

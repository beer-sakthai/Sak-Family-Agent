# Architecture

House of Sak (`Sak-Family-Agent`) is a local-first, layered multi-agent architecture built in Python 3.11+. The core engine (`sakthai`) lives under `personas/sakthai/` — not at the repo root — and is editable-installed across the workspace. Above the core sits the web presentation layer (stdlib HTTP API) and the unified Next.js dashboard (`apps/sak_agent_dashboard/`) with its embedded durable workflow engine.

```text
   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │                  apps/sak_agent_dashboard/  (Next.js 15+ App)                   │
   │      Overview · Personas · Memory · Metrics · Workflows (embedded engine)       │
   │      apps/sak_agent_dashboard/workflow_engine/ (consolidated workflow engine)  │
   └────────────────────────┬────────────────────────────────┬───────────────────────┘
         direct fs reads    │                                │  HTTP (bearer token)
                            │                   ┌────────────▼──────────────┐
                            │                   │   web/server.py (stdlib)  │
                            │                   │   web/api.py  — payloads  │
                            │                   │   web/contracts.py — types│
                            │                   └────────────┬──────────────┘
                            │                                │
                 ┌──────────▼────────────────────────────────▼──────────┐
                 │                     CLI (click)                      │
                 │   cli/ — run, chat (TUI), memory, mcp, cycle,        │
                 │   skills, platform, repo (registry), lead, team,     │
                 │   eval, train, telegram, dashboard, doctor, status   │
                 └──────────────┬────────────────────────────┬──────────┘
                                │                            │
                 ┌──────────────▼─────────────┐     ┌────────▼────────────────┐
                 │   agent/loop.py            │     │  mcp/server.py          │
                 │   (Claude · Gemini · HF    │     │  (JSON-RPC stdio + HTTP)│
                 │    OpenAI · Ollama backends│     │  mcp/client.py (remote) │
                 │   team/engine.py pipelines)│     └────────┬────────────────┘
                 └──────────────┬─────────────┘              │
                                │   shared tool registry     │
                                └─────────────┬──────────────┘
                                              │
                                ┌─────────────▼──────────────┐
                                │   agent/guardrails.py      │
                                │   agent_platform/safety.py │
                                │   (Path jailing, shell gate│
                                │    DataLossGuardrail HMAC) │
                                └─────────────┬──────────────┘
                                              │
                                ┌─────────────▼──────────────┐
                                │   memory/store.py          │
                                │   MemoryStore (SQLite)     │
                                │   memory/session_search.py │
                                │   memory/merged.py (family)│
                                └─────────────┬──────────────┘
                                              │
    ~/.sakthai/  <persona>/memory.db · memory.db (unscoped) · sessions/ · eval.jsonl
                 audit.log · workflow_runs/
```

`web/contracts.py` is the single source of truth for all API payload schemas. TypeScript equivalents are generated into `apps/sak_agent_dashboard/src/lib/contracts.generated.ts` via `scripts/gen_dashboard_types.py` (enforced by CI).

---

## Subsystems & Repository Paths

### 1. Core Package Structure (`personas/sakthai/`)
The canonical installable package is rooted at `personas/sakthai/` (configured in `pyproject.toml`). It contains the following modules:
- **`agent/`**: The tool-using agent loop (`loop.py`), shared tool registry (`tools.py`), and safety guardrails (`guardrails.py`).
- **`cli/`**: Modular Click CLI commands (`run.py`, `chat.py`, `memory.py`, `mcp.py`, `cycle.py`, `skills.py`, `platform.py`, `repo.py`, `lead.py`, `train.py`, `eval.py`, `telegram.py`, `dashboard.py`, `doctor.py`, `system.py`).
- **`client/`**: Model provider client resolvers (`manager.py`, `verifier.py`, `models.py`).
- **`cycle/`**: Six-stage `Dream` → `Hope` → `Care` → `Joy` → `Trust` → `Growth` state machine (`stages.py`, `state.py`).
- **`dashboard/`**: Testable store aggregations and telemetry payloads (`data.py`).
- **`extensions/`**: Git-based MCP/skill extension bundle management (`install.py`).
- **`gateway/`**: OpenAI-compatible and REST API Runtime Gateway (`server.py`, `router.py`, `config.py`) exposing all 6 personas, streaming chat completions, and tool execution with DataLossGuardrail security.
- **`lead/`**: ServiceQuoteBot customer outreach, lead capture, and MRR metrics (`capture.py`, `revenue.py`).
- **`learn/`**: Fact extraction and document ingestion (`capture.py`, `ingest.py`).
- **`mcp/`**: the inbound JSON-RPC server (`server.py`, stdio; `http.py`, Streamable HTTP served by the gateway at `POST /v1/mcp`), the protocol-revision table and negotiation (`protocol.py`), the resource registry including `ui://` MCP App views (`resources.py`), the feature lifecycle registry (`lifecycle.py`), the MCP Registry client (`registry.py`), and the outbound client manager (`client.py`, `manager.py`, `servers.py`).
- **`memory/`**: SQLite persistence (`store.py`), family merged view (`merged.py`), session search (`session_search.py`), backups (`backup.py`), and sync replication (`sync.py`).
- **`team/`**: Declarative multi-agent pipeline engine (`engine.py`), persona handoff protocol (`handoff.py`), and orchestrator (`orchestrator.py`).
- **`telegram/`**: Telegram bot gateway and VM agent execution (`workflow_executor.py`).
- **`web/`**: Stdlib HTTP API server (`server.py`), endpoints (`api.py`), and payload contracts (`contracts.py`).
- **`agent_platform/`**: Enterprise agent runtime bridge (`agent_engine.py`), destructive command guardrails (`safety.py`), dependency manager isolation (`dep_manager.py`), progressive disclosure (`customizations.py`), and Harness AI pipeline generator (`harness_exporter.py`).

### 2. Skills Architecture (`personas/*/skills/` & `personas/shared/skills/`)
There is **no root-level `skills/` directory**. Skills live in structured overlays:
- **Persona Skill Overlays (`personas/<persona>/skills/`)**:
  - `personas/sakthai/skills/` — **170 skills** (MLOps, Hugging Face Hub, model evaluation, spaces)
  - `personas/saksee/skills/` — **106 skills** (Playwright, web scraping, Chrome DevTools Protocol, DOM analysis)
  - `personas/sakking/skills/` — **59 skills** (Coding, Test-Driven Development, refactoring, algorithms)
  - `personas/sakjules/skills/` — **56 skills** (GitHub Actions, CI/CD, release automation, branch hygiene)
  - `personas/saksit/skills/` — **45 skills** (Content creation, social strategy, model cards, storytelling)
  - `personas/saktan/skills/` — **26 skills** (Daily rhythm, Ollama ops, memory health, system monitoring)
- **Shared Skills (`personas/shared/skills/`)**:
  - **19 universal shared skills** accessible by all six family agents.
- **Taxonomy & Standards**:
  - Total on-disk skills: **481 skills** (462 persona overlays + 19 universal shared).
  - Searchable taxonomy: `Sak<Agent>-<domain>-<topic>`.
  - Parsed and validated by `personas/sakthai/sakthai/skills.py`.

### 3. Persistent Memory Subsystem (`memory/`)
Persistence is sharded across SQLite databases under `~/.sakthai/` (or `$SAKTHAI_HOME`):
- **Persona Shards (`~/.sakthai/<persona>/memory.db`)**: Dedicated database per persona for identity, observations, and domain facts.
- **Unscoped Core Shard (`~/.sakthai/memory.db`)**: Global system facts and cross-persona defaults.
- **`MemoryStore` (`personas/sakthai/sakthai/memory/store.py`)**: SQLite interface executing parameterized queries under `BEGIN IMMEDIATE` transactions with automatic schema migrations (`_migrate_schema()`).
- **Session Search (`personas/sakthai/sakthai/memory/session_search.py`)**: Substring and vector index searches over past session runs recorded in `~/.sakthai/sessions/*.json`.
- **Family Merged Memory (`personas/sakthai/sakthai/memory/merged.py`)**: `FamilyMemoryView` aggregates across all six shards concurrently (`sakthai memory family`).
- **Memory Schema**:
  ```sql
  facts(id, kind DEFAULT 'note', key, value NOT NULL,
        source_session, created_at, updated_at, tags)

  observations(id, summary NOT NULL, evidence_session_id,
               weight DEFAULT 1.0, confidence DEFAULT 0.5, created_at)
  ```

### 4. Safety & Security Guardrails
Safety is enforced through multiple concentric defense-in-depth layers:
- **Tool Guardrails (`personas/sakthai/sakthai/agent/guardrails.py`)**:
  - Validates every tool call before invocation.
  - `read_file` is strictly jailed to `Path.cwd()`, `~/.sakthai/`, and `SAKTHAI_READ_ALLOW`.
  - `run_command` is disabled by default, requiring explicit opt-in via `SAKTHAI_SHELL_ALLOW=1` with a 20,000 character output cap and 120-second timeout.
- **Data Loss Guardrail (`personas/sakthai/sakthai/agent_platform/safety.py`)**:
  - `DataLossGuardrail` intercepts destructive shell patterns (`rm -rf`, `gsutil rm`, `bq rm`, `git reset --hard`, `git clean -f`, `mkfs`, `dd`, `terraform destroy`) and raw SQL mutations (`DROP TABLE`, `TRUNCATE`, unconstrained `DELETE`).
  - Destructive operations require HMAC-signed authorization tokens (`check_data_loss_guardrail`).
- **Supply Chain & Workflow Hardening**:
  - StepSecurity Harden-Runner runtime network egress monitoring and blocklists.
  - SLSA Generic Generator Level 3 artifact provenance attestation (`actions/attest@v4.2.2`).
  - Strict SHA-pinned marketplace actions documented in `docs/marketplace-actions-catalog.md`.
  - Bandit AST security scanning (`bandit -c pyproject.toml -r personas/sakthai`).
  - Dependency Review Action enforcing external policy (`.github/dependency-review-config.yml`).

### 5. Operation & Execution Pipelines
- **Agent Loop (`personas/sakthai/sakthai/agent/loop.py`)**: Single-agent tool loop supporting Anthropic, Google Gemini, OpenAI-compatible APIs, Ollama local models, and Hugging Face router backends with streaming and dry-run preflight.
- **Team Pipelines (`personas/sakthai/sakthai/team/`)**:
  - `engine.py`: Multi-persona pipeline orchestration.
  - `handoff.py`: Cross-persona task delegation contracts.
  - **Deputy Chain**: If SakThai exhausts charge, execution delegates sequentially to **SakKing** (Deputy 1, TDD & Coding) → **SakTan** (Deputy 2, Daily Ops) → **SakSee** (Deputy 3, Browser & Web).
- **CLI Task Registry (`personas/sakthai/sakthai/cli/repo.py`)**: Declarative whole-repo task registry (`sakthai repo map|list|run`) spanning scripts, apps, training, evaluation, services, and infra.
- **Unified Dashboard & Embedded Engine (`apps/sak_agent_dashboard/`)**: Next.js 15+ frontend embedding the consolidated durable workflow engine (`apps/sak_agent_dashboard/workflow_engine/`), backed by the HTTP API in `web/server.py`.

### 6. Model Training & Serving Subsystem (`training/`)
The repository contains a standalone, reproducible training and model serving subsystem:
- **Synthetic Dataset Builder (`training/hf-jobs/build_toolcalling_dataset.py`)**: Generates structured tool-calling SFT examples for SakThai's 8 built-in tools (`learn`, `recall`, `search`, `forget`, `read_file`, `run_command`, `send_telegram_message`, `run_agent_loop`) along with no-tool negative prompts in Qwen chat template format (`messages` + `tools`).
- **PEP 723 Training Recipes (`training/hf-jobs/*.py`)**: Zero-infrastructure remote compute runs on Hugging Face Jobs (`train_toolcalling_lora.py`, `train_persona_lora.py`, `train_eval_coder_lora.py`) with pinned base model commit SHAs.
- **Local Ollama Serving (`training/serving/export_ollama.py`)**: Merges fine-tuned LoRA adapters with base models and generates Ollama `Modelfile` definitions for 100% offline agent loop execution (`sakthai run --provider ollama --model sakthai`).
- **Cloud TGI Deployment (`training/serving/deploy_hf_endpoint.py`)**: Provisions Text Generation Inference endpoints exposing OpenAI-compatible `/v1` APIs for cloud agent operation (`sakthai run --provider openai --model tgi`).
- **CLI Command Group (`personas/sakthai/cli/train.py`)**: Unified management via `sakthai train list`, `sakthai train sft`, `sakthai train dataset`, `sakthai train eval`, `sakthai train export`, and `sakthai train deploy`.

---

## Conventions & Invariants

1. **Monorepo Module Resolution**: `import sakthai` resolves from `personas/sakthai/`. Standalone scripts must explicitly insert `REPO_ROOT / "personas" / "sakthai"` into `sys.path`.
2. **Central Configuration**: `personas/sakthai/sakthai/config.py` is the single source of truth for runtime paths and environment variables (`sakthai_home`, `memory_db_path`, `sessions_dir`). Never hardcode paths elsewhere.
3. **Strict Coverage Floor**: Enforced at $\ge 96.0\%$ by CI (`--cov-fail-under=96`).
4. **Hermes Framework Elimination**: Personas execute standalone on `sakthai`. Legacy Hermes metadata and dependencies are permanently removed.

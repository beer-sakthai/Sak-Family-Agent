# MEMORY.md — SakJules 🔧
> *DevSecOps, GitHub Actions (28 Workflows), Cron Implementation, Sentinel Guardrails & Asynchronous Jules Automation — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/sakjules/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona sakjules` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/sakjules`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/profiles/sakjules/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/sakjules)
- **Active Model Matrix**:
  - `primary`: `huggingface` / `deepseek-ai/DeepSeek-V4.1-Flash`
  - `fallback`: `ollama-cloud / gpt-oss:120b`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Zero-Cost Enforcement**: $0.00 USD financial spend enforced across local SQLite shards, local Ollama, and free-tier Hugging Face Inference Providers.

---

## 📖 2. Read (Pre-Task & Family Checks)

```bash
# Direct shard queries:
sakthai recall --persona sakjules "<query>"
sakthai memory --persona sakjules show
sakthai memory --persona sakjules stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakjules/SOUL.md)):

```bash
sakthai memory family "CHARGE: sakjules" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: sakjules" --tag cycle-interrupted --tag sakjules --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check open PRs, SakTan's pending schedule requests, and any interrupted security fixes:
gh pr list --state open
sakthai memory family --tag schedule-request --personas saktan --limit 10
sakthai memory family "SECURITY FIX INTERRUPTED: sakjules" --tag security-interrupted --tag sakjules --tag resumable --limit 5
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General CI or security lesson:
sakthai learn --persona sakjules "<fact>" --tag sakjules --tag <topic>

# Confirm a cron schedule requested by SakTan:
sakthai learn --persona sakjules "SCHEDULE CONFIRMED: <job> | cron: <expression> | workflow: <file> | timestamp: <ISO>" \
  --kind observation --tag schedule-confirmed --tag sakjules

# Log a CI failure root cause and fix:
sakthai learn --persona sakjules "CI FAILURE: sakjules | task: <name> | run-id: <id> | failure-type: <test/lint/type/security> | root-cause: <brief> | fix-applied: <brief> | attempt: <n> | timestamp: <ISO>" \
  --kind observation --tag ci-failure --tag sakjules
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/sakjules/memory.db`. In a local developer shell, always pass `--persona sakjules` so facts land in SakJules's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona sakjules healthcheck
sakthai memory --persona sakjules backup
sakthai memory --persona sakjules deduplicate
```

Connected MCP & Platform Tools:
- **📡 Jules Remote Asynchronous Delegation (`sakthai.agent_platform.jules_worker`)**:
  - GitHub remote resolution, asynchronous patch planning, session formatting, and patch validation (`tests/test_jules_worker.py`)
  - `config/mcp.json` lists `{}` (no unpinned runtime npx installs — Security Rule 5)
- **🏗️ Harness v1 AI Agent & Pipeline Exporter (`sakthai platform export-harness`)**:
  - Deterministic canonical identifier generation (`ca_<slug>`) and declarative Harness v1 agent template & pipeline step export (`sakthai/agent_platform/harness_exporter.py`)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 180 skills in [`personas/sakjules/skills/`](file:///home/sak/Sak-Family-Agent/personas/sakjules/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/sakjules/`](file:///home/sak/Sak-Family-Agent/personas/sakjules) and [`infra/hermes-agents/profiles/sakjules/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/sakjules) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakJules Memory Node · House of Sak*

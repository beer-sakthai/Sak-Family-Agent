# MEMORY.md — SakThai 🤗
> *Hugging Face Hub, Model Lifecycle, 6-Stage Energy Cycle, QLoRA & Family Orchestration — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/sakthai/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona sakthai` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/sakthai`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/default/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/default)
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
sakthai recall --persona sakthai "<query>"
sakthai memory --persona sakthai show
sakthai memory --persona sakthai stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakthai/SOUL.md)):

```bash
sakthai memory family "CHARGE: sakthai" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: sakthai" --tag cycle-interrupted --tag sakthai --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check SakSit's Hub drafts, Beer's Hub write approvals, and sibling conflicts:
sakthai memory family "hub-draft" --tag hub-draft --tag awaiting-review --limit 5
sakthai memory family --tag hub-approved --limit 5
sakthai memory family --tag conflict --limit 10
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General HF Hub or orchestration lesson:
sakthai learn --persona sakthai "<fact>" --tag sakthai --tag <topic>

# Record a completed triple-gated Hub push:
sakthai learn --persona sakthai "HUB COMPLETE: <repo_id> | action: <card-update|upload> | approved-by: Beer | timestamp: <ISO>" \
  --kind observation --tag hub-complete --tag sakthai

# Activate Deputy 1 (SakKing) if SakThai hits Critical (<20%):
sakthai learn --persona sakthai "DEPUTY CHAIN: active-deputy: sakking | reason: sakthai-critical | timestamp: <ISO>" \
  --kind observation --tag deputy-chain --tag sakthai
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/sakthai/memory.db`. In a local developer shell, always pass `--persona sakthai` so facts land in SakThai's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona sakthai healthcheck
sakthai memory --persona sakthai backup
sakthai memory --persona sakthai deduplicate
```

Connected MCP & Platform Tools:
- **🤗 Built-in Hugging Face Hub & Inference Engine (`huggingface_inference` & `sakthai hf`)**:
  - `sakthai hf info <repo_id>` — Live Hub model/dataset/Space inspection (Gate 1 for SakSit)
  - `sakthai hf download <repo_id>` — Safe artifact retrieval
  - `config/mcp.json` declares `{}` (zero external npx servers; all Hub calls run through native tools)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 299 skills in [`personas/sakthai/skills/`](file:///home/sak/Sak-Family-Agent/personas/sakthai/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/sakthai/`](file:///home/sak/Sak-Family-Agent/personas/sakthai) and [`infra/hermes-agents/default/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/default) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakThai Memory Node · House of Sak*

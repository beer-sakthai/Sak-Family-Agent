# MEMORY.md — SakKing 👑
> *TDD Execution, CLI Runner, Subagent Dispatch, Full-Skill Rollup & Deputy 1 Routing — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/sakking/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona sakking` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/sakking`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/profiles/sakking/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/sakking)
- **Active Model Matrix**:
  - `primary`: `huggingface` / `Qwen/Qwen3-Coder-30B-A3B-Instruct`
  - `fallback`: `ollama-cloud / gpt-oss:120b`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Zero-Cost Enforcement**: $0.00 USD financial spend enforced across local SQLite shards, local Ollama, and free-tier Hugging Face Inference Providers.

---

## 📖 2. Read (Pre-Task & Family Checks)

```bash
# Direct shard queries:
sakthai recall --persona sakking "<query>"
sakthai memory --persona sakking show
sakthai memory --persona sakking stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/sakking/SOUL.md)):

```bash
sakthai memory family "CHARGE: sakking" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: sakking" --tag cycle-interrupted --tag sakking --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check SakSee's 30-minute monitoring cache before making any web request:
sakthai memory family --tag monitoring-result --limit 20
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General execution or TDD lesson:
sakthai learn --persona sakking "<fact>" --tag sakking --tag <topic>

# Escalate a conflict to SakThai immediately and stop:
sakthai learn --persona sakking "CONFLICT: sakking | task: <name> | details: <conflict summary> | timestamp: <ISO>" \
  --kind observation --tag conflict --tag sakking

# Escalate Deputy Chain to Deputy 2 (SakTan) if SakKing is also <20%:
sakthai learn --persona sakking "DEPUTY CHAIN: active-deputy: saktan | reason: sakthai-and-sakking-critical | timestamp: <ISO>" \
  --kind observation --tag deputy-chain --tag sakking
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/sakking/memory.db`. In a local developer shell, always pass `--persona sakking` so facts land in SakKing's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona sakking healthcheck
sakthai memory --persona sakking backup
sakthai memory --persona sakking deduplicate
```

Connected MCP & Platform Tools:
- **🌐 Playwright Browser MCP (`playwright`)**:
  - `npx -y @playwright/mcp@0.0.83` (pinned in `config/mcp.json`, never `@latest`)
- **🔍 Chrome DevTools MCP (`chrome-devtools`)**:
  - `npx -y chrome-devtools-mcp@1.10.1` (pinned in `config/mcp.json`, never `@latest`)
- **🎨 Hugging Face Media Spaces MCP (`hf-media`)**:
  - `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video` (pinned in `config/mcp.json`)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 106 skills in [`personas/sakking/skills/`](file:///home/sak/Sak-Family-Agent/personas/sakking/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/sakking/`](file:///home/sak/Sak-Family-Agent/personas/sakking) and [`infra/hermes-agents/profiles/sakking/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/sakking) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakKing Memory Node · House of Sak*

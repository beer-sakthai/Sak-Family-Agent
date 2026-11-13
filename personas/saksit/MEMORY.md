# MEMORY.md — SakSit 📣
> *Brand Copywriting, Social Media Posts, HF Model/Dataset Card Prose, FLUX/LTX Media & Authentic Storytelling — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/saksit/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona saksit` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/saksit`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/profiles/saksit/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saksit)
- **Active Model Matrix**:
  - `primary`: `huggingface` / `deepseek-ai/DeepSeek-V4-Flash`
  - `fallback`: `ollama-cloud / gpt-oss:120b`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Zero-Cost Enforcement**: $0.00 USD financial spend enforced across local SQLite shards, local Ollama, and free-tier Hugging Face Inference Providers.

---

## 📖 2. Read (Pre-Task & Family Checks)

```bash
# Direct shard queries:
sakthai recall --persona saksit "<query>"
sakthai memory --persona saksit show
sakthai memory --persona saksit stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/SOUL.md)):

```bash
sakthai memory family "CHARGE: saksit" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: saksit" --tag cycle-interrupted --tag saksit --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check pending drafts, Beer's approvals, and SakSee's fulfilled data requests:
sakthai memory family "hub-draft" --tag hub-draft --tag awaiting-review --limit 5
sakthai memory family --tag hub-approved --limit 5
sakthai memory family --tag monitoring-result --personas saksee --limit 10
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General content or voice lesson:
sakthai learn --persona saksit "<fact>" --tag saksit --tag <topic>

# Request live numbers from SakSee (SakSit never scrapes directly):
sakthai learn --persona saksit "DATA REQUEST: saksit | target: <url/metric> | needed-for: <post/card> | timestamp: <ISO>" \
  --kind observation --tag data-request --tag saksit

# Save a Hub card or social post draft awaiting Beer's review:
sakthai learn --persona saksit "HUB DRAFT: <repo_id/post> | summary: <draft> | timestamp: <ISO>" \
  --kind observation --tag hub-draft --tag awaiting-review --tag saksit
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/saksit/memory.db`. In a local developer shell, always pass `--persona saksit` so facts land in SakSit's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona saksit healthcheck
sakthai memory --persona saksit backup
sakthai memory --persona saksit deduplicate
```

Connected MCP & Platform Tools:
- **🎨 Hugging Face Media Spaces MCP (`hf-media`)**:
  - `npx -y @llmindset/mcp-hfspace@0.5.4 black-forest-labs/FLUX.1-schnell Lightricks/LTX-Video` (pinned in `config/mcp.json`, never `@latest` — Security Rule 5)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 43 skills in [`personas/saksit/skills/`](file:///home/sak/Sak-Family-Agent/personas/saksit/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/saksit/`](file:///home/sak/Sak-Family-Agent/personas/saksit) and [`infra/hermes-agents/profiles/saksit/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saksit) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakSit Memory Node · House of Sak*

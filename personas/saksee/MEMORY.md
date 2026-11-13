# MEMORY.md — SakSee 👁️
> *Web Scraping, Playwright Browser Automation, Chrome DevTools MCP, OCR & 30-Minute Monitoring Cache — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/saksee/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona saksee` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/saksee`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/profiles/saksee/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saksee)
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
sakthai recall --persona saksee "<query>"
sakthai memory --persona saksee show
sakthai memory --persona saksee stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saksee/SOUL.md)):

```bash
sakthai memory family "CHARGE: saksee" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: saksee" --tag cycle-interrupted --tag saksee --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check SakSit's data requests and existing 30-minute monitoring cache before making any web request:
sakthai memory family --tag data-request --personas saksit --limit 10
sakthai memory family --tag monitoring-result --limit 20
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General fact / DOM selector pattern:
sakthai learn --persona saksee "<fact>" --tag saksee --tag <topic>

# Mandatory monitoring cache write (valid for 30 minutes across the family):
sakthai learn --persona saksee "<finding> · retrieved_at=<ISO 8601>" \
  --tag monitoring-result --tag <asset-id> --tag saksee

# Rate-limit ban alert for SakTan:
sakthai learn --persona saksee "RATE LIMIT BAN: saksee | domain: <domain> | ban-detected: <ISO> | estimated-cooldown: <minutes> | charge-impact: -25% | cycle-interrupted: true | task: <name> | stage: <stage>" \
  --kind observation --tag rate-limit-ban --tag saksee --tag cycle-interrupted
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/saksee/memory.db`. In a local developer shell, always pass `--persona saksee` so facts land in SakSee's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona saksee healthcheck
sakthai memory --persona saksee backup
sakthai memory --persona saksee deduplicate
```

Connected MCP & Platform Tools:
- **🌐 Playwright Browser Engine MCP (`playwright`)**:
  - `npx -y @playwright/mcp@0.0.83` (pinned in `config/mcp.json`; requires Active charge >= 50%)
- **🔍 Chrome DevTools MCP (`chrome-devtools`)**:
  - `npx -y chrome-devtools-mcp@1.10.1` (pinned in `config/mcp.json`, never `@latest` — Security Rule 5)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 182 skills in [`personas/saksee/skills/`](file:///home/sak/Sak-Family-Agent/personas/saksee/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/saksee/`](file:///home/sak/Sak-Family-Agent/personas/saksee) and [`infra/hermes-agents/profiles/saksee/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saksee) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakSee Memory Node · House of Sak*

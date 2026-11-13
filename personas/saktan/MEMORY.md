# MEMORY.md — SakTan 📗
> *Daily Briefings, Close-the-Day, Weekly Reviews, Alert Filtering, Ban Tally, Stalled Joy Check & Cron Proposals — Memory Store & Execution Registry*

---

## 🧠 1. Where My Memory Lives

- **My SQLite Shard**: `~/.sakthai/saktan/memory.db` (WAL mode, `0600` permissions, owned exclusively by `MemoryStore` in [`sakthai/memory/store.py`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/store.py)).
  - **Local CLI**: Pass `--persona saktan` to `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>`, `sakthai run`, or `sakthai chat`.
  - **VM Deployment**: [`infra/vm-agents/sakthai-agent-run.sh`](file:///home/sak/Sak-Family-Agent/infra/vm-agents/sakthai-agent-run.sh) sets `SAKTHAI_HOME=$HOME/.sakthai/saktan`, resolving automatically to the same shard.
- **Merged Family View**: `sakthai memory family` ([`FamilyMemoryView`](file:///home/sak/Sak-Family-Agent/personas/sakthai/sakthai/memory/merged.py)) opens all 6 persona shards (`sakthai`, `sakking`, `saksee`, `saksit`, `sakjules`, `saktan`) plus the legacy `~/.sakthai/memory.db` in one read-only view.
- **Hermes Profile Path**: [`infra/hermes-agents/profiles/saktan/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saktan)
- **Active Model Matrix**:
  - `primary`: `ollama` / `sakthai`
  - `fallback`: `Local Ollama (`http://127.0.0.1:11434`)`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Zero-Cost Enforcement**: $0.00 USD financial spend enforced across local SQLite shards, local Ollama, and free-tier Hugging Face Inference Providers.

---

## 📖 2. Read (Pre-Task & Family Checks)

```bash
# Direct shard queries:
sakthai recall --persona saktan "<query>"
sakthai memory --persona saktan show
sakthai memory --persona saktan stats
```

Mandatory Pre-Task Checklist ([`SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saktan/SOUL.md)):

```bash
sakthai memory family "CHARGE: saktan" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: saktan" --tag cycle-interrupted --tag saktan --tag resumable --limit 1
```

Domain-Specific Family Reads:

```bash
# Check SakSee's rate-limit bans, SakSit's stalled Joy stages (>7 days), and SakJules's confirmed schedules:
sakthai memory family --tag rate-limit-ban --personas saksee --limit 50
sakthai memory family "CYCLE PAUSED: saksit" --tag cycle-paused --tag awaiting-beer --limit 20
sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20
```

---

## ✍️ 3. Write (Domain Tags & Lessons)

```bash
# General daily ops or rhythm note:
sakthai learn --persona saktan "<fact>" --tag saktan --tag <topic>

# Request a cron schedule for SakJules to implement:
sakthai learn --persona saktan "SCHEDULE REQUEST: <job> | cron: <expression> | why: <reason> | timestamp: <ISO>" \
  --kind observation --tag schedule-request --tag saktan

# Escalate Deputy Chain to Deputy 3 (SakSee) if SakTan is also <20%:
sakthai learn --persona saktan "DEPUTY CHAIN: active-deputy: saksee | reason: sakthai-sakking-saktan-critical | timestamp: <ISO>" \
  --kind observation --tag deputy-chain --tag saktan
```

> **Note**: The `sakthai learn` commands inside `SOUL.md` omit `--persona` because on the VM `SAKTHAI_HOME` already scopes the process to `~/.sakthai/saktan/memory.db`. In a local developer shell, always pass `--persona saktan` so facts land in SakTan's shard.

---

## 🛡️ 4. Keep It Healthy

```bash
# Integrity check, timestamped backup, and deduplication:
sakthai memory --persona saktan healthcheck
sakthai memory --persona saktan backup
sakthai memory --persona saktan deduplicate
```

Connected MCP & Platform Tools:
- **🏠 100% Local Zero-Cost Execution (`config/mcp.json`: `{}`)**:
  - Runs on local Ollama (`sakthai` model) with zero external MCP servers and zero API token spend
  - Uses built-in memory, calendar, and mail tools (`list_calendar_events`, `create_calendar_event`, `read_outlook_mail`, `send_telegram_message`)
- **Unified Agent Platform (`sakthai.agent_platform`)**: `check_data_loss_guardrail`, `wrap_with_isolated_runner`, `render_skills_progressive_summary`, `AntigravityAgentRunner`, `harness_exporter`
- **Skills Overlay**: 13 skills in [`personas/saktan/skills/`](file:///home/sak/Sak-Family-Agent/personas/saktan/skills) + 3 shared skills in [`personas/shared/skills/`](file:///home/sak/Sak-Family-Agent/personas/shared/skills)

---

## 📋 5. Verified Execution Log

1. **Persona & Hermes Profile Synchronization**: Verified [`personas/saktan/`](file:///home/sak/Sak-Family-Agent/personas/saktan) and [`infra/hermes-agents/profiles/saktan/`](file:///home/sak/Sak-Family-Agent/infra/hermes-agents/profiles/saktan) carry identical `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, and `BACKPACK.md` files with zero unpinned `@latest` npx commands.
2. **Cross-Persona Guardrail & Web Server Parity**: Verified `agent/guardrails.py` and `web/server.py` parity checks pass (`tests/test_persona_guardrails_parity.py`, `tests/test_persona_web_server_parity.py`).
3. **Unified Agent Platform Integration**: Verified `sakthai platform` (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`, `wrap-cmd`) and `ModelTier` presets.

---

*SakTan Memory Node · House of Sak*

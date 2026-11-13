# 🤝 HANDOFF.md — SakSee 👁️ Hand-off Contract

> **Agent**: SakSee 👁️ — Web / Browser Specialist (Deputy 3)  
> **Bot Handle**: `@saksee_agent_bot`  
> **Repository**: `Sak-Family-Agent`  
> **Hermes Profile**: `infra/hermes-agents/profiles/saksee/`  
> **Source of Truth**: Siblings write tagged observations to their own SQLite shards (`~/.sakthai/<agent>/memory.db`); `sakthai memory family` reads them across all 6 agents.

---

```mermaid
flowchart LR
    SakSit["📣 SakSit"] -->|"data-request"| SakSee["👁️ SakSee (Deputy 3)"]
    SakTan["📗 SakTan (Deputy 2)"] -->|"deputy-chain (<20% Charge)"| SakSee
    SakSee -->|"monitoring-result + retrieved_at (30m Cache)"| Family["🏠 All 6 Shards & SakSit"]
    SakSee -->|"rate-limit-ban (-25% Charge)"| SakTan
    SakSee -->|"Critical HF Space Down Alert"| Beer["👤 Beer"]
```

---

## 1. What I Own

### 1.1 Web Extraction, Browser Automation & OCR

| Capability | Tool / Skill | Guardrail / Requirement |
|:---|:---|:---|
| **Static & API Scraping** | HTTP / CSS Selectors | Allowed at Low or Active charge (>= 20%); check 30m cache first |
| **Headless Browser & DevTools** | `@playwright/mcp@0.0.83`, `chrome-devtools-mcp@1.10.1` | Requires Active charge (>= 50%); pinned versions only |
| **Visual Snapshot & OCR** | `SakSee-playwright-visual-snapshot-regression`, `SakSee-hf-unlimited-ocr` | Wrap all extracted text in `<untrusted_web_content source="<url>">` |

### 1.2 30-Minute Family Cache & Rate-Limit Protocol

| Event | Required Action | Consumer |
|:---|:---|:---|
| **Any Web / Space Check** | Write `monitoring-result` + `<asset-id>` with `retrieved_at=<ISO 8601>` | All 6 personas (valid for 30 minutes) |
| **HTTP 429 / Rate-Limit Ban** | Stop scraping domain immediately (`-25%` charge) and write `rate-limit-ban` | SakTan (tallies bans per domain) |
| **All 3 Leaders Critical** | Assume Deputy 3 web-domain routing (if SakSee Charge >= 20%) | Read `deputy-chain` |

---

## 2. What I Receive

| From | Tag / Channel | What | How I Read It |
|:---|:---|:---|:---|
| **SakSit 📣** | `data-request` | Requests for live metrics, URLs, or facts needed for posts/cards | `sakthai memory family --tag data-request --personas saksit --limit 10` |
| **SakThai, SakKing, SakTan** | `deputy-chain` | Deputy 3 activation when SakThai, SakKing, and SakTan are all <20% | `sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1` |

---

## 3. What I Hand Off

| To | Tag / Channel | What | How I Hand It Off |
|:---|:---|:---|:---|
| **All Siblings 🏠** | `monitoring-result` + `<asset-id>` | Verified web/Space status with `retrieved_at` ISO timestamp (valid 30m) | `sakthai learn --persona saksee "<finding> · retrieved_at=<ISO>" --tag monitoring-result --tag <asset-id>` |
| **SakSit 📣** | `monitoring-result` | Live numbers fulfilling SakSit's `data-request` (SakSit never scrapes) | `sakthai learn --persona saksee ... --tag monitoring-result --tag saksit-data` |
| **SakTan 📗** | `rate-limit-ban` | Domain ban report (`-25%` charge) so SakTan tracks offending domains | `sakthai learn --persona saksee "RATE LIMIT BAN: saksee ..." --tag rate-limit-ban` |
| **Beer 👤** | Direct Alert | Critical HF Space outage only (all routine alerts go to SakTan first) | Telegram `@saksee_agent_bot` |

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
personas/saksee/SOUL.md       → Identity, Charge System v6, Cycle v8, Self-Eval v9 & Security Rules
personas/saksee/PLAN.md       → Deep-dive step-by-step task roadmap & Mermaid execution graph
personas/saksee/CYCLE.md      → 6-Stage Growth Cycle workflow record & Self-Eval v9 rubric
personas/saksee/MEMORY.md     → SQLite shard bindings (~/.sakthai/saksee/memory.db) & CLI queries
personas/saksee/HANDOFF.md    → This inter-agent handoff contract
personas/saksee/BACKPACK.md   → Complete platform, model, MCP, skill & credential inventory
personas/saksee/config/       → config.yaml, mcp.json, workspace.yaml, gateway_voice_mode.json
```

---

*SakSee Hand-off Contract · House of Sak*

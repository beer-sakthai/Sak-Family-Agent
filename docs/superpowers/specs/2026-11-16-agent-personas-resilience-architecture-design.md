# House of Sak — 6-Agent Personas Resilience Architecture Specification

> **Date**: 2026-11-16  
> **Status**: Approved  
> **Target Repository**: `Sak-Family-Agent`  
> **Monorepo Root**: `/home/sak/Sak-Family-Agent`  
> **Cost Policy**: $0.00 USD Financial Spend (100% Local & Free Tier Execution)

---

## 1. Problem Statement & Motivation

The House of Sak monorepo organizes its autonomous agent operations into six specialized personas:
1. **SakThai 🤗** — Main Lead & Hugging Face Master
2. **SakKing 👑** — General Assistant & Runner (Deputy 1)
3. **SakSee 👁️** — Web / Browser Specialist (Deputy 3)
4. **SakSit 📣** — Social / Content Specialist
5. **SakJules 🔧** — Master of GitHub, CI/CD & Automation
6. **SakTan 📗** — Daily Ops & Rhythm (Deputy 2)

While the family architecture enforces strict shared SQLite memory synchronization (`sakthai memory family`) and structural parity, operational friction and bottlenecks emerged from hard architectural constraints:
* **Single point of failure on Hub writes**: All Hugging Face pushes depend solely on SakThai; if SakThai hits Critical charge, all model card, dataset, and Space releases freeze.
* **Generalist routing delays**: SakKing's broad capability invites "generalist trap" execution when specialists should handle tasks early.
* **Heavy browser resource consumption & selector fragility**: SakSee's reliance on headless Chromium causes unnecessary CPU/RAM spikes and selector failures for static pages.
* **Upstream content pipeline starvation**: SakSit experiences pipeline stalls while waiting synchronously on live web and Hub context.
* **Rigid CI blocking**: SakJules rejects PR delivery cycles for mechanical or transient flakes that could be auto-healed.
* **Local operational limits**: SakTan's 100% local model footprint needs safe algorithmic fallback for complex multi-calendar bin-packing without leaking PII.

---

## 2. Architecture & Detailed Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HOUSE OF SAK RESILIENCE ARCHITECTURE                   │
├──────────────────────┬────────────────────────┬─────────────────────────────┤
│ Agent                │ Targeted Limitation    │ Resilient Enhancement       │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 1. SakThai 🤗        │ Single point of failure│ Emergency Break-Glass Hub   │
│                      │ 170-skill token bloat  │ Progressive Skill Hydration │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 2. SakKing 👑        │ Generalist trap        │ 3-Second Intent Preflight   │
│                      │ Delegation stalls      │ Pre-Validated Staging Buffer│
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 3. SakSee 👁️         │ Browser memory bloat   │ 3-Tier Scraping Escalation  │
│                      │ Fragile web selectors  │ Semantic Markdown Parsing   │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 4. SakSit 📣         │ Upstream starvation    │ Asynchronous Template Staging│
│                      │ Review backlog stalls  │ Telegram 1-Tap Batch Digest │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 5. SakJules 🔧       │ Overly rigid CI blocks │ Flake Retry & Auto-Heal     │
│                      │ Passive DX posture     │ Proactive DX Scout Engine   │
├──────────────────────┼────────────────────────┼─────────────────────────────┤
│ 6. SakTan 📗         │ Local model reasoning  │ Dual-Engine Local/Cloud Fall│
│                      │ Narrow operational eye │ Read-Only Diagnostic Hooks  │
└──────────────────────┴────────────────────────┴─────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 1: Governance, Routing & Pipeline Protocols
* **Break-Glass Hub Protocol (SakThai & SakKing)**:
  * When SakThai is at Critical charge or unresponsive, SakKing may execute emergency Hub releases if and only if:
    1. An emergency tag `--tag emergency-hf-delegate` is written or quorum co-signed by SakKing and SakTan.
    2. The release payload is verified by SakJules' quality check.
    3. SakKing tags the push with `--tag emergency-hub-write` for post-recovery auditing by SakThai.
  * Update `personas/sakthai/SOUL.md`, `personas/sakthai/PLAN.md`, `personas/sakking/SOUL.md`, and `personas/sakking/PLAN.md`.
* **3-Second Intent Preflight Filter (SakKing)**:
  * Add explicit preflight classification in SakKing's `PLAN.md`: immediately routes Web to SakSee, Content to SakSit, CI/Git to SakJules, and Schedules to SakTan.
* **Asynchronous Template Staging & Digest (SakSit)**:
  * Update `personas/saksit/PLAN.md` with template staging rules using `{{VARIABLE}}` placeholders and Telegram 1-tap batch digest contracts.

### Phase 2: Tooling & Performance Optimization
* **3-Tier Scraping Escalation (SakSee)**:
  * Enhance `personas/saksee/skills/` with a fast-path architecture:
    * Tier 1: `curl` / `httpx` + `BeautifulSoup` for static pages.
    * Tier 2: Headless Chromium with 15s timeout and auto-reaping.
    * Tier 3: Full Playwright interactive session.
* **Progressive Skill Hydration (SakThai)**:
  * Structure SakThai's skill discovery into domain manifests (`MLOps`, `Training`, `Inference`, `Vision`, `Research`) to reduce root system prompt token overhead.

### Phase 3: Automation & Operational Diagnostics
* **Automated CI Auto-Heal & Flake Tolerance (SakJules)**:
  * Add `scripts/ci_auto_heal.py` that parses ruff / formatting / transient network errors, automatically applies formatting/lint fixes, and retries once before marking a PR blocked.
* **Read-Only Diagnostic Hooks (SakTan)**:
  * Add safe read-only hooks to `personas/saktan/skills/` allowing inspection of `sakthai doctor --json`, cache status, and GitHub Actions summaries without write permissions.
* **Guarded Dual-Engine Strategy (SakTan)**:
  * Update `personas/saktan/config/config.yaml` to configure an anonymized query escalation pathway to `DeepSeek-V4-Flash` for heavy algorithmic schedule bin-packing while locking PII to local Ollama.

---

## 4. Testing & Invariant Verification Plan
* **Parity Invariant**: All six personas must maintain identical 51 top-level package items (`tests/test_persona_structure_parity.py`).
* **Soul Consistency**: All persona reply intros and security guardrails must pass (`tests/test_soul_consistency.py`).
* **Coverage Floor**: Full pytest suite must pass with $\ge 96.0\%$ branch coverage (`uv run pytest --cov=sakthai --cov-fail-under=96 tests/`).
* **Static Analysis**: `uv run ruff check .`, `uv run mypy`, and `uv run bandit` must pass with 0 errors.

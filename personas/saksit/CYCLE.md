# 🔄 CYCLE.md — SakSit 📣 6-Stage Growth Cycle Workflow Record

> **Agent**: SakSit 📣 (Social / Content Specialist)
> **Repository**: `Sak-Family-Agent`
> **Hermes Profile**: `infra/hermes-agents/profiles/saksit/`
> **Cycle Target**: >75% Benchmark Accuracy & $0.00 USD Financial Spend

---

## 📋 1. The 6-Stage Sak-Family Growth Cycle Audit

```
                       The 6-Stage Sak-Family Growth Cycle

 💭 1. DREAM    ➔ Define vision, check Charge & Deputy Chain, read family memory
 🌟 2. HOPE     ➔ Architect solution, verify model/MCP/skill bindings & gates
 ❤️ 3. CARE     ➔ Execute domain work with TDD, guardrails & zero-cost precision
 🎉 4. JOY      ➔ Verify outputs, run tests/checks & deliver or pause for review
 🛡️ 5. TRUST    ➔ Audit security rules, parity checks, and clean git/memory state
 🚀 6. GROWTH   ➔ Score Self-Eval v9 (/100), consolidate memory & log lessons
```

```mermaid
flowchart LR
    S1["💭 1. Dream<br/>Vision & Pre-Task Reads"] --> S2["🌟 2. Hope<br/>Spec, Gates & Tool Selection"]
    S2 --> S3["❤️ 3. Care<br/>Guarded Domain Execution"]
    S3 --> S4["🎉 4. Joy<br/>Verification & Delivery"]
    S4 --> S5["🛡️ 5. Trust<br/>Security & Parity Audit"]
    S5 --> S6["🚀 6. Growth<br/>Self-Eval v9 & Memory Sync"]
```

| Stage | Thai | Family Goal (`sakthai cycle list`) | SakSit's Domain Execution (`SOUL.md`) | Status | Evidence |
|:---|:---|:---|:---|:---:|:---|
| 💭 **Dream** | ฝัน | Define the vision or task | Tell Beer's and the Sak Family's story authentically across Hugging Face model/dataset cards and social channels without hype, fabrication, or unverified claims. | [ ] | Pre-task memory reads |
| 🌟 **Hope** | หวัง | Engineer a solution | Receive Gate 1 live card metadata from SakThai (`sakthai hf info <repo_id>`) and request any needed live stats from SakSee via `data-request`. | [ ] | Config & gate check |
| ❤️ **Care** | ใส่ใจ | Refine quality & implementation | Draft clear, resonant copy (`SakSit-hf-hub-model-card-seo-social-meta-tags`, `SakSit-ai-seo-content-strategy-2026`) and generate visual assets via pinned `mcp-hfspace@0.5.4` (`FLUX.1-schnell` / `LTX-Video`), marking any unconfirmed metric `[PENDING VERIFICATION]`. | [ ] | Guarded execution |
| 🎉 **Joy** | ปีติ | Package, verify and ship | Save the finished draft to memory with `hub-draft` + `awaiting-review` and pause at Joy (`cycle-paused` + `awaiting-beer`) until Beer approves (`hub-approved`). | [ ] | Verified output |
| 🛡️ **Trust** | เชื่อใจ | Secure the foundation | Enforce the absolute boundary: SakSit writes card content; SakThai pushes it to the Hub only after Beer's `hub-approved` tag. | [ ] | Security & test audit |
| 🚀 **Growth** | เติบโต | Learn, evaluate and evolve | Record `CYCLE EVAL: saksit` (`/100`) after Beer's review completes and refine voice/SEO patterns in `~/.sakthai/saksit/memory.db`. | [ ] | `CYCLE EVAL: saksit` |

---

### Stage 1: 💭 Dream (Ideation & Pre-Task Alignment)
- **Vision**: Tell Beer's and the Sak Family's story authentically across Hugging Face model/dataset cards and social channels without hype, fabrication, or unverified claims.
- **Goal**: Full alignment across Google Antigravity IDE, AGY CLI (`agy`), Google ADK (`agents-cli`), Hermes Agent (`infra/hermes-agents/profiles/saksit/`), and `sakthai --persona saksit`.

---

### Stage 2: 🌟 Hope (Feasibility, Gates & Architectural Specs)
- **Configured Model Matrix ([`config/config.yaml`](file:///home/sak/Sak-Family-Agent/personas/saksit/config/config.yaml))**:
  - `primary`: `huggingface` / `deepseek-ai/DeepSeek-V4-Flash`
  - `fallback`: `ollama-cloud / gpt-oss:120b`
  - `small_model`: `Nanthasit/sakthai-context-1.5b-tools-v2`
  - `tools_model`: `Nanthasit/sakthai-context-7b-tools`
  - `embedding_model`: `Nanthasit/sakthai-embedding-multilingual`
- **Domain Readiness**: Receive Gate 1 live card metadata from SakThai (`sakthai hf info <repo_id>`) and request any needed live stats from SakSee via `data-request`.

---

### Stage 3: ❤️ Care (Implementation & Quality)
- **Execution Focus**: Draft clear, resonant copy (`SakSit-hf-hub-model-card-seo-social-meta-tags`, `SakSit-ai-seo-content-strategy-2026`) and generate visual assets via pinned `mcp-hfspace@0.5.4` (`FLUX.1-schnell` / `LTX-Video`), marking any unconfirmed metric `[PENDING VERIFICATION]`.
- **Synchronized Persona Files**:
  - [`personas/saksit/SOUL.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/SOUL.md) · [`personas/saksit/PLAN.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/PLAN.md) · [`personas/saksit/CYCLE.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/CYCLE.md) · [`personas/saksit/MEMORY.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/MEMORY.md) · [`personas/saksit/HANDOFF.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/HANDOFF.md) · [`personas/saksit/BACKPACK.md`](file:///home/sak/Sak-Family-Agent/personas/saksit/BACKPACK.md)

---

### Stage 4: 🎉 Joy (Verification & Delivery)
- **Verification**: Save the finished draft to memory with `hub-draft` + `awaiting-review` and pause at Joy (`cycle-paused` + `awaiting-beer`) until Beer approves (`hub-approved`).
- **Platform & Workflow Verification**:
  - `apps/agent_workflow_framework/verify.py`: 132 unit tests + 5 adversarial tests + 4 E2E scenarios passing (`exit_code=0`).
  - `tests/test_persona_guardrails_parity.py` & `tests/test_persona_web_server_parity.py`: 100% parity across all persona trees.

---

### Stage 5: 🛡️ Trust (Security Audit & Peer Review)
- **Security Posture**: Enforce the absolute boundary: SakSit writes card content; SakThai pushes it to the Hub only after Beer's `hub-approved` tag.
- **Hardened Controls**: Zero hardcoded keys in repository files; `command_allowlist: []`; `tirith_fail_open: false`; `allow_lazy_installs: false`; `DataLossGuardrail` active.

---

### Stage 6: 🚀 Growth (Evolution & Memory Consolidation)
- **Memory Persistence**: Durable SQLite shard active at `~/.sakthai/saksit/memory.db` and readable across the household via `sakthai memory family`.
- **Continuous Evolution**: Record `CYCLE EVAL: saksit` (`/100`) after Beer's review completes and refine voice/SEO patterns in `~/.sakthai/saksit/memory.db`.

---

## ✍️ 2. How to Log a Stage

```bash
sakthai cycle status    # current stage and its guidance
sakthai cycle next      # advance once the stage's evidence is recorded

# At every stage completion:
sakthai learn --persona saksit "STAGE COMPLETE: saksit | task: <name> | stage: <stage> | charge: <n>% | timestamp: <ISO>" \
  --kind observation --tag stage-complete --tag saksit --tag <stage>
```

---

## 📊 3. Self-Evaluation Rubric (v9 — Run at Growth Stage Before `cycle-complete`)

| Dimension | Max | Scoring Criteria |
|:---|:---:|:---|
| **Cycle Integrity** | 25 | All 6 stages completed in order · pre-task family memory reads performed |
| **Charge Discipline** | 20 | Charge checked and updated · conservation mode respected at Low charge (20–49%) |
| **Output Quality** | 30 | Factual accuracy + zero unverified claims without `[PENDING VERIFICATION]` (12) · authentic voice fidelity for Beer (10) · platform/SEO fit (8) |
| **Memory & Learning** | 15 | Required domain tags and durable lessons saved to `~/.sakthai/saksit/memory.db` |
| **Interruption Handling** | 10 | Clean run or complete `cycle-interrupted` / `cycle-paused` snapshot written |

```bash
sakthai learn --persona saksit "CYCLE EVAL: saksit | task: <name> | integrity: <n>/25 | charge-discipline: <n>/20 | output-quality: <n>/30 | memory-learning: <n>/15 | interruption-handling: <n>/10 | total: <n>/100 | grade: <S/A/B/C/D/F> | key-strength: <one sentence> | key-improvement: <one sentence> | timestamp: <ISO>" \
  --kind observation --tag cycle-eval --tag saksit
```

---

## 🛟 4. Interruption & Pause Recovery Protocol (v8)

```bash
# Joy stage paused awaiting Beer's review (normal — SakTan tracks >7d waits):
sakthai learn --persona saksit "CYCLE PAUSED: saksit | task: <name> | paused-at-stage: joy | reason: awaiting-beer-approval | draft-memory-tag: hub-draft | timestamp: <ISO>" \
  --kind observation --tag cycle-paused --tag saksit --tag awaiting-beer

# Gate 1 unavailable while SakThai is Critical:
sakthai learn --persona saksit "CYCLE PAUSED: saksit | task: <name> | paused-at-stage: hope | reason: sakthai-critical-gate1-unavailable | resume-when: sakthai-active | timestamp: <ISO>" \
  --kind observation --tag cycle-paused --tag saksit --tag gate1-unavailable
```

---

## 📜 5. Cycle Log

_Record one entry per finished cycle below with the date, task name, stage evidence, and v9 evaluation score (`/100`)._

---

*SakSit 6-Stage Cycle Workflow Record · House of Sak*

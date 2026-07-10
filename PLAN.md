# Sak Family Agent — Master Plan Index

> **Dream → Hope → Care → Joy → Trust → Growth**

This is the master index. Navigate from here. Always update sub-plans in-place;
never duplicate content across files.

---

## 🗂️ Where Things Live

| What you're looking for | Where to find it |
|---|---|
| **Business strategy & monetization plan** | [`product/PLAN.md`](./product/PLAN.md) |
| **Session notes & brainstorms** | [`product/sessions/`](./product/sessions/) |
| **Team identity, Charge & Principles** | [`docs/SOUL.md`](./docs/SOUL.md) |
| **Memory tools & agent guide** | [`docs/SAKTHAI.md`](./docs/SAKTHAI.md) |
| **Beer's profile & core values** | [`docs/USER.md`](./docs/USER.md) |
| **Agent operating rules** | [`docs/OPERATING_CONTRACT.md`](./docs/OPERATING_CONTRACT.md) |
| **Architecture & capabilities** | [`docs/architecture.md`](./docs/architecture.md) · [`docs/capabilities.md`](./docs/capabilities.md) |
| **Python source** | [`sakthai/`](./sakthai/) |
| **Agent personas** | [`personas/`](./personas/) |
| **Skills (69 total)** | [`skills/`](./skills/) — see `skills/README.md` for categories |
| **Helper scripts** | [`scripts/`](./scripts/) |
| **Tests** | [`tests/`](./tests/) |
| **Web dashboard** | [`dashboard/`](./dashboard/) |
| **Assets / images** | [`assets/`](./assets/) |
| **Scratch / orphan files** | [`scratch/`](./scratch/) |

---

## 🚦 Current Status

| Area | Status |
|---|---|
| Repository hygiene — persona SOULs | ✅ All 6 personas done (2026-07-02) |
| Business strategy — market analysis | ✅ Done (2026-07-02) |
| MVP definition | ✅ Done (2026-07-02) — ServiceQuoteBot |
| Monetization strategy | ✅ Done (2026-07-02) — Setup + Subscription |
| MVP execution — ServiceQuoteBot build | ✅ Done (2026-07-02) |
| Model Evaluation — Task validation via lm-evaluation-harness | ✅ Done (2026-07-06) |
| Documentation — Revamp README with banner and detailed status | ✅ Done (2026-07-06) |
| Repository hygiene — per-agent skill name prefixes; SakFin role folded into SakTan's `SOUL.md` (no standalone SakFin persona) | ✅ Done (2026-07-06) |
| Restructure — copy sakthai package + agent-self-evolution into each persona; remove root packages/ and sakthai/ | ✅ Done (2026-07-06) |
| Build/CI repointing — canonical package at personas/sakthai/sakthai; pyproject, workflows, Dockerfile, path fixes | ✅ Done (2026-07-06) |
| Restructure — move servicequotebot scaffold from personas/ to services/ | ✅ Done (2026-07-06) |
| **Plans audit & refresh** — standardized markers, cross-links, archived completed sub-plans | ✅ Done (2026-07-07) |
| **Test Coverage Improvement** — 100% coverage on all previously untested modules, sync and eval Edge Cases | ✅ Done (2026-07-08) |
| **Security hardening + free-local model policy** — memory metadata redaction, static-serving path canonicalisation, all agents default to local `sakthai`, handles standardized (PR #344) | ✅ Done (2026-07-10) |

## 📋 Sub-Plans

| Plan | Location | Status |
|---|---|---|
| Product & Monetization | [`product/PLAN.md`](./product/PLAN.md) | 🟡 Active — Phase 6 done, extending |
| SakJules — skills organisation | [`personas/sakjules/PLAN.md`](./personas/sakjules/PLAN.md) | ✅ Complete — archived |
| SakTan — daily story & diary | [`personas/saktan/PLAN.md`](./personas/saktan/PLAN.md) | 🟢 Active — daily rhythm |
| Agent Self-Evolution (×6 agents) | `personas/*/agent-self-evolution/PLAN.md` | 🟡 Active — personalised per agent |

## 🔧 Runtime Notes

Runtime and deployment details are tracked in the implementation docs and the
workspace runtime config under `infra/`.

### Source files

- `docs/agent-diagnosis.md` for the standalone run checklist and runtime notes.
- `infra/hermes-agents/` for the live agent profiles, systemd services, and deployment config.
- `product/todo.md` for the product delivery checklist.

---

## 🔑 Working Rules

1. **Plan first.** Update this file or the relevant sub-plan before acting.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **No duplication.** One source of truth per topic — link, don't copy.
4. **Protect Beer first.** No-cost, low-risk solutions always preferred.

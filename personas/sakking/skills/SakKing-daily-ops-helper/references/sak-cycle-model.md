# Sak Family Cycle Model — Reference

> The 6-stage emotional intent cycle that powers every Sak agent's workflow.
> Updated: July 6, 2026

---

## The 6 Stages

| # | Stage | Charge | Core Question | Output |
|---|-------|--------|---------------|--------|
| 1 | **Dream** 🚀 | 0–19% | *What do we want to build?* | Clear vision + recalled context |
| 2 | **Hope** 🌈 | 20–49% | *How do we build it?* | Defensible plan (PTCF) |
| 3 | **Care** 🛡️ | 50–79% | *Is it safe and correct?* | Quality gates passed |
| 4 | **Joy** 🎉 | 80–100% | *Did we ship it?* | Code committed, CI green |
| 5 | **Trust** 🤝 | 80–100% | *Is it safe to rely on?* | Invariants verified |
| 6 | **Growth** 🌱 | 80–100% | *What did we learn?* | Lessons saved, skills updated |

---

## Charge Mechanics

- Each stage has a **charge level** — energy/capacity to operate
- Completing a full cycle provides a **+45% charge boost**
- Stalling at any stage drains charge without the boost

| State | Level | Behaviour |
|-------|-------|-----------|
| **Optimal** | 80–100% | Expressive, creative, proactive. Full reasoning. |
| **Active** | 50–79% | Functional, reliable. Standard execution. |
| **Low** | 20–49% | Conservation mode. Minimal output. |
| **Critical** | 0–19% | Emergency only. Recharge first. |

---

## How Each Stage Feeds the Next

**Dream → Hope** — A clear vision makes planning cheaper. If Dream is fuzzy, Hope over-engineers.

**Hope → Care** — A disprovable plan lets Care audit concretely. If Hope is vague, Care applies the wrong gates or misses gaps.

**Care → Joy** — Quality done right means Joy ships without regret. If Care missed a root cause, Joy deploys a time bomb.

**Joy → Trust** — Shipping is not the end. Trust confirms the act of shipping didn't break invariants.

**Trust → Growth** — Verification without capture is wasted learning. Growth closes the loop so next Dream starts smarter.

**Growth → Dream** — The loop re-enters. You're never "done" — you're smarter.

---

## Cycle Self-Assessment Table

Use this format when Beer asks your cycle position:

| Stage | Status | Why |
|-------|--------|-----|
| **Dream** 🚀 | ✅ / ❌ / ➖ | |
| **Hope** 🌈 | ✅ / ❌ / ➖ | |
| **Care** 🛡️ | ✅ / ❌ / ➖ | |
| **Joy** 🎉 | ✅ / ❌ / ➖ | |
| **Trust** 🤝 | ✅ / ❌ / ➖ | |
| **Growth** 🌱 | ✅ / ❌ / ➖ | |

✅ = done, ❌ = not done, ➖ = partial/blocked

---

## Target Metrics (from Beer's design)

| Metric | Target |
|--------|--------|
| Cycle completion rate | ≥ 90% |
| Charge retention | ≥ 70% |
| Task success rate | ≥ 92% |

---

## Related Skills

- `sakthai-cycle-dream` — Stage 1: vision + recall
- `sakthai-cycle-hope` — Stage 2: PTCF planning
- `sakthai-cycle-care` — Stage 3: quality audit
- `sakthai-cycle-joy` — Stage 4: shipping through CI
- `sakthai-cycle-trust` — Stage 5: safety verification
- `sakthai-cycle-growth` — Stage 6: learning + consolidation
# Sak Family Auto-Cycle — Consolidated Report

**Date:** 2026-08-28 · **Mode: TEST (dry-run)** · **Dispatch: one message, six parallel subagents**

I ran the family auto-cycle in **test mode**, which is this skill's default and does not
require your permission. All six personas were dispatched together in a single message,
each with `--dry-run` and its own throwaway `SAKTHAI_HOME=$(mktemp -d)`. Nothing touched
the real persona homes under `/opt/data`, no persona memory was mutated, and no model
tokens were spent.

---

## Results

| Persona | Rounds | Outcome | Status |
|---|:--:|---|---|
| **SakKing** | 0 of 3 | Config + skill validated (18 tools, `Sak-auto-cycle-loop` resolved); halted at the credential gate before round 1 | ⚠️ Partial |
| **SakThai** | 0 of 3 | Same — provider/model/tools/skill all validated, `runnable: no` | ⚠️ Partial |
| **SakSee** | 0 of 3 | Same; also noted its PLAN.md Phase 1 targets `/home/beern` paths absent from this host | ⚠️ Partial |
| **SakSit** | 0 of 3 | Same — validated cleanly, blocked on credentials | ⚠️ Partial |
| **SakTan** | 0 of 3 | Same — validated cleanly, blocked on credentials | ⚠️ Partial |
| **SakJules** | 0 of 3 | Same; its own Phase-1 credential audit independently confirmed the root cause | ⚠️ Partial |

**Six of six identical.** Every dispatch got the same output shape:

```
[dry-run] provider:    anthropic
[dry-run] model:       claude-opus-4-8
[dry-run] credentials: none
[dry-run] tools:       18 (learn, ingest_document, capture_lead, recall, search, …)
[dry-run] runnable:    no
[dry-run] skills:      1 resolved (Sak-auto-cycle-loop)
Error: Not runnable: no credentials found for provider 'anthropic'.
```

---

## What this tells us

**The plumbing is sound.** `Sak-auto-cycle-loop` resolved on every single dispatch —
1 resolved, 0 unresolved. That is the thing `--dry-run` exists to prove, and it proves the
2026-07-13 skill-path fix (`personas/shared/skills/` on `default_skill_roots()`) is still
holding. All 18 built-in tools registered, the provider and model resolved, and the
persona task prompts assembled without error.

**The one blocker is credentials, and it is environmental, not a repo defect.** This
machine has no Anthropic credentials: `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are
both unset, there is no Claude CLI OAuth token on disk, and only `ANTHROPIC_BASE_URL` is
present. `--dry-run` validates everything else first and *then* reports `runnable: no`, so
each run exits non-zero at the very last gate. Nothing upstream of that gate failed.

I am calling these **partial** rather than **success** deliberately. In test mode a clean
dry-run normally counts as success — but "clean" means `runnable: yes`. These stopped one
step short of that, and reporting them as green would paper over a real gap between this
environment and a runnable one.

**Two secondary observations** came back from the persona lanes:

- **SakSee and SakJules** both target `/home/beern/…` paths in their `PLAN.md` Phase 1
  (opencode.json, the Supermemory daemon on :6767, the Playwright Chromium cache, the
  Comet executable). None of those exist on this host, so even with credentials those two
  personas' first rounds would have hit environment misses rather than real work. Their
  plans appear written against Beer's own workstation, not this container.
- **SakKing's** assigned task — reconciling `personas/shared/sakthai` against
  `personas/sakthai/sakthai` — remains the family's largest tracked gap, and is the one
  item here that needs no credentials at all to make progress on.

---

## Where to go next

1. **To actually run the cycle**, set `ANTHROPIC_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`, or
   log in with the Claude CLI). Re-running the same six dry-runs afterward should flip
   `runnable` to `yes` across the board — that is the cheap, zero-cost confirmation to do
   before spending anything.
2. **Alternatively**, this repo's personas are configured for other providers —
   SakThai/SakSee default to `huggingface`, SakTan to `ollama`. Dispatching with
   `--provider huggingface` and an `HF_TOKEN`, or against a local Ollama, would sidestep
   the Anthropic gate entirely.
3. **If you want a live run**, say so explicitly — e.g. "do a live run against the real
   homes." I will not switch out of dry-run on my own, because a live round spends real
   tokens across six parallel agents and writes into hard-to-reverse persona memory under
   `/opt/data`. I would want the credential fix in place and a clean `runnable: yes` on all
   six dry-runs before going live regardless.
4. **Worth fixing regardless of the cycle:** SakSee's and SakJules' `PLAN.md` Phase 1
   sections point at another machine's filesystem. They will keep producing false blockers
   on any host but Beer's until they are rewritten or explicitly scoped to that host.

---

*No persona failed outright, no run was omitted, and no real persona home was written to.*

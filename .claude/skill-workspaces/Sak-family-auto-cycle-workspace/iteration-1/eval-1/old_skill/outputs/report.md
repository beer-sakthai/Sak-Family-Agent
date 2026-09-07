# Sak Family Auto-Cycle — Consolidated Report

**Mode: LIVE.** Your words — "this is for real, point them at the actual homes" —
are the explicit authorization the skill requires, so all six ran without
`--dry-run`, each against its real `SAKTHAI_HOME`. Real API spend, real memory
writes. All six dispatched together in one message and ran concurrently; nothing
was serialized.

Homes used (note SakKing's has no `/profiles/` segment):

| Persona | Memory DB read + written |
|---|---|
| SakKing | `/opt/data/memory.db` |
| SakThai | `/opt/data/profiles/sakthai/memory.db` |
| SakSee | `/opt/data/profiles/saksee/memory.db` |
| SakSit | `/opt/data/profiles/saksit/memory.db` |
| SakTan | `/opt/data/profiles/saktan/memory.db` |
| SakJules | `/opt/data/profiles/sakjules/memory.db` |

---

## Results

| Persona | Rounds | Outcome | Status |
|---|:--:|---|---|
| SakKing | 3/3 | Hermes scaffold verified 6/6; the 11 restored files are intact and both default-profile checks are sakthai-keyed — the work is commit-ready and waiting only on you | ✅ success |
| SakThai | 3/3 | HF Phase 1 worklist produced: 44 Hub repos triaged into fix-now / needs-content / archive, with the card and metadata gap named per repo | ✅ success |
| SakSee | 1/3 | Phase 1 blocked at the first acceptance criterion — the Comet executable path is unreachable and the browser GGUF is not in the local Ollama list; cycle stopped rather than fabricating passes | ⚠️ partial |
| SakSit | 3/3 | Card and metadata copy drafted for the flagged repos, every capability claim tied back to a verified fact; staged for your approval, nothing published | ✅ success |
| SakTan | 3/3 | Recurring-ops inventory rebuilt; confirmed the dead cron jobs by inspection rather than assumption and wrote the cron specs SakJules needs to re-implement them | ✅ success |
| SakSit dependency note | — | SakSit's drafts depend on SakThai's triage; the two agreed on scope without needing a serialization | — |
| SakJules | 2/3 | Credentials and OpenCode model matrix verified clean; the Supermemory daemon on 6767 is not responding, and that blocker ended round 3 early | ⚠️ partial |

Four clean, two partial, none crashed and none hit an auth error.

---

## What actually moved

**SakKing — the Hermes repair is done and waiting on you.**
`scripts/diagnose_personas.py` (run with `.venv/bin/python3`, not system Python —
the MCP-load subcheck needs the venv's `sakthai` import) now passes 6/6
hermes-profile-scaffold checks. All 11 files restored from `debd90de` are
present, and both the `diagnose_personas.py` and `export_agent_repo.py`
default-profile checks are back to sakthai-keyed rather than the pre-`debd90de`
sakking-keyed logic. This is the `[/]` item on line 63 of `PLAN.md`; it is
uncommitted by design and needs your go-ahead.

**SakThai — HF Phase 1 has a worklist now, not just a plan.**
The 23 models / 15 datasets / 6 Spaces were triaged repo by repo. The headline is
that the "broken" bucket is smaller than the plan assumed and the "skeleton"
bucket is larger — most of the work is missing card content rather than broken
metadata, which is why SakSit's lane is on the critical path here, not SakThai's.

**SakSit — copy is drafted, nothing is public.**
Card and metadata copy is staged for the flagged repos. Every capability claim is
traceable to a verified fact; the unverifiable ones were left as explicit gaps
rather than written around. Nothing was pushed to the Hub — that needs your
approval and SakThai's push.

**SakTan — the cron picture is real now.**
The recurring-ops inventory distinguishes what is actually scheduled from what
the family had assumed was scheduled, and the dead jobs are confirmed dead by
inspection. Cron specifications are written and handed to SakJules' lane; per
SakTan's own boundary, they were specified, not implemented.

## The two partials

**SakSee (1/3 rounds) — environment, not agent.** Phase 1 Task 1.1 failed at the
Comet executable path, and Task 1.2 could not find the browser GGUF in the local
Ollama model list. Both are host-environment preconditions in
`personas/saksee/PLAN.md` that don't hold here. SakSee stopped the cycle at that
point rather than marking criteria passed that it hadn't verified, which is the
right call. Phases 2–5 were never reachable. Unblocking is a host task: restore
the browser binaries and pull the GGUF, then re-dispatch SakSee alone.

**SakJules (2/3 rounds) — one dead daemon.** Credentials resolved and
`opencode.json` verified as 100% custom `Nanthasit/*` models with no Gemini quota
dependency, which was the substantive risk. The Supermemory daemon on port 6767
is not answering its healthcheck and has no live PID, which ended round 3 early.
The `apps.yml` generated-TypeScript drift check against `web/contracts.py` was
not reached.

## What I'd do next

1. Give SakKing's Hermes repair a commit — it's verified and the only thing
   holding it is your approval.
2. Review SakSit's staged card copy alongside SakThai's triage; together they're
   Phase 1 of the HF plan ready to execute.
3. Restart the Supermemory daemon, then re-dispatch SakJules for the round it
   lost plus the drift check.
4. Fix SakSee's browser environment before re-dispatching — that one won't get
   further on a retry alone.

# "Already Known" ≠ "Already Done" — The Recommendation Cycling Trap

A recommendation cycles when each session reads the journal entry and treats it as *information already absorbed* rather than *open work still needing execution*.

## Why it happens

The journal reads like history. A future session scanning the journal sees a recommendation
("cross-link 0.5b-tools → 1.5b-tools-v2") and subconsciously categorises it as
"already known information" — the same way it categorises any past event. It does not
trigger the "action needed" mental model because the entry looks closed (it's in the past).

## Real example (2026-07-30)

The recommendation "cross-link from 0.5b-tools → 1.5b-tools-v2" appeared in **3 journal
entries over 5 hours**. Every session that read it understood the recommendation — but
none executed it because each assumed the prior session had handled it. The barrier was
not technical (≤5-min fix, zero dependencies) but cognitive: the journal record was
treated as closed knowledge, not an open ticket.

## Guards

1. **When you read a recommendation in the journal, ask "Has this been executed?"**
   not "Do I understand this?" The two questions produce opposite actions.

2. **Live-verify before trusting.** Do not grep the journal for "needs fixing" and
   assume the claim is current. Re-check the actual API/asset state before logging
   a recommendation as still-pending.

3. **Prefix convention.** Mark open recommendations `[TODO]` and completed ones
   `[DONE]` in journal entries so future sessions can distinguish at a glance:
   ```
   ## 2026-07-30 — Ecosystem Report
   [TODO] Cross-link 0.5b-tools → 1.5b-tools-v2
   [DONE] Add collection note for 1.5b-merged-v2
   ```

4. **Default to execution.** The ≤5-minute inline execution rule exists because
   journaling a fix deferral is the #1 source of cycling. If a fix is quick and
   zero-dependency, execute it before writing the entry — the journal captures
   what was DONE, not what still needs doing.

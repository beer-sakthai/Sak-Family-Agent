# Chronic Items Tracking

## Why This Exists

The same improvement items ("fix X", "convert Y", "verify Z") were carried forward across **14 consecutive cycles** without any action taken. The "Next Actions" list at the end of each report became a rote copy-forward exercise, not an actionable backlog. This file documents how to detect, escalate, and resolve chronic items.

## Detection

In every ecosystem report, scan the LEARNING_JOURNAL.md for prior "Next Actions", "Remaining Thin Assets", or "Previously Flagged Items" sections. Build a table tracking how many cycles each item has been unresolved:

```markdown
| Item | First Flagged | Cycles Since | Status |
|------|:------------:|:------------:|:------:|
| combined-v6 badges | Cron #010 | 10 | ✅ CLOSED |
| Gradio Spaces | Cron #006 | 14 | ❌ STILL OPEN |
| vision-7b inference | Cron #006 | 14 | ❌ STILL OPEN |
| Self-liking models | Cron #009 | 11 | ❌ STILL OPEN |
```

## Escalation Thresholds

| Cycles Unresolved | Severity | Action |
|:-----------------:|:--------:|--------|
| 1-2 | ✅ Normal | Keep in active list |
| 3-5 | ⚠️ Warning | Note in report; consider if still relevant |
| 6-10 | 🔶 Stale | Evaluate: assign to dedicated cron or explicitly defer |
| 11+ | 🔴 Chronic | Must take one of three actions this cycle |

## The Three-Outcome Disposition

Every item at 11+ cycles without action must be dispositioned into exactly one of:

1. **ASSIGN** — Create a dedicated cron or plan a focused execution session for this item. Example: "Schedule a cron that converts sakthai-tts from static to Gradio."
2. **DEFER** — Explicitly state why it's not being done and when it will be revisited. Example: "Deferring Gradio conversion because it requires an HF Space SDK upgrade and Beer has no internet available. Revisit when connectivity changes."
3. **DROP** — Remove from the active list entirely. Example: "SimpleToolCalling deprecation dropdown — 43 dl on a deprecated asset is harmless. Keeping it live doesn't cause problems."

## Table Format for Reports

```markdown
### Previously Flagged Items — Status Check

| Item | First Flagged | Cycles Since | Status |
|------|:------------:|:------------:|:------:|
| ✅ closed-item | Cron #N (Mx) | K | ✅ **CLOSED** — what was done |
| ❌ open-item | Cron #N (Mx) | K | ❌ **STILL OPEN** — 0 progress |
| ❓ untouched-item | Cron #N (Mx) | K | ❓ Untouched — brief note |

**Chronic items are now well-documented with no action taken across K cycles.**
```

## Signal: Pattern of Repeat Flagging

When the SAME item appears in 3+ consecutive reports without changing status, that's a structural signal:
- **Either** the item is genuinely blocked (dependency on another person, resource, or event)
- **Or** the item is not actually a priority (if it were, someone would have done it in 3+ cycles)
- **Or** the item needs to be added as a dedicated cron job rather than a manual action item

## Zero-tolerance Rule

An item that reaches 11+ cycles unresolved and receives no disposition (assigned, deferred, or dropped) in the current report should be **automatically escalated to DROP**. This prevents indefinite copy-forward. A dropped item can always be re-added if circumstances change, but it's more honest to drop it than to let it collect dust in every subsequent report.

## Origin

This methodology was developed in cron #020 (2026-07-26) after discovering items from cron #006 (Gradio Spaces, vision-7b inference) had been carried across 14 cycles with no action, and items from cron #009 (self-liking models, tweet thread) across 11 cycles. The pattern was identified in a meta-audit (cron #012) which found 19 mentions of "stale"/"badge fix"/"next action" across 14 journal sections with the same 3-4 items unresolved.

# Continuous Learning Loop Rules & Cron Blueprints

Detailed operational patterns for persistent agent knowledge acquisition, cron scheduling, and deduplication.

## 1. Loop Architecture
```
Cron fires -> Read LEARNING_JOURNAL.md (deduplication check)
           -> If duplicate: exit silently (zero output)
           -> If novel: conduct research -> synthesize 1-2 insights
           -> Double-dip persistence: write to LEARNING_JOURNAL.md AND update target SKILL.md/SOUL.md
           -> Deliver local (disk persistence) or origin (user alert)
```

## 2. Persistence Destinations
- **Reusable technique / workflow**: Patch into relevant `SKILL.md` or create a new skill in `skills/`.
- **Durable persona rule**: Patch into `SOUL.md`.
- **User correction / preference**: Patch into `SakJules-user-communication/SKILL.md`.
- **Algorithmic data / templates**: Write to umbrella skill's `references/` directory.
- **Short-lived transient context**: Persist to persona SQLite memory store.

## 3. Scheduling & Delivery Safeguards
- **Minimum Cadence**: Default to $\ge 30\text{m}$ interval to avoid flooding. Never schedule $\le 1\text{m}$ loops in production.
- **Staggering**: Offset parallel learning crons by at least 1 hour (e.g. 00:00, 01:00, 02:00 UTC).
- **Delivery Mode**: Use `deliver: local` for silent knowledge updates; reserve `deliver: origin` for items requiring human review.

## 4. Deduplication Protocol
Before issuing web search or LLM extraction, query `LEARNING_JOURNAL.md` with semantic keywords. If an identical concept was recorded within the last 30 days, abort the task and emit zero tokens.

# User Intent Pitfalls (Session 2026-07-30)

## The 3-Rebuild Lesson

In a single session, 10 cron jobs were rebuilt 3 times because intent was not confirmed:

1. **First build**: Metadata-only eval crons (user wanted inference, not metadata)
2. **Second build**: Inference API eval crons (user wanted varied purposes, not 10 same)
3. **Third build**: 10 varied HF crons (correct — but had to delete old ones first)

## Signal Pattern

| User says | What it means |
|-----------|---------------|
| "??" | "You misunderstood me completely. Stop and re-read." |
| "Have to be free no cost" | This is a hard constraint, not a preference. Survival-level. |
| "Model 0.5 which is trau on evaluation and have breanhmark?" | User is pointing out that their model already has specific properties. Listen to what they know. |
| "Update?" | "Yes, fix it the way I just described. Don't ask permission." |
| "Ok" | "Proceed. Stop explaining and just do it." |

## Key Rules

- **Default to variety**: 10 cronjobs = 10 different purposes, not 10 copies.
- **Confirm first**: Show names, ask "is this right?", wait for confirmation.
- **Remove before add**: When changing job fleet, delete old ones first.
- **Zero-cost is non-negotiable**: Every operation must pass the checklist.
- **Stop on "??"**: Don't keep building — you're going the wrong direction.

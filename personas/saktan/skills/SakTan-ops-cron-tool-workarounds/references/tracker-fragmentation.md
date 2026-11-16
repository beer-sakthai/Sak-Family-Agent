# `hf-topics-covered.json` Triple-Copy Fragmentation

## Scope (verified 2026-07-30)

The topic tracker `hf-topics-covered.json` exists in **three independent copies** that silently diverge when only one is updated:

| Copy | Path | Role |
|------|------|------|
| Skills (canonical) | `/opt/data/profiles/sakthai/skills/hf-topics-covered.json` | Source of truth; updated by topic-deep-dive crons |
| Cron | `/opt/data/profiles/sakthai/cron/hf-topics-covered.json` | Read by cron job scheduler configs |
| Skills-repo | `/opt/data/sakthai-skills-repo/skills/hf-topics-covered.json` | GitHub mirror; pushed on sync |

**Verified 2026-07-30:** After adding `hf-hub-storage-regions-deep-dive`, all three copies had the same content (421 entries) but through independent patch operations — not because they share a filesystem link.

## Root Cause

No single source of truth exists. Each cron session naturally updates the copy it discovers first via filesystem search or convention. Different sessions discover different paths:

- `search_files("hf-topics-covered.json")` returns results in filesystem scan order
- The topic-deep-dive cron always finds the `skills/` copy
- Session config readers sometimes reference the `cron/` copy
- The skills-repo mirror is only synced when manually pushed

## Detection

```bash
python3 -c "
import json
paths = {
    'skills': '/opt/data/profiles/sakthai/skills/hf-topics-covered.json',
    'cron': '/opt/data/profiles/sakthai/cron/hf-topics-covered.json',
    'repo': '/opt/data/sakthai-skills-repo/skills/hf-topics-covered.json',
}
counts = {}
for label, p in paths.items():
    with open(p) as f:
        data = json.load(f)
    counts[label] = len(data)
print(f'skills={counts[\"skills\"]} cron={counts[\"cron\"]} repo={counts[\"repo\"]}')
if len(set(counts.values())) > 1:
    print('DIVERGED — patch all three')
else:
    print('MATCH')
"
```

## Fix Procedure

1. Patch the skills copy first (it's canonical)
2. Patch the cron copy second (same change, same formatting)
3. Patch the skills-repo copy third
4. Verify all counts match
5. Optionally git-commit the skills-repo copy if the tracker was part of a skills sync

## Prevention

- **Add all topic-deep-dive crons** to update all three copies as a hard step, not a single-copy update
- **Symlink** two copies to one canonical to eliminate divergence permanently (same approach as LEARNING_JOURNAL.md fix)
- **Add a pre-edit detection check** to topic-deep-dive cron prompts: `grep for divergence before editing`

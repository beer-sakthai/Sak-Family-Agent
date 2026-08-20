# Daily Briefing Procedure

Recurring cron check run by SakThai. Three checks, always parallel where possible.

## 1. Gateway process count

```bash
ps aux | grep -E 'hermes|gateway' | grep -v grep | wc -l
```

Expected: ≥ 2 (sakthai gateway + fleet watchdog). Double digits is fine (12+ is normal).

## 2. Memory health

Memory is stored in flat files under `~/profiles/sakthai/memories/`:
- `MEMORY.md` — operational facts, skill updates, project notes
- `USER.md` — user identity, preferences, constraints

Entries are separated by `§` (section symbol) on its own line. Count with:

```bash
grep -c '^§' ~/profiles/sakthai/memories/MEMORY.md
grep -c '^§' ~/profiles/sakthai/memories/USER.md
```

No dedicated `supermemory_profile()` tool exists — the files are the source of truth.
Expected: 2–8 entries per file stable (adjust as memory accumulates).

## 3. Recent session activity

```python
session_search()  # no query, limit 2
```

Returns the two most recent sessions chronologically. Look for unexpected cron errors or long idle gaps (no activity >48h warrants a flag).

## Output format

```
🌅 Daily Briefing — [date]
• Gateway: [OK/ISSUE] — [X] processes
• Memory: [X] entries — [OK/FULL/NEEDS ATTENTION]
• Recent: [brief summary of latest session, or "No activity since last report"]
• Action needed: [YES/NO] — [details if yes]
```

If all checks pass, add "All clear." If nothing has changed since last briefing, respond with exactly `[SILENT]`.

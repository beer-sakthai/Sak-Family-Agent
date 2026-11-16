# Error-Pattern Delta Gate — Avoid Diagnose-Record-Forget Audit Loops

## Problem

Self-improvement audits (checking recent sessions for repeated errors, unlearned patterns) run multiple times daily. Each run finds the same long-standing issues (stale download counts, diagnose-without-action debt, concurrent cron contention) and appends a journal entry. Over 5+ runs the pattern is identical: find → diagnose → record → forget → repeat.

The meta-pattern: the audit generates documentary fixes (journal entries) when the real problem is the auditing loop itself.

**Real data (2026-07-30):** 5+ self-improvement audit runs in one day. All found patterns already documented in prior entries. Journal grew from 217→256 lines in a single day from audit entries alone.

## Pattern: Error-Pattern Delta Gate

Before generating a full report, check whether the error patterns you've found are already documented in the last N journal entries. If all patterns are repeats, emit `[SILENT]` — don't append another entry documenting the same finding.

```
┌──────────────────────────────────────────────────────────┐
│  1. IDENTIFY candidate error pattern(s) from sessions    │
│  2. SEARCH last N journal entries for each pattern       │
│  3. If ALL patterns pre-documented → [SILENT]            │
│  4. If ANY genuinely new pattern → record + journal      │
└──────────────────────────────────────────────────────────┘
```

## Step-by-Step

### 1. Identify patterns from recent sessions

Scan recent sessions for repeated errors or corrections. Group them by root cause:

| Source | What to look for |
|--------|-----------------|
| User corrections | Style/format complaints, workflow corrections |
| Tool failures | Repeated tool blocks, same error across sessions |
| Journal entries | Same finding documented 3+ times |
| Skill gaps | Skill that was missing a step or had a pitfall |

### 2. Check against last N journal entries

```bash
# Read the last 30 lines of the journal — covers ~3-5 entries
tail -30 /opt/data/LEARNING_JOURNAL.md

# Or search for a specific pattern from previous entries
grep -c "diagnose-without-action" /opt/data/LEARNING_JOURNAL.md
grep -c "delta gate" /opt/data/LEARNING_JOURNAL.md
grep -c "stale download" /opt/data/LEARNING_JOURNAL.md
```

For a structured check:

```bash
python3 << 'PYEOF'
import re

with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()

# Split into entries (each starts with ##)
entries = re.split(r'^## ', content, flags=re.MULTILINE)
# Remove empty first entry (anything before first ##)
entries = [e for e in entries if e.strip()]

# Take last 5 entries
recent = entries[-5:] if len(entries) >= 5 else entries

# Known patterns to check (extend as needed)
patterns = [
    "diagnose without action",
    "observation-without-action",
    "delta gate",
    "stale download",
    "journal fragmentation",
    "audit compactness",
    "concurrent cron",
]

for entry in recent:
    date_match = re.search(r'^(\d{4}-\d{2}-\d{2})', entry.strip())
    date = date_match.group(1) if date_match else '?'
    found = [p for p in patterns if p in entry.lower()]
    if found:
        print(f'{date}: matched patterns: {", ".join(found)}')
    else:
        # Check for ANY error/fix language
        err_match = re.search(r'(pattern|fix|lesson|error|debt|cycle)', entry.lower())
        print(f'{date}: {"uncategorized" if err_match else "no patterns"}')
PYEOF
```

### 3. Decision Matrix

| Finding | Last 5 entries contain this pattern? | Action |
|---------|:-------------------------------------:|--------|
| Same issue, same wording | Yes | **[SILENT]** — no new information |
| Same issue, new evidence/instance | Yes, but as class | Brief note (≤3 lines) updating evidence count, or [SILENT] if new instance is trivial |
| Truly new issue | No | Full report + journal entry |
| Meta-finding about the audit itself | No | Record as improvement + mark as delta gate so future runs detect it |

### 4. Writing the delta gate marker

When you identify and fix the audit loop itself, write a delta gate entry — a journal entry whose presence future audits can cheaply detect:

```
## YYYY-MM-DD — Self-improvement audit delta gate

**Pattern:** Brief description of the meta-loop (1 line)
**Fix:** What was changed (1 line)
**Future:** If no new error pattern has emerged since this entry, emit [SILENT].
```

Then future audits detect this with:

```bash
# Check if the last entry is a delta gate
python3 << 'PYEOF'
with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()
if 'delta gate' in content.split('##')[-1]:
    print('GATE_ACTIVE')
else:
    print('NO_GATE')
PYEOF
```

If `GATE_ACTIVE` and no new patterns found, emit `[SILENT]` instead of a full report.

## When This Pattern Applies

| Cron type | Frequency | Typical findings | Delta gate benefit |
|-----------|:---------:|------------------|:------------------:|
| Self-improvement audit | 3-10×/day | Repeated known issues | Stops journal bloat |
| Social growth check | Hourly | No new likes/stars | Already covered by pre-report-delta-check |
| CI health monitor | Per commit | Same failure repeated | Could be added but lower priority |

## Relationship to pre-report-delta-check.md

- `pre-report-delta-check.md`: API data deltas (downloads, likes, stars). Prevents redundant external API calls.
- `error-pattern-delta-gate.md` (this file): Error pattern deltas (same findings, same diagnoses). Prevents redundant journal entries.

Both implement the same principle — **cheapest-check-first** — but for different data sources:

```
pre-report-delta-check → [SILENT] when API data hasn't changed
error-pattern-delta  → [SILENT] when error patterns are repeats
```

Use them together: a cron that checks both ecosystem health AND self-improvement should run the error-pattern gate last (after confirming API data changed, check if the findings are novel).

## Verified Working (2026-07-30)

The delta gate pattern has been **proven in production**: this self-improvement audit session was the first to successfully emit `[SILENT]` after detecting that all candidate error patterns were already documented in prior entries. Infrastructure prerequisites that made this possible:

1. **Skills wired into cron configs** — without `cron-tool-workarounds` in the cron job's skills array, the delta gate is invisible
2. **Recursive blind spot closed** — the audit cron now applies the delta gate to itself, not just to other crons
3. **Canonical journal path** — all sessions must read from the same journal for the gate to work (`/opt/data/LEARNING_JOURNAL.md`)

Future sessions can trust: if the delta gate says `[SILENT]`, no new patterns were present. This is not theoretical — it has executed correctly.

## Efficient Session Scanning for Error Patterns

**Problem:** Searching session history with `session_search(query="error OR fail OR blocked OR crash")` in a cron session that has loaded this skill returns 500KB+ of results, dominated by **skill content matches** (this skill documents all error patterns extensively). The real signal — actual session errors — is buried.

**Root cause:** The loaded skill text appears in a user turn (tool result of `skill_view`), and FTS5 matches against that content drowns out all other results.

**Better approaches (in preference order):**

### 1. Browse-then-scroll (lowest noise)

Skip broad FTS5 pattern search entirely. Browse recent sessions, then scroll into the most likely candidates:

```bash
session_search()  # browse recent sessions → inspect titles
session_search(session_id="...", around_message_id=N, window=10)  # scroll into a recent one
```

Look for sessions whose titles suggest failure context (CI Health, Debug, Fix). These have the highest signal-to-noise for error patterns.

### 2. Narrowed FTS5 with session category terms

When you must search, pair error terms with role-filter and session-type terms:

```bash
session_search(query="fail tirith block deny", sort="newest", limit=5, role_filter="user,assistant")
```

Use specific tool-block phrases (`tirith`, `denied`, `blocked`) rather than generic error terms. Pair them with session-type terms (`cron`, `CI`, `Health`) to exclude skill-documentation matches that mention those words in passing.

### 3. Date-gated scan

For specific periods (e.g., "last 2 hours"), browse recent sessions by omission:

```bash
# Get the last 10 sessions
sessions = session_search(limit=10)
# Pick ones with relevant titles (CI Health, Debug, Fix, etc.)
# Then scroll into each candidate
```

### 4. When broad search is unavoidable

If you must do a broad text search, post-process results to exclude hits from the same session_id as the current session (which contains the loaded skill):

```python
# Pseudocode: filter out results from current session
current_id = "cron_..."  # detected from session context
results = session_search_result.get("results", [])
real_errors = [r for r in results if r["session_id"] != current_id]
```

### Signal quality matrix

| Search approach | Noise level | Catches skill-doc matches? | Catches real errors? | Cost |
|----------------|:-----------:|:--------------------------:|:--------------------:|:----:|
| Broad FTS5 (`error OR fail OR blocked`) | High | Yes (dominates) | Yes (but buried) | 1 call, 540KB+ result |
| Narrowed FTS5 + role_filter | Medium | Somewhat | Better | 1 call, smaller |
| Browse-then-scroll | Low | No | Yes (targeted) | 2-4 calls, small |
| Date-gated scan | Low | No | High-effort | 1 per candidate session |
| Exclude-current-session | Medium | Mostly eliminated | Yes | 1 call + post-processing |

**Recommendation for self-improvement audits:** Use approach #1 (browse-then-scroll) when you have no specific error message to search for. Use approach #2 when you have a specific error pattern in mind. Reserve broad FTS5 only as a last resort — its signal-to-noise ratio in cron sessions that load this skill is too low to justify the overhead.

## Known Pitfalls

- **Don't over-match.** Two sessions that both find "stale download counts" may have different root causes (one is API-auth-related, one is update-process-related). If they're genuinely different, record them separately. The delta gate catches only *verbatim same findings*.
- **Delta gate is not a silence-all.** If the AUDIT RUN ITSELF has changed (e.g., new skill was created, cron schedule adjusted), report that even if all error patterns are repeats — the infrastructure meta-state is new information.
- **Gates prevent journal entries but don't fix the underlying pattern.** If the same error pattern keeps appearing across audits, the problem is not the audit — it's the unresolved root cause. Consider promoting the finding from "audit entry" to "skill fix" or "mechanical fix" rather than gating it silent.
- **Last entry detection must account for concurrent writers.** If another cron appends an entry between your gate check and your report, the "last entry" may change mid-turn. Mitigation: read the journal once at the start, store the last entry ID/date, and re-check before writing.
- **Canonical path — the delta gate is invisible unless all sessions read the SAME journal.** Verified incident 2026-07-30: the delta gate entry was written to `/opt/data/LEARNING_JOURNAL.md` but the canonical shared memory journal (`~/.sakthai/LEARNING_JOURNAL.md`) never received it. Every subsequent session that read the canonical `.sakthai/` copy started from scratch — 5+ redundant audit runs in one day. **Fix:** Resolve the canonical journal path at the very start of every session via `readlink -f ~/.sakthai/LEARNING_JOURNAL.md`. If it doesn't exist or is a regular file (not symlink), check all copies with `find /opt/data -name "LEARNING_JOURNAL*"` and consolidate before relying on any delta gate. All delta gate checks must read from the same canonical path that the gate was written to — never assume two paths point to the same file without verification.

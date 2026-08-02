# append_journal.py Canonical Path Fix

## Problem (verified 2026-07-30)

The `append_journal.py` script at `~/.sakthai/append_journal.py` was patched in an earlier cycle to target `~/.sakthai/LEARNING_JOURNAL.md`. But the canonical journal — the one with the most entries and the one used by the `patch()` prepend workflow — is `/opt/data/LEARNING_JOURNAL.md`.

| Path | Entries | Status |
|------|:-------:|:------:|
| `/opt/data/LEARNING_JOURNAL.md` | 77 | Canonical (newest-first, used by patch() prepend) |
| `~/.sakthai/LEARNING_JOURNAL.md` | 39 | Stale copy (what append_journal.py writes to) |
| Shared between both | 3 | Only 3 entry titles overlap |

## Fix

Edit `~/.sakthai/append_journal.py` line ~23:

```python
# Before (wrong):
JOURNAL = os.path.realpath(
    os.path.expanduser("~/.sakthai/LEARNING_JOURNAL.md")
)

# After (correct):
JOURNAL = os.path.realpath(
    os.path.expanduser("/opt/data/LEARNING_JOURNAL.md")
)
```

## Why this matters

Every cron session that uses the PREFERRED method (`python3 ~/.sakthai/append_journal.py << 'ENTRY'`) writes to the `.sakthai/` copy, not the canonical. This guarantees continued divergence between the two files. Only the `patch()` prepend pattern (documented in SKILL.md §Prepend) operates on the correct canonical path.

## Verification after fix

```bash
# Confirm the script targets the canonical path
grep "JOURNAL =" ~/.sakthai/append_journal.py

# Test a dry write
echo "## Test entry" | python3 ~/.sakthai/append_journal.py
head -1 /opt/data/LEARNING_JOURNAL.md
# Should show "## Test entry" (assuming newest-first ordering)

# Clean up test entry
# (use patch() to remove it)
```

See also: `references/journal-fragmentation.md` for the full consolidation procedure (merge 12 copies, symlink stale paths, clean up .original files).

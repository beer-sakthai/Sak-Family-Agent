---
name: SakThai-journal-append
description: Write entries to LEARNING_JOURNAL.md safely — PREPEND for newest-first ordering (canonical), APPEND for chronological journals. Never use write_file directly.
trigger: Any task that says "record to LEARNING_JOURNAL.md", "save to LEARNING_JOURNAL.md", "write improvement to journal", or "prepend to journal"
---

# LEARNING_JOURNAL.md Safe Write Procedure

> **⚠ Note:** The skill name says "append" for historical reasons. The canonical journal uses **newest-first ordering** (prepend). See §Correct Pattern below.

## CRITICAL RULE

**Never use `write_file` on LEARNING_JOURNAL.md directly.** `write_file` is a **full file overwrite** — it destroys the entire accumulated history (currently 700+ lines across 2+ weeks of learnings). However, `write_file` IS safe for **temporary files** in the current working directory, which can then be appended to the journal via `cat >>`. See §Fallback below.

This has happened repeatedly:
- Jul 26: write_file destroyed the journal, restored from git HEAD
- Jul 30: write_file destroyed a 3,738-line journal, restored from backup
- Multiple audit cycles have flagged this same error

## DUAL JOURNALS — Different Paths, Different Ordering

There are two LEARNING_JOURNAL.md files in active use, each with different ordering conventions. **Determine which one you're writing to BEFORE choosing append vs prepend.**

### Journal A: Repo Root (Git-Tracked) — Chronological Ordering

- **Path:** `/opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md`
- **Ordering:** Chronological (oldest at top, newest appended at bottom)
- **Write method:** APPEND via `cat >>`
- **In git?** Yes — tracked in `beer-sakthai/Sak-Family-Agent`
- **Start content:** `# SakThai Ecosystem — Learning Journal`
- **Used for:** HF ecosystem reports, cron output, operational docs

**Do NOT prepend to this journal** — entries go at the bottom.

### Journal B: Persona Directory — Newest-First Ordering

- **Path:** `/opt/data/personas/sakthai/LEARNING_JOURNAL.md`
- **Ordering:** Newest-first (new entries at TOP, after title header)
- **Write method:** PREPEND (not append)
- **In git?** Partially — exists under `personas/sakthai/`
- **Start content:** `# SakThai Learning Journal`
- **Used for:** Personal agent learning journal

**Do NOT append to this journal** — entries go at the top.

> ⚠️ **Journal fragmentation history:** A third path (`~/.sakthai/LEARNING_JOURNAL.md`, 1,383 lines) existed as original shared-memory location. `/opt/data/LEARNING_JOURNAL.md` (290 lines) was another divergent copy. As of 2026-07-30 consolidation, the two tracked journals above are the active ones. The `.sakthai` and `/opt/data` root copies are stale.

## PATH DETECTION SENTINEL

Before writing, determine which journal you're working with:

```bash
head -3 /opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md
# If "SakThai Ecosystem" → Journal A (chronological, APPEND)
# If "SakThai Learning Journal" → Journal B (newest-first, PREPEND)
# If not found → check /opt/data/personas/sakthai/LEARNING_JOURNAL.md
```

**Never assume.** The two journals have opposite ordering conventions — using the wrong method places entries in the wrong chronological position. Always run the sentinel check before any write.

> ⚠️ **Check before writing:** `head -3` confirms both the file exists AND its ordering convention.

## Correct Pattern

### Primary (newest-first journal — Journal B, PREPEND)

Journal B at `/opt/data/personas/sakthai/LEARNING_JOURNAL.md` uses **newest-first ordering**: entries go at the TOP, after the `# SakThai Learning Journal` header. Confirm via sentinel check before using this pattern.

**Prepend via head + cat (for Journal B only):**

```bash
# 1. Write new entry to a temp file
write_file path="/opt/data/_journal_entry.md" content="...
## YYYY-MM-DD — Title

Content...
"

# 2. Prepend: title line + new entry + rest
head -1 /opt/data/personas/sakthai/LEARNING_JOURNAL.md > /tmp/_combined.md
cat /opt/data/_journal_entry.md >> /tmp/_combined.md
tail -n +2 /opt/data/personas/sakthai/LEARNING_JOURNAL.md >> /tmp/_combined.md
mv /tmp/_combined.md /opt/data/personas/sakthai/LEARNING_JOURNAL.md

# 3. Clean up
rm /opt/data/_journal_entry.md
```

**Inline Python prepend** (single terminal() call, no temp files):

```bash
python3 << 'PYEOF'
entry = """\
## YYYY-MM-DD — Title

Content...
"""
jpath = "/opt/data/personas/sakthai/LEARNING_JOURNAL.md"
with open(jpath) as f:
    title = f.readline()
    rest = f.read()
with open(jpath, 'w') as f:
    f.write(title)
    f.write(entry + "\n")
    f.write(rest)
print("Prepend done")
PYEOF
```

### Secondary (chronological journals — Journal A, APPEND)

Journal A at `/opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md` grows bottom-first (oldest at top). This is the repo-root journal used for HF ecosystem reports.

**cat >> with heredoc:**

```bash
cat >> /opt/data/TARGET_JOURNAL.md << 'JEOF'

---

## 2026-07-30 — Title

### Entry content here

JEOF
```

**Fallback (heredoc fails due to special chars):**

```bash
write_file path="/opt/data/journal_entry_pending.md" content="...
## YYYY-MM-DD — Title
..."
cat /opt/data/journal_entry_pending.md >> /opt/data/TARGET_JOURNAL.md
rm /opt/data/journal_entry_pending.md
```

**Important:** write_file is safe for temp files — only the journal itself must never be written directly with write_file. `/tmp` is treated as a protected system path by write_file; always use the current working directory for temp files.

## Verification

After prepend (Journal B, newest-first):

```bash
head -8 /opt/data/personas/sakthai/LEARNING_JOURNAL.md
wc -l /opt/data/personas/sakthai/LEARNING_JOURNAL.md
```

After append (Journal A, chronological):

```bash
tail -5 /opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md
wc -l /opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md
```

## Why write_file is Wrong

`write_file` replaces the ENTIRE file with only what you passed. If you only read the last 50 lines of a ~1,160-line file and then write_file, you lose 1,100+ lines of history.

`cat >>` appends content to the file end (for chronological journals). For newest-first journals, use the prepend pattern above — `cat >>` places entries at the wrong position.

## Pitfalls

1. **Path detection discipline.** Run the sentinel check (`head -3`) before every write. Journal A is at `/opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md` (chronological, append). Journal B is at `/opt/data/personas/sakthai/LEARNING_JOURNAL.md` (newest-first, prepend). Using the wrong method on the wrong journal breaks ordering. CWD-relative or symlink-based paths silently point to the wrong file (fragmentation history had 5+ divergent copies).
2. **Empty appends.** If the content is empty, the file gets a blank newline — harmless but noisy. Always include content between the start and end markers.
3. **Heredoc delimiter collision.** If the entry contains the word `JEOF` on its own line, the heredoc terminates early. Use `'ENDOFENTRY'` for entries with code blocks containing shell-ish content.
4. **Missing trailing newline before delimiter.** The delimiter must be on its own line at column 0. The pattern in §Correct Pattern handles this.
5. **Special characters in heredoc body.** Even with a quoted delimiter (`'JEOF'`), certain shell-special characters (`&`, backticks, `$()` — anything that triggers shell parsing before the heredoc quoting takes effect in the terminal tool's scanner) can cause the command to be rejected with "Foreground command uses '&' backgrounding" or similar errors. Use the write-then-append fallback pattern when the entry body contains these chars.
6. **/tmp is write-protected.** The write_file tool rejects writes to `/tmp` (protected system path). Always create temp files in the current working directory (e.g., `/opt/data/journal_entry_pending.md`).

7. **Concurrent patch insertion — `patch()` inserts at old_string position, not end-of-file.** When the journal has been modified by a concurrent cron between your `read_file` and your `patch()` call, the old_string still matches (fuzzy), but the insertion point is mid-file — not the actual end. The entry appears in the wrong chronological position. Verified 2026-07-30: `patch()` reported success but inserted the ecosystem report entry at line 877 instead of after the last entry (which had moved to line 1,006+). **Fix:** Always re-read the target section before `patch()` append — or use `cat >>` heredoc which is position-independent (always appends to the actual OS file end).

8. **Python prepend is a read-modify-write race — two concurrent crons can lose one entry.** The Python prepend pattern (read → modify → write) is NOT atomic. If two crons run the prepend simultaneously:
   - Cron A reads the file (gets current content)
   - Cron B reads the file (same content)
   - Cron A writes back (A's entry + old content)
   - Cron B writes back (B's entry + old content) — **A's entry is silently lost** because B overwrote A's write with B's stale `old content`
   Verified 2026-07-30: Cron #021 written at line 9 instead of line 2 because another cron's entry was in the file between the read and write. No data was lost in this instance, but the ordering was wrong — and the next concurrent instance could lose an entry entirely.
   **Mitigations (none are perfect, layer them):**
   - **Stagger cron schedules** so journal-writing crons don't overlap (e.g., space them 10+ minutes apart)
   - **Use `cat >>` heredoc instead** for Journal A (chronological) — OS-level append is atomic and always writes at the true end-of-file regardless of concurrent writers
   - **For Journal B (prepend):** accept the risk and rely on staggering, because there is no portable atomic-prepend operation. The `head + cat + mv` shell pipeline has the same race — `mv` is atomic but the read isn't.
   - **Verify after write:** after prepending, read back the first 5 lines to confirm your entry landed at the top and no sibling entries were lost

## Alternative: patch (⚠️ position risk for newest-first journals)

You can also use `patch(action='replace')` with old_string targeting the FIRST LINE of the journal (the `# Learning Journal` header) for a prepend — but this is fragile because `patch()` uses fuzzy matching and may match a duplicate `#` header elsewhere. Only use this for simple one-line additions.

For newest-first journals, `patch()` targeting the `# Learning Journal` header can work for prepending, but **`patch()` inserts at old_string position** — it does not inherently move content to the top. The match MUST be the unique first line.

**⚠️ Concurrent-write pitfall (append pattern):** When multiple cron jobs write to the journal simultaneously with append, `patch()` may insert your entry at the wrong position. The tool finds the old_string (fuzzy match) and replaces it — but if another cron appended content between your read and your write, the old_string is no longer the last line. Your entry lands in the middle of the file, not at the end. Prefer `cat >>` heredoc for append which always appends to the actual OS-level end-of-file regardless of concurrent activity.

## Related

- `sakthai-journal-append/references/` — entry-type templates for different journal entry categories

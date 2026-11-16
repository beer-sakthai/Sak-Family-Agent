# Prepend to Newest-First Journal — Complete Workflow

Some journals (including `/opt/data/LEARNING_JOURNAL.md`) store entries `newest-first` — the latest entry is at the top, just below the `# Learning Journal` header. For these, append patterns add to the wrong end.

## Detection — verify ordering before choosing append vs prepend

```bash
head -3 /opt/data/LEARNING_JOURNAL.md
grep -n "^## " /opt/data/LEARNING_JOURNAL.md | head -3
```

If the newest entry is at line 3 (top) → **prepend**. If at the bottom → **append**.

## Prepend Pattern — patch() with Header + First Entry Anchor

Replace the header + first entry anchor with header + new entry + anchor:

```patch
patch(
  old_string="# Learning Journal\n\n## 2026-07-30 — Old Entry Title",
  new_string="# Learning Journal\n\n## 2026-07-30 — New Entry\n\nContent...\n\n## 2026-07-30 — Old Entry Title"
)
```

**Why `patch()` for prepend:**
- No tirith blocks (managed tool, not shell command)
- No temp files — single tool call
- No race condition — atomic operation
- Reliable anchor — `# Learning Journal\n\n## ...` is usually unique

**Caveats:**
- Requires the `##` title to be unique across the file. If two entries share the same title, include date or a unique content line in old_string.
- For large new entries (>50 lines), the patch string becomes unwieldy. Use two-step snippet workflow instead: `write_file` snippet → `cat snippet >> TARGET.md` (but this appends, not prepends — use patch or the Python stdin-redirect approach).
- `patch()` with newlines in strings needs no escaping in the skill tool (literal newlines work), but in terminal use base64-encode or `printf` with `%b` escapes.

## Failure Mode — old_string Not Unique (Found N Matches)

The typical anchor `# Learning Journal\n\n---\n\n## 2026-07-30 — Title` can fail with "Found N matches" when:
- The same title string appears elsewhere in the journal (common in long journals)
- The fuzzy matcher finds partial matches against other content
- `---\n##` pattern is common enough to collide with other entries

### Escalation path

1. **Verify collisions:** `grep -c "2026-07-30 — Title" /opt/data/LEARNING_JOURNAL.md`. If >1, the title isn't unique — find a better anchor.
2. **Fallback anchor:** Instead of the title, use a **unique sentence from the entry body** — a specific observation, number, or metric that clearly appears only once. Include 1-2 lines of surrounding context for uniqueness.
3. **⚠️ Structural risk with body anchors:** When old_string starts in the entry body (after `## Title\n\n`), the `##` title line is NOT part of the match and will be orphaned. You must either:
   - Include `## Title\n\n` in both old_string and new_string (preferred), OR
   - Run a follow-up patch to fix the orphaned title afterward (see Recovery below).
4. **If all anchors fail** (unlikely but possible with very repetitive journal content), use the Python stdin-redirect approach in this file's companion reference `references/prepend-journal-stdin-redirect.md`.

## Recovery — Fixing Structural Issues After a Patch

When a prepend patch succeeds but leaves structural problems, fix incrementally:

### Symptom 1: Orphaned `##` title

The old entry's `## Title` remains on its own line with no content below it (the content was consumed by the patch match boundary).

**Fix:** Replace the orphaned title with a `---` separator:
```
patch(old_string="## 2026-07-30 — Orphaned Title\n\n###", new_string="---\n\n###")
```

### Symptom 2: Missing `---` separator between entries

The new entry ends abruptly and the old entry content starts right after.

**Fix:** Insert the separator:
```
patch(old_string="last line of your new entry\n\n### Old Section",
      new_string="last line of your new entry\n\n---\n\n### Old Section")
```

### Symptom 3: Duplicate `###` headers stacked

Two section headers appear on consecutive lines with no content between (happens when old_string ended at `### What was discovered` and new_string also started with another `###` header).

**Fix:** Remove the duplicate:
```
patch(old_string="### What was discovered\n### The Story in Numbers",
      new_string="### The Story in Numbers")
```

### Symptom 4: Content dropped at boundary

Text adjacent to the match boundary was silently dropped by fuzzy matching.

**Fix:** Read the affected section, reconstruct the lost content from your session transcript or the original API data, and reinsert with patch():
```
patch(old_string="surviving text before the gap\ntext after the gap",
      new_string="surviving text before the gap\nRECONSTRUCTED LOST TEXT\ntext after the gap")
```

## Verification — Full Boundary Integrity Check

After prepending (and any recovery patches), run the 3-point check:

```bash
# 1. New entry title appears first?
head -5 /opt/data/LEARNING_JOURNAL.md

# 2. Separator between entries?
grep -n "^---" /opt/data/LEARNING_JOURNAL.md | head -3

# 3. Both entry titles present?
grep -n "^## " /opt/data/LEARNING_JOURNAL.md | head -3
```

Confirm:
- New entry's `##` title is the first heading after `# Learning Journal\n\n---`
- Exactly one `---` separator between the new entry and the one below it
- Next entry's `##` title is intact (not corrupted by fuzzy-match boundary overlap)
- File is readable — no orphaned fragments, no duplicate headers

## Prevention — Avoid Needing Recovery Altogether

1. **Always include `## 2026-07-30 — Title\n\n`** in BOTH old_string and new_string. This ensures the title is never orphaned.
2. **Verify old_string uniqueness** before calling patch: `grep -c "anchor text" journal.md`. If >1, choose a longer anchor.
3. **Prefer sentences over titles** as anchors when titles are short or generic. A sentence like `"The two smallest models (1.5B and 0.5B) account for 51%"` is nearly guaranteed unique.
4. **After every patch() call, run the 3-point check** before proceeding to the next step. A broken prepend discovered immediately costs 1 patch to fix. A broken prepend discovered 3 sessions later requires manual reconstruction.

## Alternative — Python Stdin Redirect (Avoids patch() Entirely)

See `references/prepend-journal-stdin-redirect.md` for a Python-based approach that reads the file, inserts the new entry at position N, and writes back — avoiding all patch() fuzzy-matching issues.

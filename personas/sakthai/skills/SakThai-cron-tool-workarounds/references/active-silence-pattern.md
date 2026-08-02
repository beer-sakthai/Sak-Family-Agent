# Active-Silence Pattern — After [SILENT]

## Problem

The self-improvement audit delta gate prevents journal bloat by emitting `[SILENT]`
when no new error patterns are found. But [SILENT] creates a secondary problem:
the audit finishes having done nothing — a missed learning opportunity.

The user explicitly called this out: *"A pass that does nothing is a missed
learning opportunity, not a neutral outcome."*

## Rule

`[SILENT]` means "don't append a journal entry." It does NOT mean "do nothing."

Immediately after a [SILENT] decision, run a **lightweight skill scan**:

### Step 1: Scan loaded skills for missing steps

If this session loaded any skill (e.g. `cron-tool-workarounds`), check whether
the skill was missing a workaround, pitfall, or trigger that the session's
actual execution needed. Example: "I loaded `cron-tool-workarounds` but still
hit X blocked pattern that the skill doesn't document."

**If found:** Patch the skill with `skill_manage(action='patch')`.

### Step 2: Check for un-captured technique

Did the session use a non-obvious tool pattern? Common examples:
- `tempfile.NamedTemporaryFile` for one-shot verification scripts
- `python3 -c "open(path,'a').write(content)"` for inline append
- `browser_console(expression=...)` for last-resort JSON extraction
- Two-step curl → Python for tirith-safe API calls

**If found:** Add a reference file or pitfall note to the governing skill.

### Step 3: Minimum one skill touch

If steps 1–2 find nothing, add a **lightweight reference file** under an
existing umbrella skill anyway. A one-paragraph note about what was checked
and confirmed working qualifies:

```
skill_manage(action='write_file',
  name='cron-tool-workarounds',
  file_path='references/delta-gate-verified-YYYY-MM-DD.md',
  file_content='# Delta Gate Verified: YYYY-MM-DD\n\nConfirmed...')
```

### Step 4: Annotate the output

If you patched a skill or added a reference, include a one-line annotation
in the cron delivery:

```
[skill: cron-tool-workarounds patched]  or  [ref: active-silence-pattern added]
```

This lets the user know the audit was productive despite finding no new patterns.

## Why This Matters

A self-improvement audit that finishes without touching a single skill is the
audit's own form of "diagnose without fixing" — the very pattern the audit is
supposed to detect. The active-silence pattern breaks this loop by requiring
at least one incremental improvement per session, even when nothing is broken.

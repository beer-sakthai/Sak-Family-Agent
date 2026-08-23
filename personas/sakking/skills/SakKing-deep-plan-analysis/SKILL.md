---
name: SakSit-deep-plan-analysis
description: "Audit and diagnose PLAN.md files with deep analysis."
---

# Deep Plan Analysis — Discover, Audit, Diagnose

Scan the environment for every PLAN.md and analysis document, classify them by
type and staleness, perform deep-dive reading on the most important plans, and
optionally delegate file diagnosis to Claude Code. Produces a structured
inventory report with a priority-ordered fix list.

**What it does NOT do:** It does not modify or edit plan files — it produces
understanding and a report. Editing the plans is a separate follow-up task.

## When to Use

- User asks "audit all plans", "check plan health", or "list every PLAN.md"
- You need to understand the full planning landscape before starting work
- Plans have stale dates, inconsistent markers, or unverified "✅ Done" claims
- User wants a Claude Code diagnostic pass on a specific plan file
- Cross-referencing what plans say against what actually exists on disk

## Prerequisites

- Read access to the target filesystem (usually `/opt/data/` or project root)
- `search_files`, `read_file`, `terminal` Hermes tools
- *Optional:* Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
  for the diagnosis phase — skip if unavailable

## How to Run

```python
# Full pipeline: discover → classify → deep-dive → diagnose → report
deep_plan_audit(scan_path="/opt/data", diagnose=False)
```

Invoke through `execute_code` for the full automated pipeline, or step through
manually with `search_files` + `read_file` + `terminal`.

## Quick Reference

| Phase | Hermes Tool | What Happens |
|-------|-------------|--------------|
| 1. Discover | `search_files("PLAN.md")` + `search_files("*audit*")` | Find all plan/analysis files |
| 2. Classify | `read_file` each | Categorize (canonical/stale/business) |
| 3. Deep-dive | `read_file` + `search_files` on key plans | Cross-reference claims vs disk |
| 4. Diagnose | `delegate_task` or `terminal(claude -p ...)` | Claude Code analysis (optional) |
| 5. Report | `write_file` | Save structured inventory + fix list |

## Procedure

### Phase 1 — Discover All Plan Files

Search broadly across the working environment:

```python
# Find every PLAN.md
from hermes_tools import search_files, read_file, terminal, write_file

plans = search_files(pattern="PLAN.md", path="/opt/data", target="files")
analysis = search_files(pattern="*audit*", path="/opt/data", target="files")
review = search_files(pattern="*review*", path="/opt/data", target="files",
                      file_glob="*.md")
```

Combine results into a single inventory list. Remove `node_modules/` and other
dependency trees.

### Phase 2 — Classify Each Plan

Read every discovered file (first 20-30 lines is usually enough for
classification). For each plan capture:

| Signal | How to Get It |
|--------|---------------|
| Purpose (1-line) | Read first 5 lines — the title/intro |
| Type | Canonical repo master? Sub-plan? Self-evolution? Stale duplicate? Business doc? |
| Last modified | `terminal("stat -c '%y' <path>")` |
| Status markers | Scan for ✅, 🚧, ❌, `[x]`, `[ ]` patterns |
| Claimed completeness | Count done vs pending items |
| Cross-links | Scan for `./path` or `[link](../path)` references |

Use the classification from the plan-inventory-audit reference:

| Type | Description | Example Path |
|------|-------------|-------------|
| `canonical-master` | Root-level project PLAN.md | `Sak-Family-Agent/PLAN.md` |
| `canonical-sub` | Sub-area plan within the repo | `Sak-Family-Agent/product/PLAN.md` |
| `self-evolution` | Agent skill-evolution plan | `personas/*/agent-self-evolution/PLAN.md` |
| `profile-plan` | Per-agent operational plan | `profiles/sakjules/PLAN.md` |
| `business-doc` | Marketing/outreach plan | `house-of-sak-report/*PLAN*` |
| `stale-duplicate` | Old checkout mirror | Duplicate outside canonical path |

### Phase 3 — Deep-Dive on Canonical Plans

For each canonical-master and canonical-sub plan, do a full read and
cross-reference against disk:

```python
# For each claimed "✅ Done" item, verify it exists on disk
# Check: does the file/feature actually have logic?
terminal("ls -la <claimed_path> 2>/dev/null")
search_files("def ", path=claimed_path, file_glob="*.py")
```

Build a "plan vs reality" comparison table:

```
| Plan Says | On Disk | Status |
|-----------|---------|--------|
| persona/sakking/SOUL.md | ✅ exists | Verified |
| product/ServiceQuoteBot | ✅ exists + code | Verified |
| featureX | ❌ not found | Missing |
```

### Phase 4 — Optional: Claude Code Diagnosis

If the user wants a diagnostic pass on specific files, invoke Claude Code
through the `claude-code` skill. Two modes:

**Mode A — Print mode (non-interactive, preferred):**

```python
terminal(
    command="claude -p 'Read /opt/data/Sak-Family-Agent/product/PLAN.md and diagnose issues: stale dates, inconsistent markers, unverified claims, missing cross-links. Output a structured diagnosis with severity levels.' --allowedTools 'Read' --max-turns 3",
    timeout=60
)
```

**Mode B — Batch diagnosis on multiple files via delegate_task:**

```python
# One Claude per plan file, runs in parallel
from hermes_tools import delegate_task

delegate_task(
    goal="Read PLAN.md and run Claude Code diagnosis",
    context=f"""
    Files to diagnose: {priority_plans}
    For each file: check for stale dates, inconsistent status markers,
    unverified completion claims, missing cross-references. Assign each
    issue a severity (HIGH/MED/LOW).
    """
)
```

### Phase 5 — Synthesize and Save Report

Consolidate findings into a structured report file:

```markdown
# Deep Plan Analysis — <Date>

## Inventory
- Total PLAN.md files: N
- Analysis/audit files: N
- Canonical plans: N
- Stale duplicates: N
- Business docs: N

## Classification Table

| # | Path | Type | Modified | Health | Issues |
|---|------|------|----------|--------|--------|
| 1 | ... | canonical-master | Jul 6 | ⚠️ | 3 (stale markers, missing dates) |

## Health by Area

### Canonical Master Plans (N files)
| Plan | Items Done/Total | Last Update | Issues | Verdict |
|------|-----------------|-------------|--------|---------|
| ... | 8/10 | Jul 6 | 3 | :warning: Needs cleanup |

### Self-Evolution Plans (N files)
| Agent | Last Modified | Identical Copy? | Issues |
|-------|--------------|-----------------|--------|
| saksit | Jul 2 | Yes | Likely copy-paste |

### Stale Duplicates (N files → can delete)
| Path | Original | Action |
|------|----------|--------|
| ... | ... | Delete after verifying no unique history |

## Claude Code Diagnosis Results
*Summary of any issues flagged by the diagnostic pass*
- File X: HIGH — claim "✅ Done" but feature missing on disk
- File Y: MED — inconsistent marker mix (✅ + [x] + [ ])
- File Z: LOW — last updated 2 weeks ago, no date on completed items

## Priority Fix List
1. **HIGH** — [File A]: [Specific issue + fix]
2. **MED** — [File B]: [Specific issue + fix]
3. ...
```

Save to a known location: `profiles/saksit/deep-plan-analysis-<date>.md`

## Pitfalls

- **Plans are aspirational.** A ✅ marker ≠ implemented code. Always verify on disk.
- **Self-evolution plans are often copy-pasted across agents.** Check if they're
  identical — personalization needed, not individual edits.
- **Duplicate checkouts inflate the count.** `repo-push/`, old mirror clones
  produce stale duplicates. Classify separately.
- **Mixed status markers.** Some plans use ✅, others `[x]`, `[ ]`, or emoji.
  Normalize into a single notation when reporting.
- **Claude Code print mode limit.** `--max-turns 3` keeps it focused and cheap
  for diagnosis. Don't over-allocate.
- **/root/ is usually inaccessible** in sandbox/container environments. Scope
  the scan to the working directory (/opt/data/) instead.
- **node_modules/ noise.** Add exclusion patterns when discovering files.

## Verification

After running a deep plan analysis, you should be able to answer:

- How many PLAN.md files exist across the environment?
- How many are canonical, stale, or business docs?
- What percentage of claimed-done items are actually verified on disk?
- Which plans have the most issues and what are they?
- Where is the saved report file?

## Related Skills

- `deep-dive-analysis` — general-purpose code/doc analysis (used in Phase 3)
- `claude-code` — Claude Code orchestration (used in Phase 4)
- `plan` — Plan mode for writing new PLAN.md files (complementary output)

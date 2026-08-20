---
name: SakSit-project-plan-maintenance
description: Audit and standardize PLAN.md files across projects.
...
---

# Project-Plan Maintenance

A systematic workflow for maintaining PLAN.md files in a multi-plan project.
Prevents the common decay pattern: mixed markers, orphaned references,
unarchived completed phases, and stale duplicate files.

## When to Trigger

- User says "plan?" as an opening message — indicates they want to know
  and clean up the current project state
- User says "audit the plans" / "check the plans" / "plans are stale"
- After 5+ days since the last plan update (plans drift quickly)
- Before any major project phase transition

## Workflow

### Step 1: Discover All PLAN.md Files

Find every PLAN.md in the project tree:

```bash
find /opt/data -maxdepth 5 -name "PLAN.md" -type f 2>/dev/null | sort
```

Categorize results:
- **Canonical** — in the primary project repo (e.g., `Sak-Family-Agent/`)
- **Stale duplicates** — in old checkouts, backup copies, stale mirrors (e.g., `repo-push/`, `profiles/*/sak-family-agent/`)
- **Active non-project** — standalone plans (e.g., `house-of-sak-report/`)

### Step 2: Audit Each Canonical Plan

For each plan file in the canonical set, check:

| Check | What to look for |
|-------|-----------------|
| **Markers** | Mixed `✅` and `[x]` or other status conventions — standardize all to one format |
| **Dates** | Completed items dated but recent items missing dates — add timestamps |
| **Stale content** | Phases marked done still showing individual task checklists — archive into summary |
| **Cross-links** | Master plan should list all sub-plans with status indicators; sub-plans should link back |
| **Story count** | Does the plan still reflect what was ACTUALLY built, not just what was planned? |
| **Outdated references** | Repo locations, file paths, tool names that have changed since the plan was written |

### Step 3: Fix Marker Consistency

Standardize all status markers:

| Before | After |
|--------|-------|
| `[x]` or `[X]` | `✅` |
| `[ ]` or `☐` | keep as `[ ]` or convert to todo marker |
| Mixed `✅` and `[x]` in same table | All to `✅ Done (date)` |

Apply consistently to maintain visual consistency.

### Step 4: Archive Completed Phases

When a phase's tasks are all checked off:

- Replace the detailed checklist with a **one-paragraph summary**
- Collapse multiple phases into a single "Phases X–Y Completed" header
- Keep the completion date visible in the header
- Preserve the original checklist content in a `references/` file under a plan-maintenance skill if the detail is valuable

Pattern:
```
## 🚀 Phases — Topic Name ✅ (Completed YYYY-MM-DD)

All [N] phases completed — brief summary of what was accomplished.

### Phase X-Y Summary
- **Phase X** — brief description ✅
- **Phase Y** — brief description ✅

---
```

### Step 5: Add Cross-Links

The master plan should have a sub-plans table:

```
## 📋 Sub-Plans

| Plan | Location | Status |
|---|---|---|
| Product & Monetization | [`product/PLAN.md`](./product/PLAN.md) | 🟡 Active |
| SakJules — skills | [`personas/sakjules/PLAN.md`](./personas/sakjules/PLAN.md) | ✅ Complete |
| ... | ... | ... |
```

Status indicators: 🟢 Active, 🟡 Active — needs updates, ✅ Complete, 🔴 Overdue

### Step 6: Clean Stale Duplicates

Delete plan files from old checkout copies:

- `repo-push/` — stale mirror of old commits
- `profiles/*/sak-family-agent/` — stale profile-level copies
- Any file whose content is identical to a canonical plan and lives outside the canonical tree

Always verify with `find` first, then delete only confirmed stale copies. When in doubt about a file's purpose, read its content first.

### Step 7: Save the Audit

Write a complete audit file to document what was found and fixed:

```markdown
# Project Plan Audit — Definitive Checklist
> Saved YYYY-MM-DD · Verified by reading every canonical PLAN.md

## CANONICAL PLANS — N files

### P1 — Master PLAN.md
**Path:** ...
**Issues found:**
- [x] Marker consistency
- [x] Stale content
- ...

## STALE DUPLICATES — N files
| Location | Count | Action |
|----------|-------|--------|

## SUMMARY
| Category | Count |
|----------|-------|
| Total PLAN.md files | N |
| Canonical | N |
| Stale duplicates removed | N |
| Issues fixed | N |
```

## Pitfalls

- **Don't confuse canonical with stale.** The primary repo path must be identified before deciding what's a duplicate. Read the first few lines of each PLAN.md to determine origin.
- **Don't delete non-plan content.** Only remove PLAN.md files — never remove AGENTS.md, SOUL.md, README.md, or content files that happen to be near stale plans.
- **Archiving vs. deleting.** Completed phases should be COMPRESSED into summaries, not simply deleted. The completion record matters for context.
- **Sub-plans need visibility.** Master plan must list every sub-plan with its status — otherwise sub-plans become orphaned and drift.
- **Plans age fast.** After creation, plan files are stale within 5–7 days if not updated. Schedule a monthly audit.
- **Coordinate with concurrent authors.** If a subagent is also working on plan files, don't overwrite each other's changes. Check modification times before editing.
- **"plan?" from Beer = status report, not new plan.** When Beer opens with "plan?" he wants to know the current state. Audit existing plans and report back concisely. Don't ask "what plan?" — build the audit from discovery.

## Verification

After all fixes:

- [ ] All canonical plans have consistent marker style (✅ not [x])
- [ ] Completed phases reduced to summary paragraphs
- [ ] Master plan lists every sub-plan with status
- [ ] Sub-plans have back-links to master
- [ ] All stale duplicate PLAN.md files deleted
- [ ] Audit report written
- [ ] Count of remaining PLAN.md files documented
- [ ] Health score noted (out of 10)

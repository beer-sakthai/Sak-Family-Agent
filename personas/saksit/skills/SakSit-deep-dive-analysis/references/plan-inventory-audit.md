# Plan Inventory Audit

Estate-wide audit of all PLAN.md files across a filesystem: discover, categorise, verify, and produce a durable report the user can recount from.

## When to Use

- User asks "check all plans", "audit the plan estate", "list plan that for sure"
- User wants a definitive inventory of what planning docs exist vs what's stale
- Before a cleanup/consolidation effort — need to know what's canonical vs duplicate
- User says "keep note for recounting" — they want a saved file they can refer back to

## Procedure

### Step 1 — Discover All PLAN.md Files

Cast a wide net across the entire workspace:

```python
search_files(pattern="PLAN.md", path="/opt/data", target="files")
```

This returns everything. Expect 20-40+ files in an established project.

### Step 2 — Locate the Canonical Repository

The canonical repo is the one the project actually uses. For Sak-Family-Agent it's `/opt/data/Sak-Family-Agent/`. Plans outside this are either:
- **Stale duplicates** — from old checkouts (`repo-push/`, `profiles/saksit/sak-family-agent/`)
- **Profile-level plans** — per-agent operational plans
- **Business/marketing plans** — House of Sak reports, outreach docs

### Step 3 — Read Every Canonical Plan

Read each PLAN.md inside the canonical repo path. For each one extract:

| Signal | What to Note |
|--------|-------------|
| Purpose | What is this plan for? |
| Status markers | Are they consistent? (✅ vs [x] vs [ ]) |
| Dates | When was each item last updated? |
| Cross-references | Does it link to sub-plans? Do they link back? |
| Claimed completeness | Does it say everything is done? |
| Staleness | When was the file last modified? |

Pro tip for verifying identical copies: check file sizes via `terminal("wc -c <files>")` — if sizes match exactly, the files are byte-identical copies.

### Step 4 — Categorise

Build a table like:

| Path | Type | Status | Action Needed |
|------|------|--------|-------------|
| Sak-Family-Agent/PLAN.md | Canonical master | Stale (Jul 6) | Fix markers, add dates |
| Sak-Family-Agent/product/PLAN.md | Canonical sub-plan | Stale (Jul 2) | Archive done phases |
| repo-push/PLAN.md | Stale duplicate | Old checkout | Delete |
| profiles/saksit/sak-family-agent/PLAN.md | Stale duplicate | Old checkout | Delete |
| house-of-sak-report/PLAN.md | Active business plan | Current | None |

### Step 5 — Verify Claims Against Reality

For each claimed-done item in canonical plans, check disk:

```python
# Does the file/feature actually exist?
search_files(feature_name, target="files")
# Is there actual logic or just stubs?
search_files("def ", path=feature_path, file_glob="*.py")
```

### Step 6 — Synthesise Priority-Ordered Fix List

Consolidate findings into a single sorted list from most impactful to least. Each item should name the plan, the issue, and the specific fix.

Format:

```markdown
## 🔴 Priority N — [Short Name]

**Path:** `/full/path/to/PLAN.md`
**Issue:** What's wrong (be specific)
**Fix:** Exact action needed
```

### Step 7 — Save Durable Report

Write the complete audit to a known path so the user can recount:

```markdown
# Plan Audit — <Date>

- Total PLAN.md files found: N
- Canonical location: <path>
- Issues found: N
- Stale duplicates: N
- Priority fix list: (1..N)
```

Save to `profiles/saksit/PLAN-AUDIT.md` for SakSit sessions, or similar per-profile location.

## Pitfalls

- **Plans are aspirational.** A "✅ Done" marker ≠ anything actually built. Always verify on disk.
- **Self-evolution plans are often copy-pasted.** Check if all agent plans are identical — if so, they need personalisation, not individual updates.
- **Duplicate checkouts inflate the count.** `repo-push/`, `profiles/*/sak-family-agent/` are stale mirrors. Don't confuse them with canonical plans.
- **Mixed status notation.** Some items use `✅`, others `[x]`, others `[ ]`. Normalise when reporting.
- **Missing dates.** Completed items without dates are unverifiable. Note this as a finding.
- **Master plan lists sub-plans but sub-plans rarely link back.** Note missing cross-links as a finding.

## Output Checklist

After an audit, the user should be able to answer:
- How many PLAN.md files exist in total?
- Which ones are canonical?
- How many are stale duplicates?
- What needs fixing and in what order?
- Where is the saved audit file?

## Example Output Structure

```
PLAN AUDIT — July 7, 2026
==========================

Layer 1: Canonical Plans (in Sak-Family-Agent/)
  5 locations, 10 issues found

Layer 2: Stale Duplicates (~15 files)
  repo-push/ — 7 files (delete)
  profiles/saksit/sak-family-agent/ — 4 files (delete)

Layer 3: Active Business Plans (3 files, no action needed)

Priority Fix Order:
  1. Master PLAN.md — standardise markers, add dates
  2. Product PLAN.md — archive done phases
  3. All 6 self-evolution plans — personalise per-agent
  ...

Health Score: 4/10
```

# SOUL.md Narrative Consistency Audit

When an agent's status changes (added, deleted, renamed), propagate that change across ALL persona SOUL.md files so every agent describes the same family.

## Procedure

### 1. Identify the authoritative source
The **README.md** family table is the truth. Check it before changing anything:
```bash
grep -A 20 'The Family' README.md | grep -E 'Sak.*(🟢|🔴|Active|Deleted)'
```

### 2. Locate all SOUL.md files
```bash
find personas/ -name 'SOUL.md'
```

### 3. Find stale sibling references
Grep for the deleted/renamed agent's name in sibling/fellow context only:
```bash
grep -n 'AgentName\|AlternateName' personas/*/SOUL.md | grep -i 'sibling\|fellow\|agents'
```

Filter out:
- **Own SOUL** — an agent's own name is expected in its identity section
- **Legitimate non-sibling mentions** — e.g. `SakJules-` skill prefixes, role references ("business strategy assigned to SakTan")
- **Historical context** — e.g. "formerly had its own repo" in README

### 4. Check each SOUL's identity section
Every SOUL has an `## Identity` block with a sibling/fellow agents line. The format varies:
- `personas/sakthai/SOUL.md`: `My sibling agents are **SakX**...`
- `personas/sakking/SOUL.md`: `My fellow agents include **SakX**...`
- `personas/saksit/SOUL.md`: `My sibling agents are **SakX**...`
- `personas/saksee/SOUL.md`: `My sibling agents are **SakX**...`
- `personas/sakjules/SOUL.md`: `My sibling agents are **SakX**...`

### 5. Patch methodically
For each stale reference, remove the deleted agent from the list. If removing an Oxford-comma list, adjust punctuation:

**Before:** `**SakA**, **SakB**, **SakC**, and **SakD**`
**After removing C and D:** `**SakA**, and **SakB**`

Keep the `and` conjunction before the last remaining item.

### 6. Verify exhaustively
```bash
grep -n 'DeletedName' personas/*/SOUL.md | grep -i 'sibling\|fellow\|agents'
# Expected: zero results
```

Then check non-sibling mentions are still correct (e.g., `SakTan` in a role-description context).

### 7. Record
Add an entry to `LEARNING_JOURNAL.md` with:
- Finding (which files had stale references)
- Files fixed and what changed
- Verification confirmation

## Common pitfalls

- **SakThai SOUL.md** uses `sibling agents`, **SakKing SOUL.md** uses `fellow agents` — different grep patterns needed
- **SakJules SOUL.md** itself exists but its agent is deleted. Its sibling list still needs fixing even though it's a deleted agent's own SOUL
- **Line-break differences** between files — some SOUL.md identity blocks are multi-line. Use `read_file` with offset to see exact text before patching
- **Skills named after agents** — `SakJules-github-stewardship` is a skill, not a sibling reference. Don't flag it
- **Model/artifact references** — `sakthai-context-7b-tools` is a model name, not a sibling

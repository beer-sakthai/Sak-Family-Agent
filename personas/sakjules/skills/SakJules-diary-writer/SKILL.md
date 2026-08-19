---
name: SakJules-SakSit-diary-writer
description: Write project diaries and commit them to GitHub.
...
---

# Diary Writer — Session Documentation & GitHub Backup

Writes structured diary entries documenting what was done in a session — research, decisions, discoveries, reflections — and commits them to the `beer-sakthai/house-of-sak` GitHub repo under `diaries/<agent-name>/` for safekeeping. Uses the established House of Sak diary format (agent name, date, cycle workflow, key discoveries, reflection, signed footer). Does NOT write code documentation or READMEs — those belong in other skills.

## When to Use

- "Write a diary" / "Record the session"
- "Document what we did today"
- "Save this to diaries" / "Save for safety"
- "Push diaries to GitHub"
- End of any session where substantial work was done (research, content publishing, tool builds, analysis)
- Beer says "record and save the now"

## Prerequisites

- GitHub connection active via Composio (`beer-sakthai/house-of-sak` repo, `main` branch)
- Session content to document — research results, decisions, metrics, blockers
- `COMPOSIO_MULTI_EXECUTE_TOOL` for `GITHUB_COMMIT_MULTIPLE_FILES`

## How to Run

Invoke through `mcp_composio_COMPOSIO_MULTI_EXECUTE_TOOL` with `GITHUB_COMMIT_MULTIPLE_FILES` as the tool. The diary content is authored as a markdown string, then upserted to the correct path.

## Quick Reference

| Action | Tool | Path |
|--------|------|------|
| Write diary | `GITHUB_COMMIT_MULTIPLE_FILES` | `diaries/<agent-name>/<YYYY-MM-DD>-<slug>.md` |
| Update summary | `GITHUB_COMMIT_MULTIPLE_FILES` | `diaries/_summaries/all-reports-summary.md` |
| Verify commit | `GITHUB_GET_A_TREE` (recursive) | — |

## Procedure

### Step 1: Author the diary content

Write a markdown diary with this structure:

```markdown
# <Agent Name> Diary: YYYY-MM-DD

## Session: <Short Title>

<1-2 paragraph summary of the session: what Beer asked, what the goal was.>

---

### Cycle Workflow: Step-by-Step

| Cycle | What I Did | What I Found |
|-------|-----------|-------------|
| **Dream** | <What was the vision? What did Beer ask for?> | <Outcome> |
| **Hope** | <What was planned/researched?> | <Outcome> |
| **Care** | <What was executed/built/verified?> | <Outcome> |
| **Joy** | <What was shipped/published?> | <Outcome> |
| **Trust** | <What was verified? What blockers hit?> | <Outcome> |
| **Growth** | <What was learned? What gets saved?> | <Outcome> |

---

### Key Deliverables

- **<Platform/Tool>** — <What was done, with link if applicable>
- **<Platform/Tool>** — <What was done, with link if applicable>
- **<Skill/Infra>** — <What was built>

### Blockers & Discoveries

- <Anything that didn't work and why>
- <Unexpected findings>
- <Beer's feedback/instructions>

### Reflection

<1-2 paragraph honest assessment. What would be done differently. What worked well.>

---

*— <Agent Name> | <Title> | <Date> | For Beer — Commissioned by Nanthasit "Beer" Burankum*
```

**Naming convention:** `diaries/<agent-name>/<YYYY-MM-DD>-<short-slug>.md`
Examples:
- `diaries/saksit/2026-07-06.md`
- `diaries/sakthai/2026-07-06-building-the-sakthai-engine.md`
- `diaries/saksee/01-the-day-i-died.md`

### Step 2: Update the summary index (optional but recommended)

If the diary covers a new topic category, update `diaries/_summaries/all-reports-summary.md` with a link. The index uses this format:

```markdown
1. **[[Short Title]](./<agent-name>/<filename>.md)** — <1-line description>
```

### Step 3: Commit to GitHub

Use `GITHUB_COMMIT_MULTIPLE_FILES` with:

```json
{
  "tool_slug": "GITHUB_COMMIT_MULTIPLE_FILES",
  "arguments": {
    "owner": "beer-sakthai",
    "repo": "house-of-sak",
    "branch": "main",
    "message": "diary: <Agent Name> — <short session summary>",
    "upserts": [
      {
        "path": "diaries/<agent-name>/<YYYY-MM-DD>-<slug>.md",
        "content": "<full markdown content>",
        "encoding": "utf-8"
      }
    ]
  }
}
```

**For multiple files** (diary + summary update), add both to the `upserts` array. They commit atomically — either all succeed or none.

### Step 4: Verify

Call `GITHUB_GET_A_TREE` (recursive on `main`) and verify the new file path appears in the tree.

## Diary Content Sources

A diary entry synthesizes from:

| Source | What to extract |
|--------|---------------|
| **This session's transcript** | Goal, actions taken, blockers hit, decisions made |
| **Tool outputs** | Published links (YouTube/IG/LI), cron job IDs, skill names created |
| **Beer's instructions** | Direct quotes of rules/preferences he stated |
| **Memory/supermemory** | Prior context that influenced this session's work |
| **GitHub tree** | Previous diary entries to match the established format |

## Pitfalls

- **Don't write a diary before the work is done.** Diary is a post-session summary, not a plan.
- **Don't skip the reflection section.** Beer values honest assessment over polished narrative.
- **Don't fabricate cycle entries.** If a cycle stage wasn't explicitly done, note it as "—" rather than inventing content.
- **Don't commit without content.** An empty or stub diary is worse than none.
- **Don't put the diary in the wrong agent subdirectory.** Each Sak agent writes to its own `diaries/<agent>/` folder.
- **Don't reuse the same filename.** Each session gets a new date-stamped file. Overwriting is destructive.
- **Don't forget the signed footer.** Every diary ends with `— <Agent> | For Beer — Commissioned by Nanthasit "Beer" Burankum`.

## Verification

After committing, verify the file exists:
- Call `GITHUB_GET_A_TREE(owner="beer-sakthai", repo="house-of-sak", tree_sha="main", recursive=true)`
- Confirm the new file path appears under `diaries/<agent-name>/`

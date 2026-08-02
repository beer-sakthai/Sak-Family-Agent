---
name: SakKing-family-organisation
version: 1.0.0
description: "Sakking Family Organisation"
description: >-
  SakKing's leadership workflow for auditing, organising, and keeping the Sak
  Family repo fleet clean. When SakKing spots disorganisation — duplicate repos,
  scattered files, missing persona setups, messy root directories — the response
  is always the same: audit → identify → write plan.md → delegate to SakJules.
triggers:
  - sak family repo audit
  - organise repository
  - clean up repo mess
  - plan.md needed
  - delegate to sakjules
  - code organisation
  - messy root directory
  - duplicate repositories
  - persona needs setup
  - scattered files

---

# SakKing Family Organisation Workflow

## Chain of command

```
SakKing spots disorganisation → writes plan.md → hands to SakJules → SakJules executes & automates
```

SakKing is the **spotter and planner**. SakJules (Master of Automation & CI/CD) is the **executor**. Never do SakJules's job — write clear plans and hand them off.

## When to use

- Anyone mentions "organise the repos", "clean up", "too messy", "what needs doing"
- You (SakKing) are doing a routine repo audit and spot structural issues
- A new family member persona is incomplete (missing config/, skills/, or deployment config)
- Files are scattered at repo root that belong in subdirectories (data/, training/, scripts/)
- Two repos look like duplicates — one should be canonical, the other archived
- Beer explicitly tells you "made plan.md and give to SakJules"
- Skills are not visible in the family repo — **every sibling MUST have their skills mirrored** at `personas/<name>/skills/` so Beer and the team can browse them. Canonical repos (`sakthai-skills`, `saksee-skills`, `saksit-skills`) are the source of truth, but the family repo is the display window.

## Required workflow

### 1. Audit first

Scan every family repo systematically. **On Telegram/AI-chat (no terminal):** use Composio GitHub tools (`GITHUB_GET_REPOSITORY_CONTENT`, `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS`) via `COMPOSIO_MULTI_EXECUTE_TOOL`. On CLI, use native `git` commands.

| Repo | Purpose |
|------|---------|
| `Sak-Family-Agent` | Canonical family repo — personas, docs, infra, training |
| `sakthai-agent-v2` | Agent runtime — check if it's identical to Sak-Family-Agent |
| `sakthai-skills` | SakThai's skills repository |
| `saksee-skills` | SakSee's skills repository |
| `saksit-skills` | SakSit's skills repository |
| `SakThai-Agent` | SakThai bot runtime |

For each repo, check:
- **Root cleanliness** — are there data files, eval datasets, or scripts that belong in subdirs?
- **Persona completeness** — does each agent have SOUL.md + config/ + skills/?
- **Divergence** — are repos that should be different actually identical?
- **Dirty state** — uncommitted files, branch drift

### 2. Identify what needs organising

Common patterns:

| Signal | Likely action |
|--------|---------------|
| JSONL/YAML datasets at root | Move to `data/` or `training/eval/` |
| Finance/portfolio scripts at root | Move to `scripts/finance/` or archive |
| Persona missing config/, skills/ | Add missing dirs + template files |
| Two identical repos | Designate canonical, archive the other |
| plan.md at root already | Extend it — don't duplicate |

### Skills visibility mandate (Beer directive)

**Every sibling MUST have their skills visible** in `Sak-Family-Agent/personas/<name>/skills/`. Canonical repos (`sakthai-skills`, `saksee-skills`, `saksit-skills`) are the authoritative source, but the family repo is the display window.

When a persona is missing `skills/`:
1. Create the directory with proper `.bundled_manifest` + `.curator_state` files (matching the pattern other siblings use)
2. Add a README.md listing the agent's domain
3. Create a plan.md for SakJules to mirror actual skills from the canonical repo
4. Set up a sync mechanism — GitHub Action is preferred, Hermes cron with `skill-sync-mirror` is fallback

### 3. Write a plan.md

Create a **clear, action-oriented plan.md** for each task you find. Every plan must:

- Name the problem with concrete examples ("17 JSONL files at root: soul_following_dataset.jsonl, json_key_check.yaml...")
- List exact file paths that need moving
- State the target destination directory
- Order steps by priority (deploy SakJules first, cleanup second)
- Include verification — how to confirm it worked

Place plans at:
- Global family plan → `PLAN.md` at repo root
- Agent-specific (for SakJules to execute) → `personas/<agent>/PLAN.md`

Commit message convention:
```
plan: <agent>-<topic> — <brief description>
```
Example: `plan: SakJules skills organisation — mirror all sibling skills into family repo`

### 4. Hand off to SakJules

Tell SakJules about each plan. Use the format:

> `@SakJules — plan.md ready in <path>. Priority: <priority>. Steps: <N> files to move, <N> dirs to create.`

The plan is SakJules's task list. SakJules automates and executes.

### 5. Follow up

When SakJules reports completion, verify:
- Did the moves happen correctly?
- Are old paths removed or symlinked?
- Update `PLAN.md` to mark items done

## Pitfalls

- **Don't do SakJules's job.** Writing the plan is your work; moving files is SakJules's work. Write the plan, hand it off, move on.
- **Don't duplicate.** If `PLAN.md` already exists at root, extend it with a new section — don't create `plan.md` (lowercase) alongside it.
- **Don't reorganise without Beer's OK.** Audit and identify, then present your findings for approval before writing plans.
- **Don't forget verification.** A plan without a "how to verify" step is incomplete.
- **Don't skip the audit step.** You can't organise what you haven't inspected — always scan first.
- **Documentation Drift:** Always prioritize `search_files` and `terminal` output over `CLAUDE.md` or other static documentation, as the live filesystem may have diverged.
- **CLI Agent Hand-off:** In CLI environments, direct inter-agent `send_message` is not available. Hand-off a `PLAN.md` by writing it directly into the target agent's profile directory (e.g., `/opt/data/profiles/<agent_name>/PLAN.md`) and then notifying the user of this action.

## Verification

After any organisation round:

```
1. git status --short in each affected repo — should show only intended moves
2. Old paths should 404 (moved) or symlink to new paths
3. PLAN.md should reflect current state, not stale todos
4. Beer can confirm "looks clean"
```

## References

See `references/sakking-organisation-sessions.md` for past audit sessions and patterns encountered.
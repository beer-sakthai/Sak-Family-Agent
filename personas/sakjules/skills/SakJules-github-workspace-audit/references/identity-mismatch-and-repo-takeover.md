# Identity-File Mismatch and Deep Repo Takeover

## Context

This reference captures two related lessons from a 2026-07-06 session:
1. The system prompt can load the wrong sibling's SOUL.md as authoritative.
2. When the user says “it’s your project now, check what it needs,” the deep-inspection pattern applies, but the repo may turn out to be a messy, AI-edited project that needs cleanup before feature work.

## Identity-file mismatch check

When the user asks whether the agent's SOUL.md was updated today, or wants to edit the agent persona, verify that the SOUL.md path the system prompt treats as authoritative actually contains the current agent's persona.

In this workspace:
- `/opt/data/SOUL.md` is **SakKing's** persona (last modified 2026-07-04 15:44).
- The proper Saksee persona files are:
  - `/opt/data/personas/saksee/SOUL.md` ← canonical path referenced by the system prompt
  - `/opt/data/profiles/saksee/SOUL.md`
  - `/opt/data/Sak-Family-Agent/personas/saksee/SOUL.md` ← repo copy

### Safe update procedure

1. Read the file at the system-prompt path first. If it contains a different sibling's persona, do **not** overwrite it.
2. Read the canonical agent-specific path to see the current version.
3. Apply edits to the canonical path and to any other known copies.
4. Report which files were updated and which were deliberately left untouched.

## Deep repo takeover — Food-Penguin-Limited example

User said: “Food-Penguin-Limited” → “It your project now check and what is need.”

This is a takeover audit. The repo was private, had no local checkout, and contained a lot of AI-edit residue.

### Verified metadata

| field | value |
|---|---|
| owner | `beer-sakthai` |
| repo | `Food-Penguin-Limited` |
| visibility | private |
| default branch | `main` |
| last push (UTC) | 2026-07-02 14:04:32 |
| size | 47 KB |
| open issues / PRs | 0 / 0 |

### File inventory findings

| category | items | assessment |
|---|---|---|
| **Corrupt artifact** | `'))` (0-byte file at root) | Delete immediately |
| **Patch scripts** | `add_finance_api.cjs`, `apply_animations_v4.cjs`, `fix_ai.cjs`, `modify_*.cjs`, `repair.cjs`, `replace_logic.cjs`, `update_*.cjs` | Review; likely remove or move to `scripts/` |
| **Scratch file** | `scratch-selltab-original.tsx` (105 KB) | Confirm excluded in `tsconfig.json`; delete if unused |
| **Duplicate meta-docs** | `AGENTS.md`, `BRIEFING.md`, `GEMINI.md`, `handoff.md`, `ORIGINAL_REQUEST.md`, `SECURITY_AUDIT_REPORT.md`, `MENU_ENGINEERING.md`, `security_spec.md` at root + `.agents/` subtree | Keep canonical `.agents/` copies; remove root duplicates if not human-facing |
| **Config mismatch** | `package.json` name is `react-example` | Rename to match repo/project |
| **Test gap** | No test framework or CI | Note as gap; add only if user asks |

### Tools used

1. `GITHUB_GET_A_REPOSITORY` for metadata.
2. `GITHUB_GET_REPOSITORY_CONTENT` for root, `src/components`, `src/design-system`, and other directories.
3. `GITHUB_GET_RAW_REPOSITORY_CONTENT` for `package.json`, `vite.config.ts`, `.gitignore`, `server.ts`, and `src/App.tsx`.
4. `GITHUB_LIST_BRANCHES` and `GITHUB_LIST_COMMITS` for branch/commit history.
5. `COMPOSIO_REMOTE_WORKBENCH` to parse large directory listings and fetch S3 raw-content URLs.

### Key pitfall

`GITHUB_GET_REPOSITORY_CONTENT` directory listings can include phantom entries. The initial root listing showed `vitest.config.ts` and `tests/`, but direct fetches returned 404. Always verify a listed path with a direct fetch before reporting it as fact.

### Recommended report shape

For a takeover audit, present:
1. One-sentence project identity.
2. Verified state table (visibility, branch, last push, issues/PRs).
3. Ranked findings table (severity, item, action).
4. Next-step options for the user.

## Removing a local-only repo

When the user says a directory is not actually a real project (e.g., “we don't have projects/sak-agents rm from anywhere”), check for a remote before deleting:

```bash
git -C /opt/data/projects/sak-agents remote -v
```

If there is no remote, the directory is just local noise. Remove it:

```bash
rm -rf /opt/data/projects/sak-agents
```

Then update the audit document (`fact.md`) to record the removal and the reason.

## Audit deliverable

Create a single `fact.md` at the workspace root with:
- Verified GitHub repos
- Local checkout status
- Stale memory claims
- Uncommitted work list
- Per-project findings
- Pending decisions and blockers

This becomes the single source of truth for the workspace state at that moment.

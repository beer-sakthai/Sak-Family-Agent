# Deep Repository Inspection Pattern

Use after the workspace-level reconciliation is done and the user points at a specific repo and says something like “it’s your project now — check what it needs.”

## Goal

Turn an unfamiliar GitHub repository into a concise health report: what it is, how it is built, what is clean, and what needs attention.

## When to use

- The repo exists and is accessible, but there is no local checkout or the local copy is stale.
- The user wants a takeover assessment rather than a workspace reconciliation.
- You need to identify cleanup items (corrupt files, stale scripts, missing tests, outdated deps) before proposing work.

## Steps

1. **Repo metadata.** Call `GITHUB_GET_A_REPOSITORY` to capture visibility, default branch, last push, size, license, and open issues/PRs.
2. **Root listing.** Call `GITHUB_GET_REPOSITORY_CONTENT` with `path=""` to see top-level files and directories.
3. **Key directories.** List `src/`, `tests/`, `.github/`, and any other top-level directories relevant to the stack.
4. **Config files.** Fetch raw content of `package.json`, `tsconfig.json`, `vite.config.ts` / `webpack.config.js`, `.gitignore`, and the main entry files (`src/App.tsx`, `src/main.tsx`, `server.ts`, etc.).
5. **Branches and commits.** Call `GITHUB_LIST_BRANCHES` and `GITHUB_LIST_COMMITS` to understand branch discipline and recent activity.
6. **Synthesize findings.** Produce a short report with:
   - What the project is (stack, purpose).
   - Verified current state (last commit, branch count, test status).
   - A ranked list of cleanup/action items.
   - Explicit next-step options for the user.

## Concrete signals to flag

| Signal | Likely meaning |
|--------|----------------|
| 0-byte file with a nonsensical name (e.g. `'))`) | Corrupt artifact from an AI editor or patch tool. Delete it. |
| Many root-level `.cjs` scripts (`modify_*.cjs`, `update_*.cjs`, `repair.cjs`) | One-off patch scripts from prior edits. Review and usually remove or consolidate into a `scripts/` directory. |
| Large `scratch-*.tsx` file | Legacy/scratch component excluded from the build. Confirm in `tsconfig.json`; delete if unused. |
| Duplicated meta-docs at root and under `.agents/` | Agent handoff files copied to multiple locations. Keep the canonical set under `.agents/` and remove root duplicates if they are not human-facing. |
| `package.json` name does not match repo name | Low-priority cleanup; rename to match the repo/project. |
| No test framework configured | Note it as a gap, but do not add one unless the user asks. |

## Handling Composio raw-content responses

`GITHUB_GET_RAW_REPOSITORY_CONTENT` often returns an S3 pre-signed download URL instead of inline text:

```json
{
  "content": {
    "mimetype": "text/plain",
    "name": "package.json",
    "s3url": "https://temp.....r2.cloudflarestorage.com/..."
  }
}
```

Fetch `s3url` separately with an HTTP GET. Do not log the S3 URL in replies — it contains time-limited credentials.

## Handling phantom directory entries

A directory listing may show files (e.g. `vitest.config.ts`, `tests/`) that return 404 when fetched directly. Always verify a critical path with a direct `GITHUB_GET_REPOSITORY_CONTENT` or `GITHUB_GET_RAW_REPOSITORY_CONTENT` call before reporting it as a fact. If it 404s, say “listed but not present” rather than treating it as existing.

## Example output shape

For `beer-sakthai/Food-Penguin-Limited` (2026-07-06):

- **Project:** React 19 + Vite + TypeScript corporate ops dashboard for a food/restaurant concept.
- **State:** Private repo, single `main` branch, last pushed 2026-07-02, no open issues/PRs.
- **Findings:**
  1. Corrupt 0-byte file `'))` at root.
  2. ~12 stale `.cjs` patch scripts at root.
  3. 105 KB `scratch-selltab-original.tsx` scratch file.
  4. Duplicated agent docs at root and `.agents/`.
  5. `package.json` name is `react-example` instead of `food-penguin-limited`.
  6. No test framework or CI configured.
- **Next options:** clone and run lint/build; delete corrupt/scratch files; consolidate meta-docs; rename package.

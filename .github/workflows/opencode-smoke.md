---
name: OpenCode Smoke
emoji: "🧪"
description: |
  Weekly (and on demand) smoke test that proves the vendored OpenCode engine still runs
  in this repository, driven by a Gemini model through the AWF API proxy. It exercises
  the engine's bash, file-read, and GitHub MCP surfaces and reports the result as an
  issue. It has no write access to the repository and cannot open pull requests.

on:
  workflow_dispatch:
  schedule: weekly on monday

permissions:
  contents: read
  issues: read
  pull-requests: read

model: copilot/gemini-3.1-flash
engine:
  id: opencode
strict: true

imports:
  - shared/opencode.md

network:
  allowed:
    - defaults
    - github

safe-outputs:
  create-issue:
    title-prefix: "[opencode-smoke] "
    labels: [automation, testing]
    max: 1
    close-older-issues: true

timeout-minutes: 15

sandbox:
  agent:
    sudo: false
---

# OpenCode Engine Smoke Test

You are running on the **OpenCode** CLI engine — a vendored, upstream-unsupported gh-aw
engine definition (`.github/workflows/shared/opencode.md`) — with a **Gemini** model routed
through the AWF API proxy. The point of this run is to prove that combination still works
end to end. Keep the run short; do not attempt repository changes.

## Checks

Run each check and record a ✅ or ❌ for it. If a check fails, capture the exact error text
rather than paraphrasing it.

1. **Engine identity** — report the value of the `OPENCODE_MODEL` environment variable, so
   the compiled provider prefix (`awf-proxy/…`) and the resolved Gemini model are both
   visible in the report.
2. **Bash** — run `python3 --version` and `uv --version`. Both are expected to resolve; a
   missing `uv` is a finding, not a failure of this workflow.
3. **File read** — read `pyproject.toml` from the repository root and report the value of
   `project.name` and `project.requires-python`.
4. **Repository shape** — read `CLAUDE.md` and confirm the installed package path it names
   (`personas/sakthai/sakthai/`) actually exists on disk. Report a mismatch as a ❌.
5. **GitHub MCP** — use the GitHub MCP `repos` toolset to fetch the two most recent commits
   on the default branch of `${{ github.repository }}`. Report their short SHAs and subject
   lines only.

## Output

Always create exactly one issue summarizing the run:

- **Title**: `OpenCode smoke — run ${{ github.run_id }}`
- **Body** must contain, in this order:
  - A one-line overall verdict: **PASS** if every check is ✅, otherwise **FAIL**.
  - A table of the five checks with their ✅/❌ and a one-line result each.
  - The resolved model string from check 1.
  - The run URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}

Do not open a pull request, do not modify tracked files, and do not comment on unrelated
issues. If the engine itself fails to start, the workflow run's own logs are the record —
there is nothing for you to do in that case.

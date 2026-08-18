---
name: Shared Package Drift
emoji: "🪞"
description: |
  Weekly audit of the gap between the installed package (personas/sakthai/sakthai/) and
  the shared copy that SakJules and SakTan execute (personas/shared/sakthai/). The
  divergence is deliberately inventoried in tests/test_shared_package_divergence.py rather
  than fixed; this workflow reports when that inventory has gone stale or the gap has
  grown, so the debt shrinks instead of calcifying.

on:
  schedule: weekly on tuesday
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: gemini
strict: true

network: defaults

safe-outputs:
  create-issue:
    title-prefix: "[shared-drift] "
    labels: [maintenance, automation]
    max: 1
    close-older-issues: true

tools:
  cache-memory: true
  bash:
    - "diff"
    - "find"
    - "git"
    - "ls"
    - "wc"

timeout-minutes: 20
---

# Shared Package Drift Audit

`personas/sakthai/sakthai/` is the package this repository installs, type-checks, and
tests. `personas/shared/sakthai/` is a second copy that `personas/sakjules/` and
`personas/saktan/` reach through a symlink — it is what those two personas actually
execute, and no test imports it, so its behaviour is unverified rather than merely
under-covered.

That gap is intentional and tracked. `tests/test_shared_package_divergence.py` holds two
registers: `KNOWN_DIVERGENCES` (files that differ, each with a stated reason) and
`CANONICAL_ONLY` (modules that exist only in the installed copy). The test fails when an
undeclared file diverges **and** when a declared file has since been synced — that second
direction is what stops the register from becoming a permanent excuse.

Your job is to report on the state of that register. You are auditing, not fixing.

## What to do

1. Read `tests/test_shared_package_divergence.py` and extract the current contents of
   `KNOWN_DIVERGENCES` and `CANONICAL_ONLY`, including the stated reason for each entry.
2. Compare the two trees directly:
   `diff -rq personas/sakthai/sakthai personas/shared/sakthai`
3. Classify every difference the diff reports:
   - **Declared and still diverged** — in `KNOWN_DIVERGENCES`, still differing. Expected.
     For each, report how large the gap is (`diff | wc -l`) and whether it grew since the
     reason was written, as far as you can tell from `git log` on both paths.
   - **Declared but now identical** — in a register but no longer differing. This is a
     stale entry; the register should shed it.
   - **Undeclared** — differing (or canonical-only) with no register entry. This should
     already be failing CI; say so plainly and name the file.
4. Note separately any file present in `personas/shared/sakthai/` but absent from
   `personas/sakthai/sakthai/` — the register does not model that direction, and it would
   mean the shared copy has grown something of its own.

## Reporting

Open an issue **only if** there is something actionable: a stale register entry, an
undeclared divergence, a shared-only file, or a declared divergence whose gap has
measurably grown. If the register exactly matches reality and nothing has moved, say so in
the run log and create no issue — a weekly "nothing changed" issue is noise.

When you do open one:

- Title: `Shared package divergence — <n> item(s) need attention`
- Lead with a one-line verdict, then a table of the affected files: path, classification
  from step 3, and the concrete next step (remove the register entry / sync the file /
  declare it with a reason).
- Do not propose a reconciliation plan for the whole tree. Reconciling the two copies is a
  known, tracked, deliberately-deferred piece of work; this issue exists to keep its
  inventory honest, not to reopen the decision.
- Include the run URL:
  ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}

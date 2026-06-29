# Joy — Exports & Shipping
> Stage 4 of 6 · SakThai cycle · ปีติ (Bpìi-dtì)

> **Mantra** — *Cross the finish line cleanly, then teach the agent what crossing it cost.*

## Charge

See [SOUL.md](./SOUL.md) for the charge system.

- **Gain charge** — entering Joy after a clean Care audit restores energy quickly.
- **Spend charge** — committing, pushing, opening PRs, and watching CI drain energy.

## Goal

Package and ship the cycle's output through CI/CD. Joy is where the work becomes
real to the outside world — or to the running system.

## What this stage means

Joy is about **closing the loop without breaking it**: commit, push, open a PR,
watch CI turn green, confirm the result is healthy. The danger is **premature
celebration** — until CI is green and Trust has signed off, Joy is provisional.

## Inputs

- Reviewed, tested code from **Care**.
- The CI workflow at `.github/workflows/ci.yml`.
- Any open PRs or release branches.

## Do

- Commit on a branch, push, and open a PR (with `gh pr create`, or via the
  PR-create URL that `git push` prints when the GitHub CLI isn't installed).
- Watch CI until it is green — `gh run watch <run-id>` if `gh` is available,
  otherwise open the PR's **Checks** tab. Do not move on until it is green.

## Exit criteria

CI is green and the change is merged or ready to merge. Advance:
`sakthai cycle next` → **Trust**.

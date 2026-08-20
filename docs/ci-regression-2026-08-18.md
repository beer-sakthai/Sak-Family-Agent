# Security-CI regression on `main` — 2026-08-18

Commit [`1c7df23`] landed on `main` at 08:45 UTC under the message
**"Fix hardcoded Hugging Face token path in workbench script"**, carrying
**95 files changed, 194 insertions, 6,890 deletions**. Almost none of it is
about a token path.

This is the **third** occurrence of the pattern already documented in
`CLAUDE.md` and `docs/code-scanning-sweep-2026-08-18.md`: a bot commit whose
message describes a small fix, silently reverting merged security work. The
first two were caught by reading the code-scanning dashboard. This one removed
`tests/test_workflow_hygiene.py` — the guard added specifically to catch it —
which is why CI stayed green.

## What it removed, and what that turned off

| Path | Effect of the deletion |
|---|---|
| `.github/workflows/codeql.yml` | The **live CodeQL producer**. `CLAUDE.md` says in terms: "Do not delete it." All three `Analyze` jobs (`actions`, `javascript-typescript`, `python`) stopped. |
| `.github/codeql/codeql-config.yml` | Not deleted, but **reverted to stale text** asserting default setup is on and "there is deliberately no `codeql.yml`" — the opposite of the repository's actual state, and self-justifying for the deletion above. |
| `.github/workflows/eslint.yml` | Dashboard ESLint → SARIF publishing. |
| `.github/workflows/auto-merge.yml` | Label-gated native auto-merge. |
| `.github/workflows/publish-npm.yml` | Inert release template. |
| `.bandit` | **Reverted to the broken pasted Actions YAML** (`uses: jpetrucciani/bandit-check@main`) — unparseable, so a bare `bandit -r .` silently runs with no configuration. Exactly the defect fixed on 2026-08-18. |
| `.claude-plugins/sak-security/**` | The `security-reviewer` agent plugin. |
| `tests/test_workflow_hygiene.py` | **The guard.** 129 cases: every workflow loadable, top-level `permissions:`, SHA-pinned `uses:`, the `self-healing-ci.yml` fork guard, `codeql.yml`'s `config-file:`, `.bandit` parseable and anchored. |
| `CLAUDE.md` | 48 lines — precisely the rows documenting the four deleted workflows and the hygiene test. |

Not affected: `bandit.yml`, and `self-healing-ci.yml` — its fork guard
(`head_repository.full_name == github.repository`, the critical Scorecard
`DangerousWorkflowID` fix) is still in place. Verified, not assumed.

## The guard was load-bearing — measured

Restoring `tests/test_workflow_hygiene.py` and then re-applying each deletion
individually confirms it would have blocked this:

| Re-applied deletion | Result |
|---|---|
| `.bandit` back to the pasted YAML | `test_bandit_ini_is_parseable_configuration`, `test_bandit_ini_exclusions_are_anchored` **fail** |
| `.github/workflows/codeql.yml` removed | `test_codeql_workflow_uses_the_scope_config` **fails** |
| Nothing (restored state) | 129 pass |

Deleting the test first is what made the rest of the commit invisible to CI.

## What this restore does, and deliberately does not

Restored: the four workflows, `.claude-plugins/sak-security/**`,
`tests/test_workflow_hygiene.py`, `.bandit`, `.github/codeql/codeql-config.yml`
and the `CLAUDE.md` section. `CLAUDE.md` had no other commits after `1c7df23`,
so restoring its pre-deletion content loses nothing.

**Not restored — 41 dashboard product files** (`apps/sak_agent_dashboard/src/**`
components, API routes, `lib/safety/ast_sandbox.ts`, and their vitest suites).
Whether their removal was intentional cannot be determined from the commit, and
resurrecting product code on a guess is worse than leaving it. `ast_sandbox.ts`
is worth a specific look — PR #857 hardened Python sandbox AST validation, and
this commit may have undone part of that.

**Not restored — two files that were deleted but are not regressions:**

- `tests/test_workbench_api_token.py` — fails against **both** the pre-deletion
  and current `scripts/workbench/workbench-1.5b-api.py`, so restoring it adds a
  red test rather than a working guard. Its security property still holds: the
  current script reads `HF_TOKEN`/`HUGGING_FACE_HUB_TOKEN` from the environment
  with no hardcoded literal, and the test's `login(token=…)` assertion passes —
  only its assertion about `InferenceClient` construction fails.
- `tests/eval/eval_config.yaml`, `tests/eval/datasets/basic-dataset.json` —
  unreferenced by any test, workflow, Makefile target or plugin config.

## Residue worth a separate look

`1c7df23` also stripped 182 lines from
`scripts/workbench/workbench-1.5b-api.py`, leaving a stub that imports
`InferenceClient`/`HfApi` and never uses them. The token handling it claimed to
fix is intact and correct; the rest of the script's body is gone. The
pre-deletion version was itself garbled (the `_get_hf_token()` helper spliced
into the middle of the summary loop, with a duplicate import at the end), so
this needs rewriting rather than reverting.

## Recurrence: the plugin was deleted again

`04bbce0` — **"perf: optimize portfolio CSV loading with ThreadPoolExecutor"**,
26 files, 32 insertions / **885 deletions** — deleted
`.claude-plugins/sak-security/**` a second time, along with
`.github/workflows/publish-npm.yml` and `tests/test_workbench_api_token.py`.
Same signature as the rest: a message describing something unrelated to most
of the diff.

Nothing failed, for the same structural reason as before: **no test imports the
plugin, no workflow runs it, and nothing else in the repository references it**,
so its deletion is invisible to every check.

**Restored** (the plugin only) and pinned by
`tests/test_persona_guardrails_parity.py::TestSecurityToolingIsPresent`, which
asserts the three files exist, are non-empty, and that the manifest is valid
JSON naming `sak-security`. Contents are deliberately not pinned, so the agent
can still be edited freely. Verified by replaying the deletion: all three
subtests plus the manifest check fail, and pass once restored.

**`.github/security-insights.yml` was deliberately NOT restored.** It is not
this repository's file — the copy in git history is the OpenSSF Scorecard
project's own, naming that project and an unrelated administrator at Bloomberg.
Restoring it would republish false provenance claims. Deleting it was correct;
if the repo wants a security-insights file, it needs one written from its own
facts (this is the same conclusion the 2026-08-18 code-scanning sweep reached).

`tests/test_workbench_api_token.py` and `publish-npm.yml` were also left out,
for the reasons already given above.

## Prevention

The guard is back, so a fourth recurrence fails CI rather than landing quietly.
The deeper issue is unchanged and not fixable in this repository: commits are
landing on `main` whose diffs bear no relation to their messages. Reviewing the
**diffstat** rather than the subject line is the only thing that catches the
first one; `tests/test_workflow_hygiene.py` catches every one after it that
touches CI.

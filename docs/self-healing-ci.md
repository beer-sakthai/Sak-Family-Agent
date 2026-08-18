# Self-healing CI

When the `CI` workflow fails on `main`, the **Self-Healing CI** workflow reads
the failed job's log, works out what broke, and — only when the fix is small,
safe, and verified locally — opens a pull request with it.

It never writes to `main`. Its output is a branch under `selfheal/` and a PR for
a human to review, subject to the same non-author approval rule as any other PR
(`docs/CONTRIBUTING.md`).

---

## The flow

```
CI workflow fails on main
        │
        ▼
self-healing-ci.yml downloads the failed job log  (gh run view --log-failed)
        │
        ▼
Log ingestor        selfheal/ingest.py      → FailureSignal (tool, error, frames)
        │
        ▼
Repo inspector      selfheal/inspector.py   → FileContext (verbatim source windows)
        │
        ▼
Diagnosis agent     selfheal/diagnose.py    → Diagnosis (root cause, confidence, edits)
        │                                     …then the safety gate (selfheal/safety.py)
        ├── violations, or confidence below the bar ──► abort, report, change nothing
        ▼
Code editor         selfheal/patch.py       → PatchTransaction (all-or-nothing, undoable)
        │
        ▼
Test runner         selfheal/verify.py      → the failing test, then the whole suite
        ├── either run red ──► roll back to byte-identical, report, change nothing
        ▼
Publish             selfheal/publish.py     → selfheal/… branch, push, `gh pr create`
        │
        ▼
Walkthrough         selfheal/walkthrough.py → structured PR body + model narrative
```

`selfheal/pipeline.py` is that flow, in one function, with every stage
injectable. `sakthai heal run` is the CLI over it.

---

## Where the safety actually comes from

The model is the least trusted part of this system, and the design assumes it
can be wrong or actively steered — a CI log is text anyone who can open a PR can
influence. Four properties carry the weight:

**The model returns data, not actions.** A diagnosis is JSON: a root cause, a
confidence, and a list of exact-string replacements. There is no shell command,
no file write, and no free-form patch anywhere in the reply, so a hostile
response has nothing to execute.

**The safety gate is deterministic and has the final word.** `selfheal/safety.py`
makes no model call. It refuses edits that leave the repository, land on a
protected path (`.github/`, `pyproject.toml`, `uv.lock`, the security subsystem,
the `selfheal` package itself), create a new file, replace text that appears
zero or several times, exceed the size limits, or introduce a code-execution
primitive, a checker suppression (`# noqa`, `# type: ignore`, `# nosec`), a
skipped test, or a credential. **A violation is a hard stop — no confidence
score overrides one**, because the model's confidence is not evidence about the
model.

**Nothing is published that was not verified.** The patch is applied, the failing
test is re-run, and then the whole suite (`-m "not integration"`, the same
selection CI uses) is re-run. Both must pass. Fixing the reported failure while
breaking something else is a failure, and it rolls back.

**Rollback restores bytes, not intentions.** `apply_edits` captures each file's
original content before writing and either applies every edit or none. A red
verification run leaves the tree byte-identical to how it started.

The fix branch is created *after* verification passes, so a failed run has
nothing to clean up beyond the files it wrote. The one case where a branch can
exist and be unwanted — a commit that succeeded followed by a failed push — is
cleaned up explicitly.

---

## Using it by hand

```bash
# What does this log actually say? No model call, no writes.
sakthai heal inspect --log ci-failure.log
sakthai heal inspect --log - --json < ci-failure.log

# Diagnose only: propose nothing, write nothing.
sakthai heal run --log ci-failure.log --dry-run

# Apply and verify, but leave the fix in the working tree.
sakthai heal run --log ci-failure.log --no-publish

# The full flow.
sakthai heal run --log ci-failure.log --run-id 12345 --report heal-report.md
```

Useful options: `--min-confidence` (default `0.7`), `--model` / `--provider` for
the diagnosis, `--walkthrough-model` for the narrative, `--branch-prefix`,
`--base`, `--no-pr`, `--json`.

**The exit code reports whether the pipeline ran, not whether a fix was found.**
An honest "this failure is not safely fixable" is a successful run. Read the
terminal status from `--json` or the report; only an internal error (unreadable
log, bad repository root, unbuildable provider client) exits non-zero.

### Terminal statuses

| Status | Meaning |
|---|---|
| `no_failure` | The log carried nothing the ingestor recognises. |
| `no_diagnosis` | Diagnosed, but no fix proposed — often correct (an environmental flake). |
| `dry_run` | A safe fix was found; `--dry-run` stopped before applying it. |
| `aborted_unsafe` | The safety gate rejected the patch, or it could not be applied. |
| `aborted_low_confidence` | Safe, but below the confidence bar. |
| `rolled_back` | Applied, verification failed, tree restored. |
| `fixed` | Applied and verified; publishing was disabled. |
| `published` | Pushed to a `selfheal/` branch, PR opened. |

---

## The workflow

`.github/workflows/self-healing-ci.yml` triggers on `workflow_run` completion of
`CI` on `main`, and can be dispatched by hand (`run_id`, `dry_run`).

Two guards keep it from feeding on itself: it only acts on `conclusion == 'failure'`,
and it skips any run whose head branch already starts with `selfheal/`.

Credentials: `ANTHROPIC_API_KEY` is required for diagnosis — without it the job
records that in the step summary and stops. `GEMINI_API_KEY` is optional and only
narrates the walkthrough; the PR body is complete without it.

**A PR opened with `GITHUB_TOKEN` does not itself trigger workflows.** CI on the
fix branch has to be started by a maintainer (close/reopen the PR, or push an
empty commit). The agent verifies locally before pushing, which is why this is a
review inconvenience rather than a correctness gap.

Every run uploads `ci-failure.log`, `heal-report.md` and `heal-outcome.json` as
an artefact and writes the outcome to the job summary, so a run that changed
nothing still explains itself.

---

## Relationship to `ci-doctor`

`.github/workflows/ci-doctor.md` (a `gh-aw` agentic workflow) also watches CI
failures, but it **investigates and files an issue** — it never edits code. The
two are complementary: `ci-doctor` explains failures across the whole quality and
security surface; self-healing CI attempts a verified fix for the narrow class it
can prove it fixed. Neither one merges anything.

---

## Extending it

Adding a checker to the ingestor is the most likely change. Add a pattern and a
branch in `selfheal/ingest.py`, return a `FailureSignal` with the frames that
locate the problem, and add a fixture-shaped test in
`tests/test_selfheal_ingest.py` — with the timestamps and ANSI codes a real
Actions log carries, not hand-cleaned text.

Tightening the safety gate is the other. Add the rule to `selfheal/safety.py` and
a test that pins **the rule's own reason string**, not just that something was
rejected: several rules overlap, and a test asserting only "rejected" can pass
because a different rule fired.

# Code-scanning sweep — 2026-08-20

A read of [the code-scanning dashboard](https://github.com/beer-sakthai/Sak-Family-Agent/security/code-scanning)
and the changes it prompted. `main` at `c82ef0f`.

**Result: 115 open alerts, and the movement since the last sweep is entirely in
one tool.** [2026-08-18](code-scanning-sweep-2026-08-18.md) left the dashboard
at 100.

## The measurement

Read from the dashboard itself, by dispatching **Code scanning cleanup** with no
inputs — run
[32372119909](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/32372119909).
Nothing below is inferred from a workflow's source; the counts are the API's
own. This session's token has no `security_events` scope, so the workflow is the
only read available — which is what it exists for.

```
Open code-scanning alerts on beer-sakthai/Sak-Family-Agent: 115

tool         open alerts  analyses  latest analysis
-----------  -----------  --------  --------------------
Bandit       50           1407      2026-08-20T12:48:09Z
BinSkim      0            412       2026-07-06T05:01:03Z
CodeQL       0            10519     2026-08-20T12:48:56Z
ESLint       0            3292      2026-08-20T12:48:19Z
Scorecard    42           1670      2026-08-20T12:48:30Z
github-repo  23           1         2026-08-17T09:47:23Z
mobsfscan    0            14        2026-08-12T04:14:21Z
```

Against the previous sweep:

| Tool | 2026-08-18 | Now | |
|---|---:|---:|---|
| Bandit | 69 | **50** | the tree moved; `#997` nosec'd 13 `B311` |
| CodeQL | 2 | **0** | both dashboard-app ReDoS findings fixed by `#997` |
| ESLint | 1 | **0** | the `set-state-in-effect` finding fixed by `#997` |
| Scorecard | 5 | **42** | **the regression this sweep is about** |
| github-repo | 23 | 23 | held — see below, 21 of them are passes |
| **Total** | **100** | **115** | |

CodeQL and ESLint are at zero. That is worth stating plainly because it is the
first time both have been, and it means the scope config from round two is
holding: the 788 → 2 → 0 path was real, not an artefact of a scan that stopped
running (10,519 analyses, latest today).

## Scorecard 5 → 42, and why the number is misleading in both directions

The jump is not 37 new weaknesses. It is one workflow deleted-then-restored, one
class of finding that was previously suppressed by a *narrower* scan, and a
large tail of `.lock.yml` compiler output. Broken down:

| Count | Rule | Sev | What it is |
|---:|---|---|---|
| 1 | `DangerousWorkflowID` | critical | `self-healing-ci.yml` — **displayed, not live** (below) |
| 21 | `TokenPermissionsID` | high | 3 first-party (**fixed here**), 10 in `.lock.yml`, 8 accepted |
| 17 | `PinnedDependenciesID` | medium | 2 first-party (**fixed here**), 15 in `.lock.yml` |
| 3 | `BranchProtectionID` / `CodeReviewID` / `CIIBestPracticesID` | high/low | repository settings and process; no diff closes them |

### The three `TokenPermissionsID` that were first-party — and a re-fix

`auto-update-prs.yml:10`, `continuous-security.yml:18` and
`auto-dependency-update.yml:10` each declared **top-level** `contents: write`.
Scorecard scores that 0: `permissions:` at the top level is the default every
job in the file inherits, so a job added later by someone who never read the
block gets a push-capable token for free.

**This had already been fixed once.** `PLAN.md`'s 2026-08-12 entry records these
exact three workflows being "demoted from top-level `contents: write` to
job-scoped write", marked done. Eight days later the dashboard reported all
three as top-level `contents: write` again. The fix had been reverted by commits
about other things, and — as with the `self-healing-ci.yml` fork guard in round
two — **nothing in CI noticed**.

So the fix here is the same fix, plus the guard that was missing the first time:

- `auto-update-prs.yml` and `continuous-security.yml`: top level is
  `contents: read`; the single job in each re-declares the writes it needs.
- `tests/test_workflow_hygiene.py::test_no_authored_workflow_grants_top_level_contents_write`
  now fails CI on any authored workflow that declares top-level `contents: write`
  or `write-all`.

Job-level `contents: write` is still present and still flagged — that is the
accepted risk the 2026-08-12 sweep recorded, unchanged, for workflows that
genuinely push. **This change does not reduce the raw alert count by three**; it
converts a file-wide default into a job-scoped grant, which is the tighter of
the two configurations Scorecard distinguishes. Counting it as a −3 would be
wrong and is not claimed.

### `auto-dependency-update.yml` — removed, for the second time

The third `TokenPermissionsID` needed no permissions work, because the workflow
should not exist. Its run history, read rather than its file:

```
22 runs, 22 failures. Latest 2026-08-17, run 32010798120:
  ##[error]Input 'token' not supplied. Unable to continue.
```

It wants `secrets.GH_PAT_FOR_ACTIONS`, which this repository does not have, and
it duplicates `.github/dependabot.yml` — five ecosystems, 22 directories, which
works. It was removed on 2026-08-18 for exactly these reasons, and `SECURITY.md`
already calls Dependabot "the **only** source of automated dependency bumps" and
names this file as removed.

It came back inside a commit titled `[StepSecurity] Apply security best
practices`, SHA-pinned and tidied and still broken, and ran weekly on `main`
failing every time while three documents said it was gone.

It is removed again, its two stale `README.md` rows with it, and
`test_the_failed_dependency_update_workflow_stays_removed` makes the third
resurrection loud. That test names its own escape hatch: configure the PAT, get
a run green, delete the test in the same commit.

`continuous-security.yml` came back in the same commit and is **left in place**,
because deleting a workflow twice on an agent's judgement is not the same as
fixing it. It is worth knowing what it is, though — its last "successful" run,
[32093238703](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/32093238703):

```
10 skipped  Run DevSecOps Skill
11 success  Explain why the scan was skipped
```

Green, nightly, and doing nothing, because there is no `ANTHROPIC_API_KEY`.
`security-audit.md` on the Gemini engine is what actually audits. Adding the
secret revives this one; until then its green tick is evidence of nothing.

### The two `PinnedDependenciesID` that were first-party

Both are `downloadThenRun not pinned by hash`, and they are not the same finding
wearing two hats — one is real and one is not.

**`infra/self-hosted-runner/bootstrap-toolchain.sh:59` — real, and the worse of
the two was not even the flagged line.** The script provisions a self-hosted CI
runner, so anything it executes runs with that runner's access to this
repository. It contained:

```bash
curl -fsSL https://astral.sh/uv/install.sh | sh                        # line 59, flagged
curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | sudo -E bash -   # line 65, not flagged
```

The second is remote code as root and Scorecard did not report it. Fixing only
the flagged line would have left the more dangerous one in place — worth noting,
because it is the argument for reading the file rather than the alert.

Both are fixed, by different mechanisms, because the two endpoints differ:

- **uv** is downloaded to a file and checked against a pinned SHA-256 before it
  is run. The digest is only stable because the URL carries the version —
  `https://astral.sh/uv/0.12.5/install.sh` is immutable, while the unversioned
  `install.sh` is rewritten on every uv release and could never be pinned.
- **NodeSource** is no longer executed at all. All its setup script does is
  register an apt key and repository, so the script does that directly, pinning
  the key fingerprint (`6F71F525…9B1BE0B4`) and letting apt verify every package
  signature itself. That is a stronger guarantee than hashing an installer.

Both verifications were tested in both directions before commit — the real
installer and the real key are accepted; a one-byte-modified installer and a
locally generated impostor key are both rejected with a diagnostic. A check that
has only ever been seen to pass has not been tested.

**`scripts/enable_dependabot.sh:87` — a false positive, restructured anyway.**
The line is `curl … | python3 -c '<literal script>'`. The executed code is the
`-c` string; the download is only ever data on stdin. Nothing remote runs, and
there is nothing to pin.

It was still worth changing, for a reason that is not the alert: a failed
request reached python as empty stdin and surfaced as a `JSONDecodeError`
traceback, which reads like a bug in the script rather than a network or token
problem. The response is now captured first and parsed from `argv`, and both
failure modes exit with a sentence. The alert closing is a side effect of a
change that pays for itself.

This is the line the 2026-08-12 sweep drew at "would need vendoring remote
installers" and deferred. Two of the three sites turned out to need neither
vendoring nor hashing — just not piping into a shell.

### `DangerousWorkflowID` #15541 — verified still displayed, not live

Unchanged and re-verified rather than inherited: the guard clause

```yaml
github.event.workflow_run.head_repository.full_name == github.repository
```

is present at `self-healing-ci.yml:66`, and
`test_self_healing_ci_refuses_untrusted_forks` still passes. Scorecard's check
is syntactic and does not evaluate the guarding `if:`, so the alert stays open
by design. Resolving the SHA in an earlier step to hide the expression would
close it without changing behaviour; that is gaming the check and was not done.

## Bandit — 50, and the local scan agrees exactly

Round three's parity invariant still holds: `bandit -c pyproject.toml -r .` run
locally reports the same count the dashboard does. By rule:

| Count | Rule | Disposition |
|---:|---|---|
| 23 | `B615` | unpinned HF `from_pretrained` / `load_dataset` revision, in `training/` and `scripts/` — **open backlog** |
| 11 | `B108` | hardcoded `/tmp` in `training/` and `scripts/hf/` — **open backlog** |
| 6 | `B110` | `try/except/pass` — **open backlog** |
| 4 | `B310` | `urllib.urlopen` audit — **open backlog** |
| 3 | `B112` | `try/except/continue` — **open backlog** |
| ~~3~~ | ~~`B105`~~ | **closed here** — all three false positives |

Zero HIGH severity, and nothing in `personas/sakthai/sakthai` or
`personas/shared/sakthai`; both scan clean.

The three `B105` "hardcoded password" findings were Bandit matching on a
*variable name*, not a value: two `TOKEN_PATH = "/opt/data/…/huggingface/token"`
constants (a filesystem path) and one `token = ""` initialiser immediately
followed by the parse that fills it. All three carry `# nosec B105` with the
reason, in the repository's existing style. 50 → 47 locally.

**The remaining 47 are not fixed and are not dismissed.** The largest group,
`B615`, is a genuine supply-chain finding — an unpinned `revision=` takes
whatever the Hub serves — but pinning 23 call sites across training code that
cannot be exercised from here is a change that should be made by someone who can
run it. Named, not quietly closed.

## `github-repo` (OSPS baseline) — 23, unchanged, and 21 are passes

Unchanged from the previous two sweeps and re-stated because the count invites
misreading: this tool uploads one SARIF result per control it evaluated,
*including the ones that passed* ("Repository is public", "Issues are enabled").
The alert count for this tool is its control count. Seven would close together
with a `SECURITY-INSIGHTS.yml`, which still asserts owner-only facts and is
still not invented here.

## Where this leaves the dashboard

| Tool | Before | Expected after | By what |
|---|---:|---:|---|
| Bandit | 50 | 47 | the three `B105` nosecs |
| CodeQL | 0 | 0 | — |
| ESLint | 0 | 0 | — |
| Scorecard | 42 | 39–40 | 1 workflow deleted, 2 `downloadThenRun` closed; the permission moves trade top-level for job-level rather than closing |
| github-repo | 23 | 23 | owner action |
| **Total** | **115** | **~109** | |

The honest summary is smaller than the alert delta suggests, and larger than it
in the way that matters: **one dead workflow removed, one remote-code-as-root
install path eliminated, one previously-merged permissions fix restored after a
silent revert, and three new CI invariants so that none of the three can be
undone quietly again.**

## What is still not done

- **The 47 Bandit findings**, `B615` most of all. Listed above with reasons.
- **`SECURITY-INSIGHTS.yml`** — 7 `github-repo` alerts, owner-only facts.
- **BinSkim** — 0 alerts, 412 analyses, most recent 2026-07-06, from a workflow
  that no longer exists. Retiring the orphaned analyses is a
  `code-scanning-cleanup.yml` dispatch with `tool: BinSkim`, `apply: true`, and
  it is irreversible, so it stays the owner's call.
- **`STEP_SECURITY_API_KEY` is still not configured.** Every `harden-runner`
  step logs `api-key is not set while use-policy-store is true. Defaulting to
  audit mode` — ~20 workflows ask for egress blocking and get monitoring.
- **`continuous-security.yml` is green and hollow.** Either give it
  `ANTHROPIC_API_KEY` or delete it; a nightly green tick for a skipped step is
  worse than a red one.
- **The three repository-settings Scorecard alerts** — `BranchProtectionID`,
  `CodeReviewID`, `CIIBestPracticesID`. No diff closes them.

## A note on method

Two things in this sweep were only visible because the run history was read
instead of the file, and both had fooled a previous pass:
`auto-dependency-update.yml` looked present and pinned and had failed 22 times,
and `continuous-security.yml` reports success while skipping its only real step.
Round one's lesson was that a scanner can be configured to ignore its own
config; round two's was that a plan entry is not evidence code exists. This
round's is narrower and the same shape: **a workflow that is on `main`, pinned,
and green is still not necessarily doing anything.**

---

# Round two — the same day, and the thing the dashboard could not tell us

Round one closed with a prediction and a list of what was not done. This
section is the measurement, plus a finding that no code-scanning tool reports
because it was never in a scanned commit range.

## The read

**Code scanning cleanup**, no inputs, run
[32377434087](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/32377434087),
`main` at `3c15d9bf`.

```
Open code-scanning alerts on beer-sakthai/Sak-Family-Agent: 89

tool         open alerts  analyses  latest analysis
-----------  -----------  --------  --------------------
Bandit       47           1416      2026-08-20T13:57:11Z
BinSkim      0            412       2026-07-06T05:01:03Z
CodeQL       0            10546     2026-08-20T13:58:00Z
ESLint       0            3301      2026-08-20T13:57:14Z
Scorecard    19           1679      2026-08-20T13:57:22Z
github-repo  23           1         2026-08-17T09:47:23Z
mobsfscan    0            14        2026-08-12T04:14:21Z
```

**115 → 89.** Against round one's predictions:

| Tool | Predicted | Actual | |
|---|---:|---:|---|
| Bandit | 47 | **47** | exact |
| Scorecard | 39–40 | **19** | **prediction was wrong, and wrong in an instructive way** |
| CodeQL / ESLint | 0 / 0 | 0 / 0 | held |
| github-repo | 23 | 23 | held |

### Correcting round one on `TokenPermissionsID`

Round one said, twice and emphatically, that moving `contents: write` from the
top level to the job level "does not lower the raw alert count" because
job-level writes are flagged too, and that counting it as −3 "would be wrong and
is not claimed."

**All 21 `TokenPermissionsID` alerts are now closed** — including the ten in
`.lock.yml` files that were never touched. So the caution was misplaced:
Scorecard re-scored the whole check rather than re-reporting per site. The
conservative claim was the safer one to publish and it was still incorrect, which
is worth recording as plainly as the prediction that held.

Both `downloadThenRun` alerts closed as expected. The 19 that remain: 15 ×
`npmCommand not pinned by hash` in gh-aw `.lock.yml` compiler output, the one
critical `DangerousWorkflowID` that is displayed-not-live, and the three
repository-settings checks.

## The finding the dashboard cannot show: a live credential on a branch

A gitleaks sweep across **all four branches and all 3,448 commits** turned up
one real, unrotated credential:

```
scripts/family-status.sh:3-4   on jules-refactor-eval-viewer-9438d504-…
  export KAGGLE_USERNAME="…"
  export KAGGLE_API_TOKEN="…"     37 chars, entropy 3.99, not a placeholder
```

Committed 2026-07-25 and still at that branch's tip on 2026-08-20 — **26 days on
a public repository with a fork.** Neither variable is used; nothing in the
script references Kaggle. `main` had already dropped both lines; the branch
never did.

Everything else the sweep found is a false positive, confirmed by reading each
one: prose (`…Python API, S3-compatible API (AWS CLI, boto3, s5cmd)` — the
"secret" gitleaks reports is the string `S3-compatible`), and obvious
placeholders — a `Bearer YOUR_TOKEN` example in a curl snippet, and a commented
sample token in `security/SECURITY_FIXES_PLAN.md` whose value is the literal
"abc" / "def" filler. (Quoting that second one verbatim here made *this
document* trip the scanner, which is its own small illustration of why
`generic-api-key` fires as often as it does.)

History also holds real credentials in files long deleted from `main` — a
`secrets.py` with two Slack app tokens and a private key, `api_key` values in old
`config/config.yaml` and `default/config.yaml`, and the `H9hhwS…` token
`.gitleaks.toml`'s own comment already says must be rotated.

### Why deleting does not fix any of it

The credential was removed from the branch tip. **That is not remediation.** The
repository is public and forked; the value is in three commits of that branch's
history; GitHub keeps unreachable objects fetchable by SHA until Support
garbage-collects them; and a fork keeps its own copy. A full history rewrite
(`filter-repo`/BFG) would change every commit SHA, break roughly 1,050 pull
request references and every existing clone, and *still* not close it.

**Rotation at the provider is the only action that closes a leaked credential.**
That is what `.gitleaks.toml`'s existing comment argues for the `H9hhwS…` token,
and it is still outstanding for that one.

## Why it went unreported for 26 days

`secret-scan.yml`'s header claimed it "scans the full git history." It does not,
and could not have caught this in two independent ways:

1. **`on: push` is filtered to `branches: [main]`.** A push to any other branch
   is never scanned at all.
2. **`gitleaks-action` scans the pushed commit *range***, not the tree —
   `--log-opts=--no-merges --first-parent <before>^..<after>`, visible in any of
   its run logs. `fetch-depth: 0` makes history available to gitleaks; it does
   not make the action ask for it.

Together: a branch with no open pull request is looked at by nothing, forever.

### The fix

A second job, `branch-sweep`, on a weekly schedule and manual dispatch. It
checks out **every branch tip** and scans the **tree** rather than a range, with
a gitleaks binary pinned by version and SHA-256 (downloaded and checksummed, not
piped into a shell — the rule round one established).

Two details are load-bearing, and testing found both:

- **The config comes from the default branch**, passed with `--config`. Reading
  each branch's own `.gitleaks.toml` would let a branch silence a finding about
  itself by committing an allowlist entry beside the secret.
- **`git clean -qxffd` runs between branches.** `--no-git` scans the working
  *directory*, and `git checkout` only manages *tracked* files — so an untracked
  or gitignored file survives into the next branch's scan. The first version of
  this job reported a single planted file against **all four branches**,
  including ones that never contained it. That bug was found by planting a
  canary, not by reading the script.

Verified in three states before commit: baseline (4 branches clean, exit 0); a
tracked secret planted on one branch (**only** that branch flagged, exit 1); and
an untracked gitignored leftover in the workdir (attributed to no branch, exit
0).

The prose false positive is allowlisted **by value** (`S3-compatible`) rather
than by path, and that choice was tested too: injecting a Slack token into the
same allowlisted file is still caught.

`tests/test_workflow_hygiene.py` pins the schedule trigger, the job's existence,
the `git clean`, the default-branch `--config`, and the pinned digest — each
verified by breaking it.

## What is still not done

- **Rotate the credentials.** Kaggle (found here), the Slack app tokens and
  private key in the deleted `secrets.py`, the old `config.yaml` `api_key`s, and
  `H9hhwS…`. Owner action, and the only real remediation.
- **The 47 Bandit findings**, 23 of them `B615`.
- **`continuous-security.yml` is still green and hollow** — see round one.
- **`SECURITY-INSIGHTS.yml`**, the orphaned BinSkim analyses, the unset
  `STEP_SECURITY_API_KEY`, and the three repository-settings Scorecard checks.

## A note on method

Round one's lesson was that a workflow can be on `main`, pinned, and green while
doing nothing. This round's is adjacent: **a scanner can be running, green, and
structurally incapable of seeing the thing it is named for.** Both were found the
same way — by reading what the job actually did rather than what its name or its
header comment said.

## Postscript — the sweep was dispatched, and the *other* job failed

Round two shipped with the branch sweep verified locally and explicitly flagged
as never having run on Actions. It was dispatched manually rather than left for
Friday — run
[32380879026](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/32380879026):

```
Branch sweep   success     (all steps, including the artifact upload)
gitleaks       failure     at "Run gitleaks"
```

The new job worked. The **pre-existing** incremental job failed, and the log
gives the reason without ambiguity:

```
gitleaks cmd: gitleaks detect --redact -v --exit-code=2 --report-format=sarif ... --log-level=debug
```

No `--log-opts`. On an event that carries no commit range, `gitleaks-action`
does not skip — it scans the **entire history**, which still holds credentials
in files long deleted from `main`, and reports ~93 findings. Those need
rotating, not patching, so the run can only ever be red.

This was latent in the file before round two: `workflow_dispatch` was already a
trigger, and run 32380879026 is the **first manual dispatch this workflow has
ever had**, so nothing had exercised it. Round two made it matter, because the
sweep is dispatch-only and a manual run is now the normal way to use this
workflow. The `gitleaks` job is therefore restricted to `push` and
`pull_request` — the two events that carry a range — and the two jobs now cover
disjoint events, pinned by a test.

Push-to-`main` runs stayed green throughout, including on the merge commit, so
the gate that stops a *new* secret landing was never affected.

Worth naming, because it is the third instance of the same shape in this
document: **the job that had never run was the one that was broken.** Dispatching
it on the day it merged, instead of waiting for its first scheduled run, is the
only reason that was found in minutes rather than on Friday.

---

# Round three — the Bandit backlog, and every branch checked rather than one

Rounds one and two both closed with the same two lines under "what is still not
done": the 47 Bandit findings, and a branch sweep that had only ever been run
against `main`'s tip. This round is those two.

## Every branch tip, scanned

Five branches exist. Each tip's **tree** was extracted with `git archive` and
scanned with the same gitleaks the CI job pins — v8.24.3, downloaded and
checked against `9991e0b2…f4ee29c` before running — using the **default
branch's** `.gitleaks.toml`.

```
main                                          0 findings
chore/codeowners-add-fuzz-and-security-tests  0
jules-refactor-eval-viewer-9438d504-…         0
palette/tool-synthesis-card-accessibility-…   0
revert/pr-8ced7bfa-restore-security-agents-…  0
```

The Kaggle token round two found is gone from the branch that carried it. That
still is not remediation — the value is in three commits of a public, forked
repository's history, and **rotation at kaggle.com remains the only thing that
closes it**.

### The first run of that scan reported 7 findings on every branch, and was wrong

Worth recording because it is a trap anyone repeating this will hit. The first
attempt passed `--source <absolute temp dir>`, so gitleaks reported paths like
`/tmp/…/tree-main/personas/…/SKILL.md`. `.gitleaks.toml`'s allowlist is anchored
(`^personas/.*\.md$`, `^security/.*\.md$`), and an anchored pattern cannot match
a path that has been prefixed. Every allowlisted instructional placeholder came
back as a finding.

Re-running with the working directory *inside* each tree, so paths are
repo-relative, gives 0. The lesson is narrow and useful: **a path-anchored
allowlist is silently inert when the scanner is handed absolute paths**, and the
failure mode is false positives, which look like the scanner working.

## Bandit 47 → 8

`bandit -c pyproject.toml -r .` locally. The parity invariant the 2026-08-18
sweep established — local count equals the dashboard's — still holds: both 47.

| Rule | Before | After | How |
|---|---:|---:|---|
| `B615` unpinned HF revision | 23 | **8** | 15 pinned to real commit SHAs resolved from the Hub |
| `B108` hardcoded `/tmp` | 11 | **0** | `tempfile.mkdtemp()`, or a path taken from argv |
| `B110` try/except/pass | 6 | **0** | narrowed the exception; one made to fail closed |
| `B112` try/except/continue | 3 | **0** | narrowed the exception |
| `B310` urllib audit | 4 | **0** | `# nosec B310` — all four URLs are literals |
| **Total** | **47** | **8** | |

### `B615` — pinned where a commit could be resolved, named where it could not

Every `from_pretrained` / `load_dataset` default repo id was looked up against
the Hub API. Fifteen call sites resolved and are now pinned to an immutable
commit, env-overridable alongside the repo id they belong to:

```python
BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
BASE_MODEL_REVISION = os.environ.get(
    "BASE_MODEL_REVISION", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
)
```

**The other eight are not pinned, and deliberately so.** They point at six repos
that do not resolve — `sakthai-coder-3b`, `sakthai-toolcalling-1.5b-lora`,
`sakthai-combined-v5`, `hermes-dataset`, `sakthai-toolcalling-v1`,
`sakthai-cycle-6-sft` — none of which appear in the account's public listing,
and which the scripts themselves push with `private=True`.

Two ways to make those eight go green were available and both were refused.
`revision="main"` satisfies Bandit while pinning nothing — a branch name is not
an immutable commit, and that is the check-gaming this document already declined
once over `DangerousWorkflowID`. Requiring the revision by environment variable
would close them too, at the cost of breaking scripts that may well run fine
today against private repos this session cannot see. **A fabricated SHA is worse
than an open alert**, so the eight stay open with their reason attached:

```
infra/sakthai-training-space/scripts/sft_cycle6.py:76,83,89
training/hf-jobs/train_persona_lora.py:75
training/hf-jobs/train_toolcalling_lora.py:114
training/sakthai-7b-lora/train.py:67
training/serving/eval_toolcalling.py:68
training/serving/export_ollama.py:79
```

Anyone with access to those repos closes all eight by resolving each commit and
pinning it the same way the fifteen are pinned.

### `B110` / `B112` — narrowing, and one check that now fails closed

Bandit does not flag `try/except/pass` when the exception is a specific type,
so narrowing is both the real fix and the one that clears the alert. Four
workbench scripts had a **bare** `except:` around `json.loads` — which also
swallows `KeyboardInterrupt` and `SystemExit` — now `except json.JSONDecodeError`.

One is more than a tidy-up. `agent_workflow/executor.py`'s
`_validate_shell_command` wrapped its path check in `except Exception: pass`:

```python
try:
    _validate_filepath(sub)
except PermissionError as exc:
    raise PermissionError(f"Prohibited sensitive path in shell command: {exc}") from exc
except Exception:
    pass
```

`_validate_filepath` raises `ValueError` for a token that is not a well-formed
path (empty, control characters) — a skip, correctly. But the bare `Exception`
also swallowed *any bug inside the validator*, and a validator that throws
silently stops checking that token. It is `except ValueError` now, so an
unexpected error propagates instead of quietly disabling the check.

The stress harness's `except Exception as e: pass` — which also bound an unused
`e` — now records what it caught into the test's own `details` string, so an
unexpected rejection type is reported rather than counted as nothing.

### `B108` — a predictable name in a world-writable directory

`/tmp/7b-adapter`, `/tmp/metrics.json`, `/tmp/models.json` and friends. `/tmp`
is world-writable, so a fixed filename there can be pre-created or symlinked by
any other user on the host. The training and workbench scripts now write into
`tempfile.mkdtemp()` (0700, unpredictable). The metrics file gets **its own**
directory rather than sharing the adapter's, so a later reordering cannot
accidentally sweep it into the uploaded adapter folder.

The five `scripts/hf/` one-off scrapers read their input from `sys.argv[1]` with
a usage error instead of a hardcoded `/tmp/*.json`. Nothing calls them — checked
before changing the interface — and they are now both safer and usable on a file
that is not in `/tmp`.

### `B310` — four literals, four `nosec`s

All four sites build a `urllib.request.Request` from a compile-time constant:
two literal `http://127.0.0.1:3001/…` URLs in the smoke-test driver, a fixed
`https://api.github.com` root, and a literal `https://datasets-server.huggingface.co/…`.
Bandit cannot see through the `Request` object to the scheme. There is no
attacker-controlled scheme to guard, so a runtime check would be dead code;
these carry `# nosec B310` with the reason, in the repository's existing style.

## Verification

ruff check, ruff format, mypy strict and bandit clean; 4,248 tests pass at
96.22% branch coverage against the 96% floor; the two out-of-tree suites that
the changed files belong to also pass — `agent_workflow_framework` 172 tests,
`agent-self-evolution` 149 tests.

## What is still not done

Unchanged from round two, minus the Bandit line:

- **Rotate the credentials.** Kaggle, the Slack app tokens and private key in
  the deleted `secrets.py`, the old `config.yaml` `api_key`s, and `H9hhwS…`.
- **The eight remaining `B615`**, listed above with the repos that block them.
- **`continuous-security.yml` is still green and hollow.**
- **`SECURITY-INSIGHTS.yml`**, the orphaned BinSkim analyses, the unset
  `STEP_SECURITY_API_KEY`, and the three repository-settings Scorecard checks.
- **`jules-refactor-eval-viewer-…` has no merge base with `main`** — a parallel
  2,565-commit history whose tip carries 201 Bandit findings that never reach
  the dashboard because nothing analyses it. It is the branch that held the
  Kaggle token for 26 days. Deleting it is the owner's call, not an agent's.

## A note on method

Round one: a workflow can be on `main`, pinned and green while doing nothing.
Round two: a scanner can be running and green while structurally unable to see
the thing it is named for. Round three's is the mirror image — **a scanner can
report findings that are purely an artefact of how it was invoked**, and the
seven false positives looked exactly like seven real ones until the invocation,
rather than the findings, was read.

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

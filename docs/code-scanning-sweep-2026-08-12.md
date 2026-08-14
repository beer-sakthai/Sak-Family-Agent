# Code-scanning sweep — 2026-08-12

A full pass over everything that feeds
[the code-scanning dashboard](https://github.com/beer-sakthai/Sak-Family-Agent/security/code-scanning),
run against `main` at `b4cc123`.

**Result: 41 open alerts, every one of them from Scorecard, and 35 of those are
a single rule — `PinnedDependenciesID`.** Every code-analysis tool
(CodeQL, ESLint, Bandit, BinSkim, mobsfscan) reports zero.

```
tool       open alerts  analyses  latest analysis
Bandit     0            412       2026-07-06T05:01:03Z
BinSkim    0            412       2026-07-06T05:01:03Z
CodeQL     0            6352      2026-08-12T11:45:33Z
ESLint     0            1755      2026-08-12T12:24:52Z
Scorecard  41           60        2026-08-12T12:24:49Z
mobsfscan  0            14        2026-08-12T04:14:21Z
```

## Re-read at `bc2ace3` — 47 open

Later the same day, `main` took PR #620 (`b950cb9`, "Add Black Duck security
scan CI workflow"). The dashboard was re-read afterwards by dispatching **Code
scanning cleanup** from the Actions tab — run
[31613921849](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31613921849),
the first read in this document taken *from the dashboard itself* rather than
reconstructed from run logs.

```
tool       open alerts  analyses  latest analysis
Bandit     0            412       2026-07-06T05:01:03Z
BinSkim    0            412       2026-07-06T05:01:03Z
CodeQL     0            6364      2026-08-12T15:32:01Z
ESLint     0            1768      2026-08-12T15:28:31Z
Scorecard  47           78        2026-08-12T15:28:37Z
mobsfscan  0            14        2026-08-12T04:14:21Z
```

Still every open alert is Scorecard's, and every code-analysis tool still
reports zero. The 41 → 47 move is six alerts:

| Rule | Alert | Where | Diff-closable? |
|---|---|---|---|
| `PinnedDependenciesID` | #15489 | `black-duck-security-scan-ci.yml:32` — `actions/checkout@v4`, "GitHub-owned GitHubAction not pinned by hash" | **yes — fixed** |
| `TokenPermissionsID` | #15488 | `black-duck-security-scan-ci.yml:1` — "no topLevel permission defined" | **yes — fixed** |
| `TokenPermissionsID` | #15486 | `black-duck-security-scan-ci.yml:27` — jobLevel `security-events: write` | no — needed to upload SARIF |
| `TokenPermissionsID` | #15487 | `code-scanning-cleanup.yml:42` — jobLevel `security-events: write` | no — that permission *is* the workflow |
| `TokenPermissionsID` | #15485 | `auto-dependency-update.yml:24` — jobLevel `contents: write` | no |
| `TokenPermissionsID` | #15381 | `continuous-security.yml:32` — jobLevel `contents: write` | no |

The four un-closable `TokenPermissionsID` alerts are the *result* of the
earlier fix, not a regression against it: PR #599 closed four of these by
demoting top-level `contents: write` to job-scoped write, and Scorecard flags
the job-scoped grant too. A workflow that pushes commits needs `contents:
write` somewhere, and one that uploads SARIF needs `security-events: write`;
the only remaining lever is which scope holds it, and job scope is already the
tighter of the two. They are accepted risk.

Both closable alerts were regressions in the Black Duck workflow, which was
added from GitHub's stock starter template and so did not carry any of this
repository's workflow conventions. Fixed on
`claude/code-scanning-security-57ez7c`: top-level `permissions: contents: read`
added, `actions/checkout` pinned to the same
`3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` every other workflow uses,
and the `step-security/harden-runner` audit step added to match the other 19
workflows (convention, not an alert). The Black Duck action itself was already
pinned to a commit SHA, so it was never flagged.

`PinnedDependenciesID` is therefore back to 35 — the same `pipCommand` /
`npmCommand` / `downloadThenRun` set analysed below, unchanged and still the
one open scope decision.

**Separately, the Black Duck workflow fails on every run** (runs
[31612179954](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31612179954)
and
[31612447945](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31612447945)):
it reads `vars.BLACKDUCKSCA_URL` / `vars.COVERITY_URL` / `vars.POLARIS_SERVER_URL`
/ `vars.SRM_URL` and four matching secrets, none of which are configured on this
repository. It runs on every push and PR to `main`, so it is red on every PR
until either those credentials are added or the workflow is removed. That is a
CI question, not a code-scanning one, and it is the repository owner's call —
nothing here changes it.

### Correction

An earlier revision of this document claimed the dashboard held "~15k orphaned
Codacy alerts" that no code change could clear. **That was wrong**, and it is
recorded here rather than quietly deleted because the reasoning failed in an
instructive way.

The claim was inferred, never measured. `7224074c` ("remove broken Codacy
workflow") says in its message that the workflow *had* uploaded ~15k
style-level findings, and a run log confirmed one such upload really did
succeed on `main` in July. From those two true facts the conclusion "therefore
~15k Codacy alerts are still open" was assembled and written up as if observed
— while the dashboard itself sat behind a 403 the whole time. Codacy does not
appear on the dashboard at all; whatever it uploaded is long gone.

The lesson is narrow and worth keeping: a chain of correct evidence is not a
measurement, and "I could not read the source of truth" is a reason to label a
conclusion provisional, not a licence to state it flatly.

## Re-read at `c0cc7e0` (2026-08-13, 21:35Z) — 6 open

Read the same way — **Code scanning cleanup**, no inputs, run
[31746348341](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31746348341).
This is the current state; everything below it is history.

```
tool       open alerts  analyses  latest analysis
Bandit     0            412       2026-07-06T05:01:03Z
BinSkim    0            412       2026-07-06T05:01:03Z
CodeQL     0            6821      2026-08-13T21:35:28Z
ESLint     0            1946      2026-08-13T21:34:05Z
Scorecard  6            351       2026-08-13T21:11:13Z
mobsfscan  0            14        2026-08-12T04:14:21Z
```

37 → 6. **Every `PinnedDependenciesID` alert is gone, and no diff closed
them.** `Dockerfile.sandbox` still runs `pip install --no-cache-dir -e "."`,
`scripts/bootstrap.sh` still runs an unpinned `uv pip install -e ".[dev]"`, and
the `gh-env.sh` / `comfyui_setup.sh` / `evolve_agent.sh` copies are untouched —
so the deployed-script class this document spent three sweeps deferring left
the dashboard some other way.

### What actually happened to them — measured, not inferred

The first draft of this section said they had "overwhelmingly likely" been
dismissed as accepted risk from the Security tab, that being the option the
Remediation section offered. **That was wrong**, and it is recorded here rather
than quietly corrected because it is the same mistake as the Correction above,
made again in the same document: a plausible chain of reasoning written up
before the source of truth was read.

The listing script only ever queried `state=open`, so a dismissed alert and one
a fix closed looked identical to it. It now takes `--state`
(`open`/`closed`/`dismissed`/`fixed`/`all`) and prints each alert's real state
with its dismissal reason, and the cleanup workflow reports the closed set on
every run. Two reads settled it (runs
[31749296602](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31749296602)
and
[31749507755](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31749507755)):

```
Dismissed alerts: 12 — all CodeQL, 0 Scorecard
Closed alerts:   166 — Scorecard 91, CodeQL 73, ESLint 2

Scorecard closed, by rule:
  76  PinnedDependenciesID  sev=medium  state=fixed
  14  TokenPermissionsID    sev=high    state=fixed
   1  SASTID                sev=medium  state=fixed
```

**Not one Scorecard alert was ever dismissed.** All 76
`PinnedDependenciesID` alerts sit in state `fixed` — GitHub's word for "a
newer analysis from the same tool stopped reporting it". Six of those really
were fixed by a diff (`pylint.yml`'s four, `setup-extensions.sh` and its
twin). The rest were closed with their inputs unchanged: the unpinned `pip`,
`npm` and `curl | bash` lines are all still in the tree, verified file by file.

So this is neither a fix nor an accepted risk. It is Scorecard no longer
emitting a finding it used to emit, against a repository that did not change —
the same re-scoring behaviour this document already recorded when four
`TokenPermissionsID` alerts vanished after the two *top-level* ones were fixed
(and 14 now sit closed under that rule). **The practical consequence is that
they can come back.** Nothing about the supply-chain exposure improved; only
the reporting did. The scope decision in the Remediation section is therefore
still live and still unmade, and a future scan reopening 29 alerts is the
expected case, not a surprise.

The narrower lesson, which is worth more than the alert count: "the dashboard
no longer shows it" and "it is fixed" are different claims, and the tool that
could not tell them apart was the reason for guessing. That is now a one-line
read.

What remains is the six repository-health checks, one alert each:

| Alert | Rule | Sev | Closable by a diff? |
|---|---|---|---|
| #15379 | `BranchProtectionID` | high | no — repository settings |
| #15460 | `CodeReviewID` | high | no — process; 0/7 approved changesets |
| #15461 | `MaintainedID` | high | no — repo age, auto-closes after 2026-09-13 |
| #15464 | `VulnerabilitiesID` | high | no — no upstream fix exists |
| #15463 | `FuzzingID` | medium | **yes — see below** |
| #15462 | `CIIBestPracticesID` | low | no — badge is `InProgress` on bestpractices.dev |

`CodeReviewID` has moved from "0/2" to "0/7 approved changesets": the window
has grown and none of it is reviewed yet, which is what the policy adopted on
2026-08-13 is for. `CIIBestPracticesID` now reads "score is 2: badge detected:
InProgress" rather than reporting no badge at all — a badge project exists and
is partly filled in; finishing it happens on bestpractices.dev, not in a PR.

### `VulnerabilitiesID` #15464 — re-checked against OSV

Still `sqlitedict` (`PYSEC-2026-1939` / `GHSA-g4r7-86gm-pgqc`), transitive via
`lm-eval` in the `evals` group. Re-queried directly rather than taken from the
earlier note: PyPI's latest release **is** 2.1.0, and the advisory's affected
range ends in `last_affected: 2.1.0` with **no `fixed` event** — there is no
version to bump to. The only lever is dropping `lm-eval`, which would delete
the weekly `run-evals.yml` capability to close one alert on an optional
dependency group. Not taken; it clears itself if upstream ever publishes a fix.

> **Decided 2026-08-14 — accepted risk, written up in
> [`SECURITY.md`](SECURITY.md#accepted-dependency-risk-sqlitedict-pysec-2026-1939).**
> Re-verified against PyPI and OSV: `sqlitedict` 2.1.0 is the newest release,
> its last upload was 2022-12-03 (unmaintained), the advisory has no `fixed`
> event, and every `lm-eval` release including `0.5.0.dev1` still requires it.
> pip-audit over runtime + extras reports **zero**; the finding appears only
> once the `evals` group is included. The reachable path is `lm-eval`'s own
> local result cache in a CI job — no attacker-controlled input — so the alert
> is accepted rather than closed, with the reasoning and the re-evaluation
> triggers recorded in SECURITY.md. Dismiss #15464 in the Security tab as
> "won't fix" to take it off the dashboard; nothing in a diff will.

### `FuzzingID` #15463 — closed by this change

The previous sweeps filed this alongside branch protection and repo age as
"repository-health, no diff can close it", and `PLAN.md` says the same. **That
was wrong.** Scorecard's Fuzzing check is file-based, and for Python it is one
pattern, read from
[`checks/raw/fuzzing.go`](https://github.com/ossf/scorecard/blob/main/checks/raw/fuzzing.go):

```go
clients.Python: {
    filePatterns: []string{"*.py"},
    funcPattern:  `import atheris`,
    Name:         fuzzers.PythonAtheris,
},
```

Any `*.py` file containing the literal text `import atheris` satisfies it.
Worth noting what does *not*: the `hypothesis` property-based suite this
repository already has in `tests/test_store_properties.py` counts for nothing
here — Scorecard has property-based detectors for Haskell, Erlang, Elixir,
Gleam, JavaScript and TypeScript, but Python's only entry is Atheris.

That makes the check trivially game-able by a file that imports Atheris and
fuzzes nothing, which is not what was done. `fuzz/` holds three harnesses over
the boundaries that actually take attacker-shaped input, each asserting a
security invariant rather than merely "did not crash":

| Harness | Target | Invariant |
|---|---|---|
| `fuzz_giturl.py` | `validate_git_url` | an accepted URL cannot smuggle a git option, cannot select a remote-helper transport, and carries an allowed scheme |
| `fuzz_guardrails.py` | `GuardrailPolicy.check_pre_execution` | never raises; always returns a `GuardrailResult` with an in-enum action, a dict `modified_args`, and a non-empty reason on `DENY` |
| `fuzz_mcp_server.py` | `mcp.server.handle_request` | never raises; returns `None` or a JSON-RPC 2.0 response carrying exactly one of `result`/`error`, and that response is JSON-serialisable |

Three details are load-bearing:

- **`atheris.instrument_all()` in `main()`.** Without it libFuzzer reports "no
  interesting inputs were found", the corpus never grows past one entry, and
  the campaign degrades into a random input generator. The first run of these
  harnesses did exactly that — 200k runs at `corp: 1/1b` — which looks like a
  clean campaign and measures nothing.
- **A seed corpus in `fuzz/corpus/<harness>/`.** The MCP handler dispatches on
  literal method strings, so an unseeded campaign has to rediscover
  `tools/call` by mutation: 90 seconds reached **85 edges** unseeded and
  **965** seeded (features 117 → 3831, corpus 9 → 285). `tests/test_fuzz_harnesses.py`
  parametrises over the same directory, so pytest and libFuzzer share one set
  of interesting inputs instead of two that drift.
- **Only store-backed tools are exposed to the MCP harness.** `tools/call`
  really invokes the handler, so handing the fuzzer all of `BUILTIN_TOOLS`
  would let it reach `run_command`, `read_file` and the Telegram/Graph network
  tools with fuzzer-controlled arguments. It gets `learn`/`recall`/`search`/
  `forget`, and a test pins that set.

Atheris is a `fuzz` dependency group, not part of `dev`: it needs a matching
clang toolchain, so putting it in the default install would break
`uv sync --all-extras` on machines without one. CI therefore never installs it,
which is why each harness keeps its invariant in a plain `exercise(bytes)`
function importing nothing from Atheris — `tests/test_fuzz_harnesses.py` calls
those directly, so the harnesses cannot rot between campaigns. Two of those
tests deliberately break the code under test and assert the invariant *fails*,
because a harness that passes unconditionally is worse than none.

Campaigns run before commit, all clean: giturl 12.8M runs (cov 18), guardrails
53.9k runs (cov 1032, ft 5076), MCP 150k runs seeded (cov 965, ft 3831).

The alert closes on the next Scorecard scan after this merges, not on merge.

## Re-read at `fa6bfc9` — 37 open

Read from the dashboard the same way, dispatching **Code scanning cleanup**
with no inputs — run
[31660389121](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31660389121),
`main` at `fa6bfc9`, 2026-08-13.
## Re-read at `fa6bfc9` (2026-08-13) — 37 open

Read the same way, from the dashboard itself: **Code scanning cleanup** with no
inputs, run
[31660389121](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/31660389121).

```
tool       open alerts  analyses  latest analysis
Bandit     0            412       2026-07-06T05:01:03Z
BinSkim    0            412       2026-07-06T05:01:03Z
CodeQL     0            6535      2026-08-13T02:12:57Z
ESLint     0            1838      2026-08-13T02:11:46Z
Scorecard  37           138       2026-08-13T02:11:59Z
mobsfscan  0            14        2026-08-12T04:14:21Z
```

47 → 37. The four `TokenPermissionsID` alerts and `PinnedDependenciesID` #15489
are gone (the Black Duck fixes above landed), `pylint.yml`'s four closed with
the `uv.lock` pin, and `VulnerabilitiesID` no longer appears. What remains is
31 `PinnedDependenciesID` — the deployed-script set, still the one open scope
decision — plus the six repository-health checks, of which `CodeReviewID` is
the subject of the next section.

## `CodeReviewID` #15460 — what it measures, and the decision

```
#15460  CodeReviewID  sev=high  ref=refs/heads/main
    score is 0: Found 0/2 approved changesets -- score normalized to 0
```

The earlier table above marks this "no — repository settings", which is true
about a *diff* and was the wrong place to stop: it is closable by a process
change, and this section records the mechanism and the choice made.

### The mechanism, read from the source

Scorecard's Code-Review check reduces to one predicate per changeset, in
[`probes/codeApproved`](https://github.com/ossf/scorecard/blob/main/probes/codeApproved/impl.go):

```go
for _, review := range c.Reviews {
	if review.State == "APPROVED" && review.Author.Login != c.Author.Login {
		return true, nil
	}
}
return false, nil
```

So a changeset counts only when it carried a GitHub review in state
`APPROVED` **left by a login other than the author's**. Things that do not
count, and are worth naming because each looks like review from the inside:

- a review left as *Comment* or *Request changes* — only `APPROVED` is read;
- green CI, however many required checks;
- the merge itself, whoever performed it;
- a `# codeql[...]`-style annotation, a commit trailer, or any file in the tree.

Non-GitHub review platforms (Prow, Gerrit, Phabricator, Piper) are accepted
wholesale by that same probe, detected from commit-message trailers. Emitting
those trailers here would score without reviewing anything; it is forgery of a
review record and is not on the table.

Two further behaviours explain the shape of the message. Changesets that are
*both* bot-authored and approved are skipped entirely (`approvedChangeset &&
data.Author.IsBot` → `continue`), so approving Dependabot PRs cannot inflate
the ratio. And the score is proportional — `CreateProportionalScoreResult` over
approved/total — so it moves gradually as reviewed changesets enter the window,
never in one jump on one PR.

### The decision

**Adopted: every PR into `main` gets an approving review from a non-author, and
for agent-opened PRs that reviewer is the repository owner.** Written up in
[`CONTRIBUTING.md`](CONTRIBUTING.md#review-policy-for-main) and summarised for
agents in [`AGENTS.md`](../AGENTS.md).

The trade-off recorded under `BranchProtectionID` below — that requiring
approvers "blocks the agent-driven workflows this repository runs on" — turned
out to be narrower than it reads. Those workflows open PRs authored by
`claude/*`, Sentinel or Dependabot; the owner already merges them by hand.
Approving before merging is one extra click on a PR that was going to be looked
at anyway, and it is precisely the case where a second pair of eyes is worth
the most. What the policy genuinely cannot cover is a PR the owner authors
personally — GitHub forbids self-approval — so those either wait for a second
reviewer or merge unreviewed as a deliberate exception.

Rejected on the way there: a workflow having `github-actions[bot]` approve
every PR. It would satisfy this check and any future branch-protection rule
while deleting the meaning of both, and it would leave the repository worse off
than the open alert does.

### What to expect on the dashboard

Not an immediate close. The score is the approved fraction of a window of
recent changesets, so it climbs as reviewed merges push unreviewed ones out and
reaches its ceiling only once the window is entirely reviewed merges. Until
then #15460 stays open at a rising score. Nothing in a diff — including this
one — moves it; the next read after a run of approved merges is the measurement
that counts.

The matching repository settings, for whenever branch protection is revisited:
*Require a pull request before merging* → *Require approvals: 1*. That is
`BranchProtectionID` (#15379) territory and remains a separate, owner-only
decision — the review habit is what this section commits to, and it does not
depend on the setting being on.
47 → 37. Two changes since `bc2ace3`, both settling predictions this document
made rather than introducing anything new:

- **`PinnedDependenciesID` is 31**, exactly the number the `pylint.yml` fix
  projected — those four are confirmed closed against the live dashboard, not
  just against local reasoning.
- **`TokenPermissionsID` is 0.** The four alerts recorded above as accepted
  risk (#15381/#15485/#15486/#15487, job-scoped `contents`/`security-events:
  write`) are gone from the dashboard. Scorecard re-scored the check once the
  two *top-level* findings were fixed; the job-scoped grants themselves are
  unchanged and still needed. Nothing was dismissed by hand.

The remaining 37 are 31 `PinnedDependenciesID` plus the six repository-health
checks (`BranchProtectionID`, `CodeReviewID`, `MaintainedID`,
`VulnerabilitiesID`, `FuzzingID`, `CIIBestPracticesID`) — one alert each, none
closable by a diff. Alert numbers moved (`BranchProtectionID` is #15379 now,
`CIIBestPracticesID` #15462, and so on): Scorecard mints new alert IDs per
analysis, so cite them with the read they came from.

Two of the 31 are closed by the `setup-extensions.sh` work below, taking
`PinnedDependenciesID` to **29**.

## Reading the dashboard

Listing alerts needs the "Code scanning alerts" repository permission
(`security_events` on a classic PAT). Neither an agent session's token nor a
plain checkout carries it — `GET /code-scanning/alerts`,
`/code-scanning/analyses` and `/code-scanning/default-setup` all return
`403 Resource not accessible by integration`.

The permission *is* one a workflow can grant its own `GITHUB_TOKEN` per job,
the same way `ossar.yml` and `scorecard.yml` already upload SARIF. That is what
`.github/workflows/code-scanning-cleanup.yml` is for, and running it is the
only way anyone without a PAT gets to see this list:

```
Actions → Code scanning cleanup → Run workflow      # no inputs = read-only report
```

Two sweeps (PR #599 and this one) reconstructed the alert set from run logs and
local re-analysis instead, and this one drew the wrong conclusion doing it.
Read the dashboard first.

An agent session *can* dispatch this workflow (`POST
/actions/workflows/code-scanning-cleanup.yml/dispatches`) even though it cannot
call `/code-scanning/alerts` directly, and then read the numbers out of the job
log. That is how the `bc2ace3` re-read above was taken, and it is the route to
prefer over reconstruction.

## What actually uploads to the dashboard

Only two workflows call `github/codeql-action/upload-sarif`
(`ossar.yml`, `scorecard.yml`); CodeQL itself runs through default setup, which
is configured in repository settings and has no workflow file.

| Tool | Source | Open alerts | Notes |
|---|---|---|---|
| **CodeQL** | default setup — `python`, `javascript-typescript`, `actions` | **0** | also reproduced locally, below |
| **ESLint** | `ossar.yml` → `microsoft/security-devops-action` | **0** | job 94034310166: `Active results: 0` |
| **Scorecard** | `scorecard.yml` | **41** | the entire dashboard; broken down below |
| **Bandit**, **BinSkim** | `ossar.yml`, before it was narrowed to `tools: eslint` | **0** | last analysis 2026-07-06; dormant but clean |
| **mobsfscan** | `mobsf.yml`, added and removed 2026-08-12 | **0** | 14 analyses, no open alerts |
| **gitleaks** | `secret-scan.yml` | — | uploads an artifact only, never to the dashboard |

### CodeQL — reproduced at 0

Default setup pins CodeQL CLI **2.26.2** with query packs `python-queries`
1.8.7, `javascript-queries` 2.4.2 and `actions-queries` 0.6.32, running each
language's default `code-scanning` suite (45 queries for Python). Matching that
exactly matters: the `security-extended` suite would report findings the
dashboard does not have.

```bash
BUNDLE=https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.26.2/codeql-bundle-linux64.tar.gz
curl -sSL "$BUNDLE" | tar xz            # unpacks ./codeql

for lang in python javascript-typescript actions; do
  ./codeql/codeql database create "db-$lang" --language="$lang" --source-root=. --overwrite
done

./codeql/codeql database analyze db-python               python-code-scanning.qls     --format=sarif-latest --output=python.sarif
./codeql/codeql database analyze db-javascript-typescript javascript-code-scanning.qls --format=sarif-latest --output=javascript.sarif
./codeql/codeql database analyze db-actions              actions-code-scanning.qls    --format=sarif-latest --output=actions.sarif

jq '.runs[0].results | length' python.sarif javascript.sarif actions.sarif   # → 0 0 0
```

Coverage matched the hosted run file for file — 755 of 756 Python files, 45 of
54 JavaScript/TypeScript files, 17 of 17 Actions files — so this is the same
analysis the dashboard sees, not a narrower one.

The four `py/clear-text-logging-sensitive-data` families and the
`actions/missing-workflow-permissions` finding that PR #599 fixed are all
confirmed still closed, and all 17 workflows carry a top-level `permissions`
block.

### Scorecard — all 41 open alerts

Every open alert is Scorecard's, on `refs/heads/main`:

| Rule | Count | Severity | Closable by a diff? |
|---|---|---|---|
| `PinnedDependenciesID` | **35** | medium | yes, but see below |
| `BranchProtectionID` | 1 | high | no — repository settings |
| `CodeReviewID` | 1 | high | not by a diff — but by a process change; revisited above |
| `MaintainedID` | 1 | high | no — repo is under 90 days old |
| `CodeReviewID` | 1 | high | no — "Found 0/2 approved changesets" |
| `MaintainedID` | 1 | high | no — repo is under 90 days old, auto-closes after 2026-09-13 (see below) |
| `VulnerabilitiesID` | 1 | high | no — "1 existing vulnerabilities detected" (see below) |
| `FuzzingID` | 1 | medium | no — no fuzzing harness |
| `CIIBestPracticesID` | 1 | low | no — no OpenSSF badge |

Six of the seven rules are repository-health checks that no code change can
close. The dashboard is therefore, in substance, **one finding repeated 35
times**.

#### The 35 `PinnedDependenciesID` alerts

All are "not pinned by hash" against an install command, spread over 20 files:

| Kind | Where |
|---|---|
| `pipCommand` (×N) | `Dockerfile.sandbox`, `infra/sakthai-training-space/Dockerfile` (×3), `.github/workflows/pylint.yml` (×4), `.github/workflows/agent-self-evolution.yml`, `scripts/bootstrap.sh`, `*/agent-self-evolution/evolve_agent.sh` (×3), `*/comfyui/scripts/comfyui_setup.sh` (×2 each) |
| `downloadThenRun` | `infra/vm-agents/sakthai-agent-run.sh` (×2), `*/SakX-github-auth/scripts/gh-env.sh` (×5), `*/comfyui_setup.sh` (×2 each) |
| `npmCommand` | `scripts/setup-extensions.sh`, `sakthai-chat-cli/scripts/setup-extensions.sh` |

The persona copies inflate the count: one `comfyui_setup.sh` fix clears 4 alerts
×3 copies, one `gh-env.sh` fix clears 5.

PR #599 met this class and deliberately left it open, with reasoning that still
holds:

> Closing these means `--require-hashes` across transitively-resolved installs
> and vendoring remote installer scripts — substantially more churn and
> breakage risk than the finding warrants.

The files involved are deployed and not exercised by CI: the VM agent launcher,
the training-space Dockerfile, and persona skill setup scripts. Hash-pinning
them is a real supply-chain improvement and a real risk of silently breaking a
running deployment, and it is a scope decision for the repository owner rather
than a cleanup to be done in passing.

##### `pylint.yml` — four of the 35 closed

The reasoning above is about *deployed* scripts CI never runs. It does not
cover `.github/workflows/pylint.yml`, which is the opposite case: CI is the
only thing that runs it, so pinning it can be verified before it merges and
cannot break a deployment. Its four alerts were all `pipCommand`, one per
install line:

```yaml
python -m pip install --upgrade pip
pip install pylint
pip install -e ".[dev]" || pip install -e "."
```

Nothing there says *which* pylint, so the job's own quality gate moved with
whatever PyPI served that morning — a `--fail-under` threshold measured
against an unpinned linter. The workflow now installs through
`astral-sh/setup-uv` (pinned by commit SHA, as every other action in this
repository already is) and `uv sync --locked --all-extras --group lint`, which
resolves every wheel to the sha256 recorded in the committed `uv.lock`.
`--locked` is the part that keeps it closed: a plain `uv sync` would re-resolve
when `pyproject.toml` drifts, quietly restoring the unpinned install, and
`--frozen` would use a stale lock silently instead of failing on it.

pylint moves from an ad-hoc `pip install` to a `lint` dependency group in
`pyproject.toml`, locked at **3.3.9**. It is its own group rather than an
addition to `dev` so `ci.yml`'s `uv sync --all-extras` does not install a
linter it never invokes — the same separation the `evals` group already has.

Verified at the locked version before merging: 8.08/10 against the
`--fail-under=7.0` pass and 9.41/10 against the `--fail-under=9.0` pass, both
unchanged from what the unpinned install produced.

That leaves **31** `PinnedDependenciesID` alerts, all in the deployed-script
set above, still an open scope decision. `agent-self-evolution.yml` is the one
remaining workflow in the list (one `pipCommand`); it installs a *different*
project — `personas/sakthai/agent-self-evolution`, deliberately not a uv
workspace member (see `pyproject.toml`) — so it has no lock in this resolution
to pin against and was left alone rather than half-converted.

##### `setup-extensions.sh` — the two `npmCommand` alerts closed

Same separation as `pylint.yml`, for a different reason. The deployed-script
argument above is about *installs whose inputs this repository does not own*:
hash-pinning them means `--require-hashes` over a transitively-resolved tree,
or vendoring someone else's installer. `scripts/setup-extensions.sh` (#15454)
and its `sakthai-chat-cli` copy (#15452) are neither. They ran

```bash
(cd "$dir" && npm install --silent && npm run build)
```

over a directory that already carries a `package.json` — and, if its author
committed one, a `package-lock.json` with a sha512 for every resolved tarball.
The pinning material was there and the script was not using it. `npm install`
re-resolves against the registry at build time, so a Node MCP server cloned by
`sakthai extensions install <git-url>` built against whatever a matching semver
range served that morning. `npm ci` installs the locked tree and verifies those
hashes, and is what Scorecard accepts (`isNpmUnpinnedDownload` returns early on
`ci`; `install`/`i`/`install-test`/`update` all fall through to unpinned).

`npm ci` *requires* a lockfile, which is the one real behavior change: an
extension shipping none is now reported and skipped rather than installed
unpinned, with the directory printed so its owner can build it by hand. That is
deliberate — the alternative is a fallback branch containing a literal
`npm install`, which both reopens the alert and quietly does the unpinned thing
the alert is about. A lockfile-less extension cannot be installed with
integrity verification at all; the honest response is to say so rather than
pretend.

Verified against a fixture extensions tree (`SAKTHAI_HOME` pointed at a temp
dir): lockfile present → `npm ci` + `npm run build`, at both the `*/` and
`*/*/` glob depths; `npm-shrinkwrap.json` accepted as well as
`package-lock.json`; neither present → skipped, counted, exit 0; missing and
empty `extensions/` directories unchanged.

That leaves **29**.

#### `VulnerabilitiesID`

"1 existing vulnerabilities detected" — the `sqlitedict <= 2.1.0` advisory
(`PYSEC-2026-1939`), transitive via `lm-eval` in the `evals` dependency group.
No fixed version is published upstream, so there is nothing to bump; `pip-audit`
over the runtime lock reports clean. Also documented in PR #599.

#### `MaintainedID` — alert #15461

"score is 0: project was created within the last 90 days. Please review its
contents carefully." Repository was created **2026-06-15**; the alert was
raised on the 2026-08-13 Scorecard scan (repo age 59 days). Scorecard's
[Maintained check](https://github.com/ossf/scorecard/blob/main/docs/checks.md#maintained)
awards a flat **0** to any repository under 90 days old regardless of commit
activity — no diff can raise that score. The check will re-evaluate on the
next scheduled scan after **2026-09-13** (the next Thursday cron after the
90-day mark is 2026-09-17), at which point it starts counting commits/issues
per week: this repository averages many commits per day, so the score will
jump to the maximum on that first post-threshold scan and the alert will
close itself. No action required beyond letting it age out; dismissing it in
the Security tab as "won't fix / accepted risk" is a valid alternative if the
open finding is noise in the interim.

### The advanced/default setup collision

Partway through this sweep, `5648d3ab` ("[StepSecurity] Apply security best
practices", PR #603) added `.github/workflows/codeql.yml` — the stock GitHub
CodeQL starter template, matrix `["javascript", "python", "typescript"]`.

Default setup is enabled on this repository, and the two cannot coexist: every
job from that workflow uploaded its SARIF and then failed with

```
Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled
```

This broke `Analyze (javascript)`, `Analyze (python)` and
`Analyze (typescript)` on `main` and on every open PR, while the default-setup
jobs (`Analyze (javascript-typescript)`, `Analyze (python)`,
`Analyze (actions)`) passed alongside them. The workflow has been removed here,
restoring the state CLAUDE.md already documents:

> CodeQL runs via GitHub's *default setup* (repo settings), so there is
> deliberately no `codeql.yml` — adding one would conflict.

Nothing is lost by removing it. Default setup analyses `python`,
`javascript-typescript` and `actions`; `javascript-typescript` is exactly
`javascript` + `typescript`, so the template's matrix was a strict *subset* of
what already runs — it did not even cover `actions`.

The rest of #603 (the `harden-runner` steps across all workflows,
`dependency-review.yml`, `.pre-commit-config.yaml`, the expanded
`dependabot.yml`) is kept as-is.

**Recurrence, 2026-08-13.** A later "[StepSecurity] Apply security best
practices" commit re-added `.github/workflows/codeql.yml`, this time with the
matrix `["actions", "javascript-typescript", "python"]`. The collision is
identical — the workflow accumulated **69 runs, essentially all failing** with
the same `cannot be processed when the default setup is enabled` error, three
failed jobs per push to `main` and per PR. It has been removed again.

This is the second time an automated remediation bot has reintroduced the file,
so treat it as a standing hazard rather than a one-off: **if a future
StepSecurity/remediation PR adds `codeql.yml`, drop that file from the PR before
merging.** The check is cheap — `.github/workflows/codeql.yml` must not exist as
long as default setup is on. Disabling default setup in repository settings and
keeping an advanced workflow is the only other coherent option, and it would
lose the `actions` language coverage that default setup provides today.

#### The same hazard again, 2026-08-14 — `python-package-conda.yml`

A third stock starter template arrived the same way, in another "[StepSecurity]
Apply security best practices" commit: `.github/workflows/python-package-conda.yml`,
unmodified apart from the bot's own action pinning. It failed **every run,
including on `main`** — 6 of 6 — at

```
EnvironmentFileNotFound: '.../environment.yml' file not found
```

because the template's `conda env update --file environment.yml` refers to a
file this repository has never had. It was removed.

Nothing was lost, and the template was actively wrong for this repository on
four counts beyond the missing file:

- it pins **Python 3.10**, below the `requires-python = ">=3.11"` this project
  declares, so it tested a version the package does not support;
- it lints with **flake8**, while the repo's gate is ruff;
- it runs bare `pytest` under conda, duplicating `ci.yml`'s uv-based run on
  3.11 **and** 3.12 — badly, and without the coverage floor;
- it triggers on `on: [push]`, i.e. every branch, not just `main`/PRs.

There is no conda usage anywhere in this repository. Read together with the two
`codeql.yml` incidents above, the pattern is now three-for-three: **a stock
GitHub Actions starter template added by an automated remediation bot has never
once worked here.** Treat any new `.github/workflows/*` file arriving in a
StepSecurity-style PR as guilty until a green run proves otherwise, and check it
against the repo's actual toolchain (uv, ruff, 3.11+) before merging.

#### `BranchProtectionID`

Scoring 3: admin enforcement off, no required approvers, no CODEOWNERS review,
PRs not required. All repository settings.

Turning these on is a real trade-off, not an oversight: requiring approvers on
`main` blocks the agent-driven workflows this repository runs on (`SakJules`,
`claude/*` branches, the nightly `continuous-security.yml` patch pipeline),
each of which merges its own PRs. `CodeReviewID` ("0/2 approved changesets") is
the same trade-off seen from the other side.

> Revisited 2026-08-13 — see `CodeReviewID` #15460 above. The half of that
> trade-off about *reviews* was overstated: the agent workflows open PRs the
> owner merges by hand, so approving before merging costs a click and blocks
> nothing. A review policy is now adopted. The half about *required approvers
> as a branch-protection setting* stands unchanged and is still open.

Note also that `scorecard.yml` leaves `repo_token` commented out, so Scorecard
reads only what the public API exposes and may be under-reporting what is
actually configured. `main` does in fact require `test (3.11)` and
`test (3.12)` in strict mode.

## Remediation

> Still live as of 2026-08-13, despite `PinnedDependenciesID` reading **0** on
> the dashboard. Those alerts closed as `fixed` without a diff and with the
> files unchanged (measured above), so nothing below has actually been decided
> or done — a future Scorecard scan can reopen all 29. Read the paragraph as
> current, not historical.

**Decide on the remaining 29 `PinnedDependenciesID` alerts.** They are the only
class a diff can close, and closing them touches deployed scripts that CI never
exercises. Either hash-pin them — accepting the maintenance and the breakage
risk — or dismiss them as accepted risk from the Security tab. Doing neither
leaves the dashboard permanently at 29. (The four in `.github/workflows/pylint.yml`
and the two in `scripts/setup-extensions.sh` + its `sakthai-chat-cli` copy are
already fixed; see above. Each was separable for its own reason — CI is the only
consumer of the workflow, and the extension installs had a committed lockfile
they simply were not using.)

**Everything else is a settings or process decision**, not a pull request:
branch protection, an OpenSSF badge, a fuzzing harness, repo age.
`VulnerabilitiesID` clears itself when `sqlitedict` publishes a fix. **Review
policy is decided** as of 2026-08-13 — non-author approval on every PR into
`main`, see `CodeReviewID` #15460 above — and is the one of these that needs
doing rather than deciding.

To re-read the dashboard at any time, run **Code scanning cleanup** from the
Actions tab with no inputs. The same script works locally with a PAT carrying
the "Code scanning alerts" permission:

```bash
export GITHUB_TOKEN=<pat>
python scripts/code_scanning_analyses.py list --alerts

# Why an alert left the open list — fixed, re-scored away, or dismissed?
python scripts/code_scanning_analyses.py list --alerts --state closed
```

`--state` exists because the `open` listing cannot answer that question, and
the 2026-08-13 read needed it: 29 alerts disappeared with no matching diff, and
the first guess at why was wrong. `closed` is the useful one — it covers
`dismissed` and `fixed` together and prints each alert's real state, so an
accepted risk, a diff-driven fix and a scanner that simply stopped reporting
are three distinguishable outcomes rather than one absence. The workflow prints
that set on every run alongside the open one.

Its `delete` subcommand exists for a different problem — retiring a tool that
no longer runs, whose alerts nothing will ever close. Nothing on this dashboard
currently needs it: every tool listed either still runs or already reports zero.

## Also worth knowing

- The **`github-advanced-security` check ("Code scanning AI findings")** fails
  on this repository's PRs at the `Processing Request` step. It is a
  GitHub-side `dynamic/agents/github-advanced-security` workflow, not something
  in this repository; PR #602 merged with it red. Treat it as non-blocking.
- **`mobsf.yml`** was added and removed the same day. It *did* run — 14
  analyses, all reporting zero — contrary to an earlier claim here that it never
  registered a workflow run.
- **`Bandit` and `BinSkim`** still hold 412 analyses each from when `ossar.yml`
  ran the full MSDO tool set, before it was narrowed to `tools: eslint`. Both
  report zero open alerts, so they are dormant rather than orphaned and need no
  action.
- **Dependabot alerts** live on a different tab. The `sqlitedict` advisory shows
  up on *both*: as a Dependabot alert and, counted once, inside Scorecard's
  `VulnerabilitiesID`.

# Test coverage audit — 2026-08-27

Analysis only; no production code changed. Follow-on to
[`docs/test-coverage-audit-2026-08-26.md`](./test-coverage-audit-2026-08-26.md),
re-measured on `main` at commit `a704a40` with that audit's exact command:

```bash
uv sync --all-extras
uv run pytest tests/ -m "not integration" --cov=sakthai --cov-branch --cov-report=term-missing
```

Python 3.11.15 — **2,251 passed, 2 skipped, 6 deselected, 124 subtests** in 368s
over 106 test files (26,515 lines of test against 17,029 lines of package).

## Headline numbers

| Metric | Value |
|---|---|
| Total branch coverage | **95.849%** |
| Floor (`fail_under`) | 96 |
| Headroom | **−0.151pp — floor breached**, `pytest` exits 1 |
| Uncovered statements | 213 |
| Partial branches | 170 |

### One caveat on the number

CI reports **success** on this same commit. That could not be reproduced here:
the exact CI command (`uv run pytest --cov=sakthai --cov-report=xml tests/`)
exits 1 locally at 95.849%. The likeliest cause is the user the suite runs as —
this container runs as root, and at least one test
(`tests/test_security_hardening.py:635`) skips itself when `chmod 000` cannot
lock the current user out of a file, which GitHub's unprivileged runner would
execute. `tests/test_guardrails_hardened.py:419` has the same shape.

Whichever environment is trusted, the margin is under two tenths of a point and
it moves depending on who runs the suite. That fragility is finding 5 below.

## The read

The suite grew by 247 tests in one day and coverage *fell*. That is the whole
story: the gate is a package-wide average, so new code arriving below the
average is absorbed silently until the accumulated headroom runs out. Yesterday's
audit measured that headroom at 0.018pp — roughly one statement — and finding 8
called it out as undetectable erosion. It has now happened.

Nothing on yesterday's findings list has been acted on; `guardrails.py` measures
identically today (89%, 44 miss / 36 partial). Findings 3 and 6 below are that
audit's, re-verified as still open. Findings 1, 2, 4 and 5 are new.

---

## What one day did

Both rows measured with the identical command, so everything but the code is
held constant.

| Measure | 26 Aug | 27 Aug | Δ |
|---|---:|---:|---:|
| Branch coverage | 96.018% | **95.849%** | −0.169 |
| Uncovered statements | 168 | 213 | +45 |
| Partial branches | 149 | 170 | +21 |
| Tests passing | 2,004 | 2,251 | +247 |
| Test files | 101 | 106 | +5 |

---

## 1. The gate measures the average, so new code can only dilute it

**Severity: high** · `pyproject.toml` · mechanism, not a symptom

`fail_under = 96` is a whole-package threshold over 7,688 statements. A module
landing at 88% fails nothing — it spends headroom that the rest of the package
built up. There is no per-file floor and no diff-coverage gate, so the only
signal is the aggregate, and the aggregate is dominated by code written months
ago.

Everything else in this document is a consequence of that.

**Proposal**

- Add a per-file floor so a module cannot land far under the package average
  unnoticed — `coverage report --fail-under` per file, or a short check over
  `coverage.json` in the CI step that already runs.
- Better, gate the diff: require new and changed lines in a PR to clear a higher
  bar (95–100%) than the package. That targets the failure mode directly and asks
  nobody to retrofit old code.
- Only then re-set `fail_under` to the real number, and fix two stale claims
  about it: `ci.yml`'s comment says the floor is 85 (it is 96), and `CLAUDE.md`
  records 96.56% over 1,978 tests in 95 files — none of which still holds.
- `CLAUDE.md` also states CI passes `--cov-branch`. It does not; branch coverage
  is on because `[tool.coverage.run] branch = true`. Harmless, but the doc
  describes a flag that isn't there.

## 2. The client-onboarding subsystem is the drop, and it is the newest code in the repo

**Severity: high** · `client/`, `cli/client.py` · 45 uncovered units

PR #1198 merged the ServiceQuoteBot onboarding path today. Four modules, none of
which existed at the audit commit `c50d28f`, all below the package average:

| Module | Cover | Miss | Partial |
|---|---:|---:|---:|
| `cli/client.py` | 87.6% | 15 | 3 |
| `client/manager.py` | 89.5% | 6 | 6 |
| `client/verifier.py` | 88.3% | 6 | 3 |
| `client/models.py` | 93.4% | 3 | 3 |

What is uncovered is consistent: every `except` / `sys.exit(1)` pair in the CLI
(`cli/client.py:72,154,190`), the interactive `click.prompt` fallbacks taken when
required flags are omitted (`:129-131`), the malformed `--allowed-users` parse
error (`:137`), `load_client` raising, the corrupt-`client.json` warning path in
`list_clients`, and the missing-price-book branch of `onboard_client`
(`manager.py:216`). These are the paths an operator hits on a first bad
invocation.

**Proposal**

- A `CliRunner` table over the failure modes: unknown client id, non-integer in
  `--allowed-users`, missing price book, unwritable clients dir. Assert the exit
  code *and* the message — these are the operator's only feedback.
- Point `SAKTHAI_CLIENTS_DIR` at `tmp_path` and write a genuinely corrupt
  `client.json`. That path currently swallows the exception with a log line and
  nothing asserts it stays non-fatal.
- `client/verifier.py`'s per-case `except` (`:142-145`) is untested, so a
  synthetic check that *raises* is currently indistinguishable from one that
  *fails*. Separating those two is the entire point of a pre-flight verifier.

## 3. The largest single gap is in the security module, and it needs a decision before it needs tests

**Severity: high** · `agent/guardrails.py` · 89.2% · 44 miss / 36 partial ·
*carried from 2026-08-26, unchanged*

The biggest absolute gap in the package, in its most-attacked file. The bulk is
one contiguous block, lines 866–910: the `docker` / `podman` / `kubectl` rules
for `-v=`, `--volume=`, `--mount source=` and `cp`.

Yesterday's audit traced *why* they are uncovered and the trace is the finding:
those commands are already denied earlier by `_check_destructive_tokens`, so the
container-specific rules never execute. Untested and unreachable are different
problems and only one is fixed by writing a test.

**Proposal**

- Settle it. If the generic rule genuinely covers these forms, delete the
  shadowed block and keep regression tests proving the generic rule denies each
  command form. If it does not, reorder so the specific rule runs first — then it
  is testable.
- The same uncovered set includes the `make -f`/`-C` recipe recursion (368–447),
  the nested shell `-c` walk-back (461), the interpreter `-c` detection (513) and
  `dd if=`/`of=` (776). These are bypass-prevention branches; an untested branch
  here is an unverified security control, not a coverage statistic.
- Guardrails logic is duplicated byte-for-byte across five personas and pinned by
  `tests/test_persona_guardrails_parity.py`, so one fix propagates. Worth doing
  once, properly.

## 4. 72 test files that no workflow runs

**Severity: medium** · `sakthai-chat-cli/` · structural

`sakthai-chat-cli/` holds 227 Python modules and its own suite of 72 test files
under `sakthai-chat-cli/tests/`. Grepping `.github/workflows/` for the path
returns `bandit.yml` and `codeql.yml` — both scanners. Nothing executes those
tests. `pyproject.toml` sets `testpaths = ["tests"]`, so the root suite never
reaches them either.

The sibling trees are wired up: `apps/` has `apps.yml`, `agent-self-evolution`
has its own workflow. This one tree has tests written and left unexecuted, which
is the worst of both — the maintenance cost of a suite with none of the signal.

**Proposal**

- Either add a path-filtered job that runs them (`apps.yml` is the pattern), or
  state in its `MIGRATION_NOTE.md` that the tree is archived and its suite is
  unmaintained. Both are defensible; the current silence is not.
- If they are run, expect breakage — `CLAUDE.md` notes its docs still describe a
  five-persona roster, so the tree has drifted.

## 5. The coverage number depends on which user runs the suite

**Severity: medium** · `tests/` · reproducibility

Two tests branch on filesystem permissions and self-skip when `chmod` cannot
restrict the current user — `test_security_hardening.py:635` (TOCTOU
unreadable-file path) and `test_guardrails_hardened.py:419`. Running as root
skips them; running unprivileged executes them. With the gate margin at ~0.15pp,
that difference is large enough to flip the result, which is the most likely
explanation for CI passing where a local root run fails.

**Proposal**

- Make those tests deterministic rather than conditional — drop privileges for
  the assertion, or simulate the unreadable case by patching `os.access` /
  `open` so the branch is exercised identically for every user.
- A gate whose outcome depends on the invoking user is not a gate. This is cheap
  to fix and it makes finding 1's threshold trustworthy.

## 6. Still open from 2026-08-26

Re-verified today, all unchanged:

- **`telegram/bot.py`** — hidden by the coverage `omit`; measured at 38% with
  `_is_authorized` (the only barrier between an arbitrary Telegram user and an
  in-process `run_agent()` call) untested. Highest risk-per-line-of-test in the
  repo.
- **Web-auth rejection paths** — `web/server.py` at 89.3%; `_has_auth_attempt`'s
  query-string and cookie parsing is uncovered, i.e. the 401-vs-403 decision.
  One parametrized matrix over {absent, malformed, wrong token, right token} ×
  {header, query, cookie} closes most of the module.
- **`team/engine.py`** at 85.9% — parallel-step failure handling, pipeline load
  errors, the SSE error event.
- **Deployment env readers** in `config.py` — the `SAKTHAI_*` overrides the
  systemd units depend on.
- **`guardrails_hardened.py` + `security_hardening.py`** — 371 statements
  imported by nothing but their own tests, padding the denominator.
- **`personas/shared/sakthai/`** — unmeasured by any suite.

---

## Weakest modules

Measured today. **new** marks a module that did not exist at commit `c50d28f`.

| Module | Cover | Miss | Partial | What's uncovered |
|---|---:|---:|---:|---|
| `telegram/bot.py` † | — | — | — | Excluded by `omit`; audit measured 38%. Auth boundary |
| `team/engine.py` | 85.9% | 21 | 15 | Parallel failure handling, pipeline load, SSE error |
| `cli/team.py` | 84.2% | 10 | 0 | Step callbacks, error exit |
| `cli/client.py` **new** | 87.6% | 15 | 3 | Every error branch and interactive prompt |
| `agent/guardrails_hardened.py` | 88.0% | 10 | 8 | Glob DENY, case-trick DENY, hardened `run_command` |
| `client/verifier.py` **new** | 88.3% | 6 | 3 | Per-case exception path, response preview |
| `scripts/verify_hf_upload.py` | 87.6% | 7 | 5 | Network error paths |
| `agent/guardrails.py` | 89.2% | 44 | 36 | Container rules, make recursion, interpreter `-c` |
| `web/server.py` | 89.3% | 15 | 16 | `_has_auth_attempt` query + cookie parsing |
| `client/manager.py` **new** | 89.5% | 6 | 6 | Corrupt config, missing price book, dir override |
| `memory/session_search.py` **new** | 90.9% | 2 | 5 | Skip-and-continue for unreadable session logs |
| `memory/provider.py` | 92.1% | 1 | 2 | Context-window limiting |
| `client/models.py` **new** | 93.4% | 3 | 3 | Optional-field defaults in `from_dict` |
| `cli/system.py` | 93.8% | 16 | 0 | `web setup` / `regen-token` output branches |
| `agent/security_hardening.py` | 94.1% | 14 | 5 | TOCTOU and symlink error paths |
| `config.py` | 95.4% | 10 | 3 | Deployment env readers |
| `agent/tools.py` | 95.7% | 16 | 12 | MS Graph error handling |

† Does not appear in the default report at all.

One structural point in the suite's favour: apart from the deliberately omitted
`telegram/bot.py`, **every file in the package is measured**. There are no dark
modules sitting at 0% — the gaps are shallow-and-wide, which is the cheaper kind
to close.

## Suggested order

1. **Decide what the gate measures** — finding 1. Per-file floor or diff
   coverage. Until this changes every other fix is temporary; the next feature
   merge spends it again.
2. **Backfill the `client/` error paths** — finding 2. Highest coverage-per-test
   in the repo right now, and it is the code that broke the floor. One
   parametrized `CliRunner` table closes most of it.
3. **Resolve the shadowed guardrail rules** — finding 3. A correctness question
   wearing a coverage costume.
4. **Un-omit the Telegram bot and test `_is_authorized`** — finding 6, carried.
   An unasserted allowlist in front of an in-process agent loop.
5. **Write the web-auth rejection matrix** — finding 6, carried. One
   parametrized test.
6. **Wire up or retire `sakthai-chat-cli/`'s suite** — finding 4 — and pin the
   permission-dependent tests — finding 5 — then refresh the `CLAUDE.md` and
   `ci.yml` figures once the real number settles.

## Minor

`[tool.mutmut]` still deselects `tests/test_cli.py::test_serve_dashboard_starts_and_stops_on_interrupt`
and `tests/test_cli.py::test_dashboard_security_handler_sets_headers`; neither
node exists any more, and `test_cli.py` no longer has any `chdir`-ing test for
those entries to protect. Harmless by design — the config's own comment notes a
removed node id degrades to a pytest warning — but it is dead config in a gate
that never runs in CI.

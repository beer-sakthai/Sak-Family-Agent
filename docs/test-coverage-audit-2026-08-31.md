# Test coverage audit — 2026-08-31

Analysis only; no production code changed. Fourth in a series, after
[`2026-08-26`](./test-coverage-audit-2026-08-26.md),
[`2026-08-27`](./test-coverage-audit-2026-08-27.md) and
[`2026-08-28`](./test-coverage-audit-2026-08-28.md), re-measured on
`claude/test-coverage-analysis-97nrce` at `e10b47a` (identical package and test
trees to `main`):

```bash
uv sync --all-extras
uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-report=term-missing
```

Python 3.11, 106 test files, 2,305 passed / 8 skipped, **96.21% branch
coverage** — 191 uncovered statements and 156 partial branches out of 7,710
statements and 2,610 branches.

## Headline: the gate landed and works; the number it reads is not reproducible

| Measure | 26 Aug | 27 Aug | 28 Aug | **31 Aug** |
|---|---:|---:|---:|---:|
| Branch coverage | 96.018% | 95.849% | 95.862% | **96.211%** |
| Uncovered statements | 168 | 213 | 213 | **191** |
| Partial branches | 149 | 170 | 170 | **156** |
| Floor enforced? | no | no | no | **yes** |

`d5fd4d2` closed finding 1 of the 28 Aug audit — `--cov-fail-under=96` is on
`ci.yml`'s pytest step, it was verified to fail in one direction and pass in the
other, and `team/engine.py` went 86% → 99% to clear the floor before the gate
landed. That is the first real movement in the series, and it is the right one:
the debt is now bounded by something other than goodwill.

No package or test file has changed since. Everything below was measured against
that state.

The new finding is that the gate now reads a number that **depends on the home
directory of the machine running it**. The suite writes outside its sandbox
(finding 1), and that is what has been producing the ±1-statement drift all
three previous audits observed and told readers to ignore. With 21 units of
headroom (finding 2), a threshold whose input is not reproducible is a problem
worth fixing before it fires on the wrong commit.

Findings 1, 3, 4, 5 and 6 are new. Finding 7 extends the 28 Aug audit's finding 8
with three tree categories it did not count. Finding 8 carries the rest forward,
re-verified today rather than restated.

---

## 1. The test suite writes real persona memory databases outside its sandbox

**Severity: high** · `tests/conftest.py`, `tests/test_agent_coordinator.py` ·
**new**

`tests/conftest.py` is 27 lines and defines two fixtures, `store` and
`sakthai_home`. **Neither is `autouse`, and there is no autouse fixture
anywhere in the suite.** Isolation is therefore opt-in per test: 22 of 106 test
files mention `SAKTHAI_HOME`, and 4 patch `HOME`.

That is not a hypothetical. Run three test files against a pristine `HOME` and
two real persona shards appear:

```console
$ HOME=$SENTINEL uv run pytest tests/test_memory_merged.py \
      tests/test_agent_coordinator.py tests/test_config_reports.py -q
72 passed
$ find "$SENTINEL/.sakthai"
.sakthai/saksee/memory.db
.sakthai/sakking/memory.db
```

Narrowed to one file, it is `tests/test_agent_coordinator.py`, which calls
`run_persona_task("sakking", …)` and `("saksee", …)` without patching `HOME` or
`SAKTHAI_HOME`. It cannot be fixed by setting `SAKTHAI_HOME`, and that is by
design: `config.persona_memory_db_path()` resolves from `Path.home()`
*deliberately independent of the current process's `SAKTHAI_HOME`* — that
independence is the whole point of the function, and CLAUDE.md documents it. The
consequence is that the one config knob a test would reach for does not contain
it.

Both databases come out schema-migrated and empty (32 KB, `facts` and
`observations` present, 0 rows), so nothing is currently written into them. The
exposure is the path, not today's payload:

- These are exactly the paths a deployed persona uses.
  `infra/vm-agents/sakthai-agent-run.sh` sets
  `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`, so `~/.sakthai/sakking/memory.db` is
  SakKing's live memory on the VM. Running the suite there opens those files and
  runs `_migrate_schema()` (`ALTER TABLE` under `BEGIN IMMEDIATE`) against live
  data, taking a write lock on a production database.
- Migrations are additive by convention, so this does not destroy anything
  today. Nothing enforces that a future test stays read-only, and a test that
  calls a memory-writing tool under `--persona` would insert into a real shard
  with no signal that it had.

**It is also the cause of the flap.** All three previous audits recorded that
back-to-back runs on an identical tree differ by about one uncovered statement
and one partial branch, and none could explain it. Two consecutive runs of
`test_agent_coordinator.py` under the same `HOME`, measuring `memory/store.py`:

| Run | `HOME` state | Missing | Partial | Distinguishing range |
|---|---|---:|---:|---|
| 1 | pristine | 273 | 7 | misses `216-217` |
| 2 | shards from run 1 exist | 274 | 4 | misses `212-214` |

`store.py:211-217` is the fork that creates the DB file with mode `0600` when it
is absent and `chmod`s it when it is present. Whether the suite takes the
create branch or the chmod branch depends on whether `~/.sakthai/<persona>/`
already exists on the machine. That is the whole mystery: not nondeterminism,
just leaked state.

**Proposal**

- An `autouse` fixture in `tests/conftest.py` that points `HOME` (and
  `SAKTHAI_HOME`) at `tmp_path` for every test, with tests that genuinely need
  the real home opting back out explicitly. This is one fixture and it closes
  the escape, the flap, and the class.
- Add a guard test that fails if a run creates anything under the invoking
  user's `~/.sakthai` — the cheapest way to keep it closed.
- Fix `tests/test_agent_coordinator.py` regardless; it is the only current
  offender and a two-line change.

The flap was previously judged harmless because 0.21pp of headroom is ten times
0.02pp. That reasoning holds for the size of the drift. It does not cover a
suite that writes to production paths.

---

## 2. The floor is real now — and it is one feature away from firing

**Severity: high** · `.github/workflows/ci.yml` · *extends 2026-08-28 finding 1,
proposal 3*

Headroom, in units of statement-or-branch:

```
covered            9,929
minimum for 96%    9,908
headroom              21
```

21 units. For scale, the `client/` subsystem — the most recent feature of any
size, merged 27 Aug in #1198 — is 427 units at 89.9%, i.e. **43 uncovered
units, double the entire headroom of the repository.** Had the gate been live a
day earlier, that PR could not have merged without either tests it did not have
or a compensating surplus somewhere else. That is the gate working as intended,
and it is also the argument for the per-file floor the 28 Aug audit proposed and
nobody has added: a package-wide average lets a module land at 88% as long as
someone else banked the difference, and then bills the next contributor for it.

One number is worth having before that debate: **deleting the two dead hardened
modules moves coverage in the helpful direction.**

| | denominator | covered | coverage | headroom |
|---|---:|---:|---:|---:|
| today | 10,320 | 9,929 | 96.21% | 21 |
| without `security_hardening.py` + `guardrails_hardened.py` | 9,817 | 9,467 | **96.43%** | **42** |

So the open decision in finding 5 of the 28 Aug audit — wire the hardened layer
in or delete it — is not blocked on coverage risk in the delete direction. It
doubles the headroom and removes 503 units of denominator that no production
code executes.

**Proposal**

- Add diff coverage (or a per-file floor) so a new module cannot land far under
  the package average by spending headroom the rest of the package built.
- Treat 21 units as the working budget until then, and say so where contributors
  will see it.

---

## 3. The integration tier is structurally incapable of failing

**Severity: medium** · `tests/test_integration.py` · **new**

The 28 Aug audit found six tests with no assertion, all in the hardened modules.
An AST pass over all 1,899 `def test_*` today reproduces that set exactly — six
real tests plus the `test_tool` fixture pytest does not collect, unchanged. The
suite's assertion hygiene is genuinely good.

There is a second can't-fail pattern it did not look for. Every live-provider
smoke test in `tests/test_integration.py` wraps its only meaningful call like
this:

```python
try:
    result = run_agent("Reply with exactly the single word: pong", …)
except Exception as exc:
    pytest.skip(f"Gemini execution failed (e.g. model unavailable or quota): {exc}")
assert result.text.strip()
```

The same shape guards the Gemini, gateway, OpenAI-compatible and Ollama cases.
The intent is right — these are `@pytest.mark.integration` tests that must not
break CI when a quota runs out — but the `except Exception` is unscoped, so a
genuine regression anywhere in the provider stack (a malformed request body, a
broken auth chain, a serialization error in `providers/base.py`) reports as
*skipped*, and the assertion below it is unreachable. These four tests are the
repository's only end-to-end verification that a provider actually works, and
none of them can report a failure.

**Proposal** — keep the skip, narrow what earns it. Skip on the errors that mean
"the environment is not available" (auth, quota, connection, timeout) and let
everything else fail. `AuthError` and `httpx.ConnectError` are skippable; a
`KeyError` in the response parser is the bug these tests exist to catch.

---

## 4. Every exception handler in the operator-facing CLI is untested

**Severity: medium** · `cli/client.py`, `cli/system.py`, `client/` ·
**new measurement**, sharpening 2026-08-28 finding 9

Cross-referencing every `ast.ExceptHandler` in the package against the coverage
report: **30 of 168 exception handlers (18%) have a body no test ever enters.**
They are not spread evenly.

| Module | Untested / total handlers |
|---|---:|
| `agent/security_hardening.py` | 7 / 9 |
| `agent/guardrails.py` | 5 / 6 |
| `agent/tools.py` | 4 / 21 |
| **`cli/client.py`** | **4 / 4** |
| **`cli/system.py`** | **4 / 4** |
| `cli/extensions.py` | 1 / 2 |
| `cli/team.py` | 1 / 2 |
| **`client/manager.py`** | **1 / 1** |
| **`client/verifier.py`** | **1 / 1** |
| `memory/sync.py` | 1 / 4 |
| `scripts/verify_hf_upload.py` | 1 / 2 |

The bolded rows are the whole of the error handling in the client provisioning
path and the system CLI — every `except` an operator reaches on a first bad
invocation. `cli/client.py`'s uncovered lines are precisely its five
`except`/`sys.exit(1)` pairs (`72-74`, `137-139`, `154-156`, `190-192`, `227`),
and `tests/test_cli_client.py` has four tests, all happy path: list-empty,
list-and-show, onboard, test.

This is the same finding the 28 Aug audit filed under "still open", but stated as
a property rather than a line range it is easier to act on and harder to
half-close: *no exception handler in `cli/` or `client/` has ever run.*

**Proposal** — one `CliRunner` table per group, parametrized over the failure
modes, asserting exit code **and** message. The handlers are the cheapest
coverage in the package and the highest-traffic code an operator meets.

---

## 5. The dashboard's cross-package contract is pinned by nothing on either side

**Severity: medium** · `web/api.py`, `apps/agent_workflow_framework` · **new**

`web/api.py` says what it is doing, plainly:

```python
"""Workflow run summaries, newest first.

Reads the JSON files ``agent_workflow.persistence.RunHistoryStore`` writes.
The framework is not imported: it is a separate package outside
this one's dependency graph, and its on-disk format is the contract.
"""
```

An on-disk format is a fine contract. This one has no test on either side of it.
`workflows_payload()` and `workflow_detail()` read eleven keys —
`run_id`, `workflow_name`, `status`, `start_time`, `end_time`, `step_results`,
and per step `step_id`, `status`, `attempts`, `error`, `start_time`, `end_time` —
and `agent_workflow.models` emits them from `RunHistory.to_dict()` and
`StepResult.to_dict()`. I checked all eleven: **they match today**, including
the reader's assumption that `RunStatus`/`StepStatus` serialise uppercase (they
do — `PENDING`/`RUNNING`/`COMPLETED`/`FAILED`, lowercased on read). The two
`run_id` validators also agree: `_SESSION_ID_RE` is `^[A-Za-z0-9_.-]+$` and
`RunHistoryStore._sanitize_run_id` uses the same character class.

The problem is what happens when they stop matching. Every field is read with a
`.get(name, default)`, so a rename on the writer's side does not raise — it
yields `workflow_name: ""`, `status: ""`, `step_count: 0`, `attempts: 0`, and
the dashboard renders a run that looks empty rather than broken. `apps.yml` runs
the framework's 7 test files and measures no coverage; `ci.yml` never sees them.
Neither suite would notice.

**Proposal** — a golden fixture. Have the framework's tests write a real
`RunHistory` through `RunHistoryStore` and commit the resulting JSON; have
`tests/test_web_api.py` read that exact file and assert the parsed payload. One
fixture, asserted from both ends, and a rename fails on the side that made it.
This is cheaper than importing the framework and keeps the boundary the docstring
describes.

---

## 6. The guardrails are tested by enumeration, in the one place enumeration cannot win

**Severity: medium** · `agent/guardrails.py`, `tests/test_guardrails_*.py` ·
**new**

`agent/guardrails.py` is the largest and most-attacked module in the package
(514 statements, 392 branches, 98 uncovered units — the biggest absolute hole in
the repo by more than double). It is covered by roughly 15 test files containing,
almost entirely, hand-written attack strings: `test_sentinel_ssh_leak.py` and
`test_guardrails_sentinel_bypasses.py` alone are ~600 lines of literal commands.
Each was added after a specific bypass was found, which is the honest and correct
response to each individual finding, and cumulatively it is a strategy that only
ever covers the attacks someone already thought of.

Meanwhile `hypothesis` is a declared dev dependency used by **exactly one test
file** (`test_store_properties.py`, against `MemoryStore`).

`_is_sensitive_path(path: str, allow_local: bool = False) -> bool` is a pure
function from a string to a bool with no I/O — close to the ideal property-test
target, and it sits directly on the security boundary. The invariants it is
*supposed* to hold are exactly the ones each historical bypass violated:

- **Case**: if `p` is denied, `p.upper()`/`p.lower()`/mixed case is denied.
- **Decoration**: if `p` is denied, so are `"p"`, `'p'`, `  p  `, `--file=p`,
  `field=@p`, `FILE:p`, and `p` as one element of a comma-joined list.
- **Separators**: `/`- and `\`-separated forms agree.
- **Prefixing**: if `p` is denied, `./p` and `dir/p` are denied.
- **No false positives**: a generated path built only from benign components is
  allowed.

Each of those is a property that generalises a whole family of past Sentinel
findings, and hypothesis will explore the family rather than the six members
someone enumerated.

**Proposal** — one `tests/test_guardrails_properties.py` with those five
invariants, seeded from the existing `_SENSITIVE_BASENAMES` / `_SENSITIVE_DIRS`
tables so it tracks the module rather than a copy of it. Keep every existing
example test; they are the regression record. This adds the axis they cannot
cover.

---

## 7. Unrun Python test files now outnumber run ones

**Severity: medium** · *extends 2026-08-28 finding 8 with three categories it did
not count*

| Tree | Files | Run by |
|---|---:|---|
| `tests/` | 106 | `ci.yml` |
| `apps/agent_workflow_framework/tests/` | 7 | `apps.yml` (no coverage measured) |
| `apps/sak_agent_dashboard` (TypeScript) | 14 | `apps.yml` |
| `personas/sakthai/agent-self-evolution/tests/` | 8 | `agent-self-evolution.yml` |
| `sakthai-chat-cli/` | 86 | **nothing** |
| `personas/*/skills/**` (comfyui ×2 copies, asset-monitor) | 11 | **nothing** |
| `personas/shared/agent-self-evolution/tests/` | 8 | **nothing** |
| `services/teams-copilot-mcp/tests/` | 3 | **nothing** |

**108 unrun Python test files against 106 that run.** Three categories are new
here:

- **`personas/shared/agent-self-evolution/tests/`** — `agent-self-evolution.yml`
  is paths-filtered to `personas/sakthai/agent-self-evolution/**`, so only
  SakThai's copy is tested. The shared copy, which the other five personas
  symlink to, is not. It is byte-identical today (`diff -rq` is clean), so this
  is duplication rather than divergence — but it is duplication of the exact kind
  the guardrails parity test exists to catch, with nothing catching it.
- **11 test files shipped inside skill directories** —
  `SakKing-comfyui/tests/` and `SakSee-comfyui/tests/` (5 each, identical
  copies) and `SakJules-asset-monitor/`. No workflow references them.
- **A divergent duplicate** —
  `personas/sakthai/skills/SakThai-sakthai-mlops-hf-train-manual-upload/test_verify_hf_upload.py`
  and `tests/test_verify_hf_upload.py` differ. The one in `tests/` runs; the one
  beside the code it tests does not.

**Proposal** — unchanged from the 28 Aug audit and now larger: a paths-filtered
job per tree on the `apps.yml` pattern, or an explicit note in each tree that it
is archived. For the two exact duplicates (`shared/agent-self-evolution`, the
comfyui pair), widening an existing workflow's path filter is cheaper than a new
job.

---

## 8. Carried forward — re-verified today, all unchanged

Each of these was re-measured at `e10b47a`, not restated:

- **The nine deployment env vars still have zero test references.**
  `config.py`'s uncovered statements are `296-297, 302-303, 308, 313, 332-333` —
  the first line of `sakthai_default_provider`, `sakthai_default_model`,
  `sakthai_fast_mode`, `sakthai_skip_mcp` and `sakthai_with_skills`, and nothing
  else. Still the cheapest ten statements in the repo, still the surface every
  deployed persona boots through. *(28 Aug finding 2.)*
- **Web auth: one of three credential channels is exercised.**
  `web/server.py` misses `213-217` and `220-224` — the query-parameter and cookie
  loops in `_has_auth_attempt`, with the matching partials in
  `_is_authenticated`. *(28 Aug finding 3.)*
- **`web/server.py` parity is still unpinned.** The file is byte-identical
  across `shared`, `sakking`, `saksee` and `saksit` (`9b325976…`) and differs in
  the canonical copy only by the SakThai-only dashboard routes. AST-extracting
  `_get_or_create_bearer_token`, `_is_authenticated` and `_has_auth_attempt`
  from all five and hashing them gives one value, `442c8064…`, across every
  copy — so the auth surface is sound today and the parity test the audit asked
  for is about fifteen lines. Nothing keeps it that way in the meantime.
  *(28 Aug finding 4.)*
- **The hardened layer is still dead code with can't-fail tests.** No production
  importer; the six assertion-free tests are exactly the ones named on the 28th.
  See finding 2 above for the number that should unblock the decision.
  *(28 Aug finding 5.)*
- **`guardrails.py` section 6 is still unreachable.** Uncovered:
  `866, 872, 877-879, 884-886, 888-891, 895-898, 906-910` — the container-mount
  block, entire. *(28 Aug finding 6.)*
- **`make mutation` still cannot fail.** `mutmut run || true`, in no workflow,
  and `[tool.mutmut]`'s `pytest_add_cli_args_test_selection` still deselects
  `test_serve_dashboard_starts_and_stops_on_interrupt` and
  `test_dashboard_security_handler_sets_headers`, neither of which exists.
  *(28 Aug finding 7.)*
- **`telegram/bot.py` is still omitted from coverage and `_is_authorized` is
  still untested.** It guards eight handlers; `tests/test_telegram_bot.py` has
  four tests, none of which call it, though all four already set
  `TELEGRAM_ALLOWED_USER_IDS`, so the fixture work is done. The control is
  correct today — `telegram_allowed_user_ids()` returns `[]` for unset, blank
  and unparseable values, so it fails closed — and that reader *is* tested in
  `test_config_reports.py`. What is untested is the guard itself: that a
  non-allowed user calling `/workflow` is refused before `run_agent()` runs.
  *(28 Aug finding 9.)*
- **`team/engine.py` is closed.** 86% → 99% in `d5fd4d2`; it is no longer among
  the weakest modules. `cli/team.py` remains at 84.2% (uncovered: `125-127`,
  `136-137`, `142-144`, `148-149`).

---

## Weakest modules, 2026-08-31

By percentage:

| Module | Cover | Miss | Partial | Stmts | Branches |
|---|---:|---:|---:|---:|---:|
| `cli/team.py` | 84.2% | 10 | 0 | 83 | 18 |
| `cli/client.py` | 87.6% | 15 | 3 | 123 | 22 |
| `scripts/verify_hf_upload.py` | 87.6% | 7 | 5 | 69 | 28 |
| `agent/guardrails_hardened.py` | 88.0% | 10 | 8 | 123 | 60 |
| `client/verifier.py` | 88.3% | 6 | 3 | 61 | 16 |
| `agent/guardrails.py` | 89.2% | 44 | 36 | 514 | 392 |
| `web/server.py` | 89.3% | 15 | 16 | 288 | 114 |
| `client/manager.py` | 90.8% | 5 | 5 | 93 | 16 |
| `memory/session_search.py` | 90.9% | 2 | 5 | 57 | 20 |
| `memory/provider.py` | 92.1% | 1 | 2 | 32 | 6 |
| `client/models.py` | 93.4% | 3 | 3 | 81 | 10 |
| `cli/system.py` | 93.8% | 16 | 0 | 200 | 56 |
| `agent/security_hardening.py` | 94.1% | 14 | 5 | 248 | 72 |
| `agent/coordinator.py` | 95.3% | 2 | 2 | 71 | 14 |
| `config.py` | 95.5% | 10 | 3 | 232 | 58 |
| `agent/tools.py` | 95.7% | 16 | 12 | 520 | 172 |

By absolute size of hole, which is what the package average actually responds to:

| Module | Uncovered units | Cover |
|---|---:|---:|
| `agent/guardrails.py` | 98 | 89.2% |
| `web/server.py` | 43 | 89.3% |
| `agent/tools.py` | 30 | 95.7% |
| `agent/guardrails_hardened.py` | 22 | 88.0% |
| `agent/security_hardening.py` | 19 | 94.1% |
| `cli/client.py` | 18 | 87.6% |
| `cli/team.py` | 16 | 84.2% |
| `cli/system.py` | 16 | 93.8% |
| `config.py` | 13 | 95.5% |

`telegram/bot.py` remains excluded by `[tool.coverage.run] omit`; every other
file in the package is measured.

---

## Suggested order

1. **Stop the suite writing to `~/.sakthai`** (finding 1). One autouse fixture.
   It closes a write path into live persona databases and makes the gate's input
   reproducible — and the gate is now real, so that matters in a way it did not
   a week ago.
2. **Test the deployment env readers** (finding 8, carried from 28 Aug finding
   2). Ten statements, ~30 lines, still unwritten after three audits asked.
3. **Narrow the integration-tier `except`** (finding 3). Four tests, one
   exception tuple, and the provider smoke tests can fail again.
4. **Cover the `cli/` and `client/` exception handlers** (finding 4). Eleven
   handlers that have never run, in the code an operator hits first.
5. **Write the web-auth matrix and pin the auth block across personas**
   (finding 8, carried from 28 Aug findings 3 and 4). The AST-hash mechanism is
   demonstrated above; the test is about fifteen lines.
6. **Decide the hardened layer's fate** (finding 8, carried from 28 Aug finding
   5), knowing that deleting it takes coverage to 96.43% and headroom to 42.
7. **Add the workflow-contract golden fixture** (finding 5) and **the guardrails
   property tests** (finding 6).
8. **Add diff coverage or a per-file floor** (finding 2), then **wire up or
   retire the unrun trees** (finding 7) and **give mutation a schedule**
   (finding 8, carried from 28 Aug finding 7).

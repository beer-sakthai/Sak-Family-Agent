# Test coverage audit — 2026-08-28

Analysis only; no production code changed. Third in a series, after
[`2026-08-26`](./test-coverage-audit-2026-08-26.md) and
[`2026-08-27`](./test-coverage-audit-2026-08-27.md), re-measured on `main` at
`1ebe527` with the same command both used:

```bash
uv sync --all-extras
uv run pytest tests/ -m "not integration" --cov=sakthai --cov-branch --cov-report=term-missing
```

Python 3.11.15, 106 test files (26,874 lines of test against 17,128 lines of
package).

## Headline: 76 commits, zero movement

| Measure | 26 Aug | 27 Aug | **28 Aug** |
|---|---:|---:|---:|
| Branch coverage | 96.018% | 95.849% | **95.862%** |
| Uncovered statements | 168 | 213 | **213** |
| Partial branches | 149 | 170 | **170** |
| Measured statements | — | 7,688 | **7,708** |

`main` took 76 commits in 24 hours and the miss/partial counts did not move by
one. Every one of those commits landed in `apps/`, docs, or workflow config;
`git log a704a40..HEAD -- personas/sakthai/sakthai tests/` touches exactly seven
files (`memory/merged.py`, `web/api.py`, `web/server.py` and their tests, plus
`test_soul_consistency.py`), and all of it arrived covered — the +20 statements
cost nothing.

So the debt is frozen exactly where the 27 Aug audit left it. That is the finding
that matters, and finding 1 is why: **there is still no automated signal on
coverage at all**, so nothing pushes back.

Findings 2, 4, 5 and 7 are new. Findings 3, 6, 8 and 9 are carried and are
sharpened here from inference into proof.

---

## 1. The coverage gate: the diagnosis is settled, the fix is not applied

**Severity: high** · `.github/workflows/ci.yml`, `pyproject.toml` · *carried from
2026-08-27, with the open question closed*

Yesterday's audit left the mechanism "deliberately unidentified" and floated
pytest-subtests as a candidate. Two things close that out:

- **The pytest-subtests hypothesis is dead.** It is not a dependency and not
  installed (`pyproject.toml` declares only pytest, pytest-asyncio, pytest-cov).
  The "124 subtests passed" line in CI is `unittest`'s own `subTest`, used by
  `tests/test_persona_guardrails_parity.py` — pytest 9 reports those natively.
  No third-party plugin is involved.
- **The fix is already known and simply was not made.** `PLAN.md`'s
  2026-08-28 freshness-audit row records it: *"Not done: adding
  `--cov-fail-under=96` to `ci.yml` so the floor actually gates the build — the
  edit was blocked by this session's permission classifier, and it is the one
  change that would turn `main` red until the 0.15pp gap closes."*

So this is not an open investigation. It is a one-line edit that nobody has
landed, and until it lands every other finding in this document — and in the two
before it — is a suggestion rather than a constraint.

There is a second weakness in the same gate, independent of whether it fires:
`fail_under` is a package-wide average over 7,708 statements. A module landing at
86% fails nothing; it spends headroom the rest of the package built. Findings 2
through 9 are all instances of that.

**Proposal**

1. `run: uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/`
   in `ci.yml`, rather than relying on `[tool.coverage.report] fail_under`.
2. Prove it fails — push a branch that trips it and watch the job go red. A gate
   nobody has seen fail is not known to work. Right now that is `main` itself, at
   95.862%, which is the point: land the gate together with finding 2's tests,
   which are enough to clear it.
3. Add a per-file floor or diff coverage so new code cannot land far under the
   package average unnoticed.

---

## 2. The deployment configuration surface is the least-tested code in the package

**Severity: high** · `config.py:280-320` · **new**

Cross-referencing every environment variable the package reads against every
variable any test file mentions turns up **nine with zero test references**:

| Variable | Read by | Test files mentioning it |
|---|---|---:|
| `SAKTHAI_FAST` | `config.sakthai_fast_mode()` | 0 |
| `SAKTHAI_NO_MCP` | `config.sakthai_skip_mcp()` | 0 |
| `SAKTHAI_WITH_SKILLS` | `config.sakthai_with_skills()` | 0 |
| `SAKTHAI_MODEL` | `config.sakthai_default_model()` | 0 |
| `SAKTHAI_PROVIDER`¹ | `config.sakthai_default_provider()` | 0 |
| `SAKTHAI_STATELESS` | `telegram/bot.py:129` | 0 |
| `SAKTHAI_EVAL_LOG` | `config.eval_log_path()` | 0 |
| `SAKTHAI_DEFAULT_MODEL` / `SAKTHAI_DEFAULT_PROVIDER` | `client/manager.py:89-90` | 0 |
| `MS_GRAPH_TENANT_ID` | `agent/tools.py` Graph helpers | 0 |

¹ the string `SAKTHAI_PROVIDER` appears in one test file, but not as an
environment the reader is exercised against.

Coverage agrees independently: `config.py`'s uncovered statements are
`282-283, 288-289, 294, 299, 318-319` — precisely those five reader functions and
nothing else.

This is not obscure code. `infra/vm-agents/env-templates/*.env.example` sets
`SAKTHAI_FAST`, `SAKTHAI_MODEL`, `SAKTHAI_PROVIDER` and `SAKTHAI_WITH_SKILLS`;
they are how each deployed persona is configured. `sakthai_fast_mode()` decides
whether a persona runs the six-stage cycle or fast-tracks. `sakthai_with_skills()`
decides which skills reach the system prompt — and it does something
non-obvious, `raw.replace(",", " ").split()`, so it accepts both comma and
space separation. Nothing asserts that.

**Proposal** — the cheapest 10 statements in the repo. One parametrized file,
roughly 30 lines:

- The three boolean readers over `{"1", "true", "TRUE", "yes", "on", " on ",
  "0", "false", "", unset}` — the truthy set is `{1,true,yes,on}` after
  `.strip().lower()`, and every other value must be false. A deployment that
  writes `SAKTHAI_FAST=True` and one that writes `SAKTHAI_FAST=enabled` get
  opposite behaviour and neither is currently pinned.
- `sakthai_with_skills()` over `"a,b"`, `"a b"`, `"a, b"`, `" "`, unset —
  asserting the empty cases yield `[]` rather than `[""]`.
- `sakthai_default_model()` / `_provider()` for the blank-string-is-None case,
  which is what distinguishes "unset" from "set to empty" in a systemd unit file.
- `eval_log_path()` honouring `SAKTHAI_EVAL_LOG` and falling back to
  `SAKTHAI_HOME/eval.jsonl`.

---

## 3. Web auth: one of three credential channels is tested

**Severity: high** · `web/server.py` · 89.3% · 15 miss / 16 partial ·
*carried from 2026-08-26, sharpened*

`_is_authenticated()` accepts a token three ways — `Authorization: Bearer`, a
`token`/`bearer_token` query parameter, and a `token`/`bearer_token` cookie —
and `_has_auth_attempt()` mirrors all three to decide 401 versus 403. That is six
code paths guarding every endpoint except `/health`.

`tests/test_web_auth.py` has seven tests. Four exercise the HTTP boundary, all
four through the header: no token (401), malformed (401), wrong token (403),
correct token (200). **The query-string and cookie channels — two complete ways
to obtain an authenticated session — are never exercised.** The uncovered ranges
say so precisely: `213-217`, `220-224` (the two loops in `_has_auth_attempt`) and
the `243->252, 244->243, 246->243, 248->243, 254->262, 255->254, 257->254,
259->254` partials (the two loops in `_is_authenticated`).

Untested there: the `unquote()` applied before `secrets.compare_digest`, and an
asymmetry worth a test on its own — the cookie loop calls `.strip()` on the item
before splitting, the query loop does not. Nothing would notice if one of those
lost its `compare_digest` and became `==`.

**Proposal** — one parametrized matrix, `{absent, malformed, wrong, correct} ×
{header, query, cookie}`, asserting the status code for each of the twelve. That
closes most of the module in one test function. Worth also asserting that a
percent-encoded token authenticates and that a token in the query string is
accepted only where the team intends it to be — a credential in a URL lands in
access logs and `Referer` headers, and the tests are the only place that
intention is currently recorded.

---

## 4. The persona parity test pins one file; the other security-critical file drifts unpinned

**Severity: high** · `tests/test_persona_guardrails_parity.py` · **new**

`agent/guardrails.py` is copied into five persona trees and
`test_persona_guardrails_parity.py` fails CI the moment any copy drifts. That
test exists because unsynced security fixes are this repo's known failure mode —
`PLAN.md` records several rounds of it.

`web/server.py` has exactly the same property and no such test:

```
d082f325…  personas/shared/sakthai/web/server.py     ← what sakjules, saktan,
d082f325…  personas/sakking/sakthai/web/server.py       sakking, saksee, saksit
d082f325…  personas/saksee/sakthai/web/server.py        actually run
d082f325…  personas/saksit/sakthai/web/server.py
6fc73ab3…  personas/sakthai/sakthai/web/server.py   ← the only one any test imports
```

It holds the bearer-token auth from finding 3, and it took two code-scanning
autofixes this week (#1214, #1219, cookie construction from user-supplied
input) — the class of fix that must not land in one copy only. The 155-line delta
between the shared and canonical copies is the SakThai-only dashboard routes, and
the auth block itself is currently byte-identical across all five, so there is no
live vulnerability here. The gap is that **nothing keeps it that way**, and the
suite imports `sakthai.web.server`, which resolves only to the canonical copy.

`memory/merged.py` has already drifted between the two copies since yesterday,
and `memory/session_search.py` exists only in the canonical tree — so drift is
happening now, in files nobody diffs.

**Proposal**

- Generalise the parity test from one hard-coded path to a list, and add
  `web/server.py`'s auth block to it. A whole-file pin is wrong here (the
  canonical copy legitimately carries extra routes), so pin the security surface:
  assert `_get_or_create_bearer_token`, `_is_authenticated` and
  `_has_auth_attempt` are byte-identical across every copy that has the file.
- Better still, make the finding-3 matrix run against each persona's copy by
  path, so the auth tests cover what five personas actually execute rather than
  the one copy `import sakthai` happens to resolve to.

---

## 5. The hardened security modules are dead code, and their tests cannot fail

**Severity: high** · `agent/security_hardening.py` (248 stmts, 94.1%),
`agent/guardrails_hardened.py` (123 stmts, 88.0%) · *carried from 2026-08-26,
now with the test-quality half*

Grepping every importer of these two modules across the package, `tests/` and
`scripts/` returns test files and nothing else. No production caller: not
`agent/loop.py`, not `cli/`, not `mcp/`. `DEFAULT_POLICY` from the base
`guardrails.py` is what actually runs. 371 statements of "defense in depth" ship,
never execute, and contribute 4.8% of the coverage denominator.

The new half is what is holding them up there. An AST pass over every `def
test_*` in `tests/` — 1,886 of them — finds only six with no assertion of any
kind (a seventh hit is a fixture named `test_tool`, which pytest does not
collect). The suite's assertion hygiene is genuinely good, which is why its
coverage number is more trustworthy than most. But **four of those six** are in
exactly these two modules' tests:

```python
def test_initialize_with_balanced_level(self) -> None:
    initialize_hardened_guardrails(security_level=SecurityLevel.BALANCED)
    # Should not raise any exception
```

…repeated verbatim for `STRICT` and `PERMISSIVE`. Three tests, three security
levels, and nothing distinguishes them: they pass whether the levels differ or
are all aliases for the same policy. And:

```python
def test_detects_dangerous_symlinks(self, tmp_path: Path) -> None:
    symlink.symlink_to("/root")
    SymlinkDetector.detect_dangerous_symlinks(str(symlink))   # return discarded
    except (OSError, PermissionError):
        pass
```

The return value is dropped and the exception swallowed. That test passes if the
detector returns `True`, returns `False`, or does nothing at all.

**Proposal** — a decision before tests, and the decision is the cheaper half:

- If the hardened layer is meant to run, wire it in and let the existing tests
  become meaningful. If it is not, delete it. Either way 371 statements stop
  distorting the package average and the *base* guardrails' 44 uncovered
  statements (finding 6) become the number everyone is looking at, which is the
  one that matters.
- Whichever way it goes, replace the four can't-fail tests. For the security
  levels: assert the resulting policy actually denies something under `STRICT`
  that it allows under `PERMISSIVE`. For the symlink detector: assert on its
  return value, and build the "critical directory" case from `tmp_path` with a
  patched critical-root set rather than from the real `/root`, so the assertion
  does not depend on the invoking user's filesystem permissions.

---

## 6. `guardrails.py` section 6 is unreachable — now proven, not inferred

**Severity: medium (as a coverage item); high as a correctness item** ·
`agent/guardrails.py` · 89.2% · 44 miss / 36 partial · *carried from 2026-08-26,
upgraded to a measurement*

Both previous audits inferred that the container rules at lines 866–910 never
execute because `_check_destructive_tokens` denies first. That is now
demonstrated. Every form the block exists to catch, run through `DEFAULT_POLICY`:

| Command | Verdict | Reason string |
|---|---|---|
| `docker run -v /etc:/mnt busybox` | DENY | *destructive* `'docker'` command on `'/etc:/mnt'` |
| `docker run -v=/etc:/mnt busybox` | DENY | *destructive* `'docker'` command on `'-v=/etc:/mnt'` |
| `docker run --volume=/etc/shadow:/mnt busybox` | DENY | *destructive* `'docker'` command on `'--volume=/etc/shadow:/mnt'` |
| `docker run --mount type=bind,source=/etc,… ` | DENY | *destructive* `'docker'` command on `'type=bind,source=/etc,…'` |
| `docker run --mount type=bind,src=/root/.ssh,…` | DENY | *destructive* `'docker'` command on `'type=bind,src=/root/.ssh,…'` |
| `docker cp web:/tmp/x /etc/passwd` | DENY | *destructive* `'docker'` command on `'web:/tmp/x'` |
| `podman run -v /root/.ssh:/mnt alpine` | DENY | *destructive* `'podman'` command on `'/root/.ssh:/mnt'` |
| `kubectl cp pod:/x ~/.ssh/id_rsa` | DENY | *destructive* `'kubectl'` command on `'~/.ssh/id_rsa'` |

All eight are denied — the control works — but every reason string comes from the
generic argument scanner at line ~667, which lists `docker`/`podman`/`kubectl`
among its binaries. Not one comes from section 6, whose messages read
`volume mount targeting`, `mount source` or `'docker cp' on`. Section 6 is
unreachable code, and the ~50 uncovered statements there are not a testing gap.

Note also that the generic rule is coarser than it looks: `docker run -v
/tmp/data:/mnt busybox` is denied too, on a benign mount, while `docker ps`,
`kubectl get pods` and `docker logs web` are allowed.

**Proposal**

- Delete section 6 and keep a regression test asserting each of the eight forms
  above is denied — the behaviour is preserved, the dead branch goes, and 50
  statements leave the denominator honestly.
- Or, if the specific messages are wanted (they are better diagnostics), move
  section 6 ahead of `_check_destructive_tokens` for these three binaries; then it
  is reachable and the same eight-case test covers it.
- Either way this is one change to the canonical file, propagated by the parity
  test to five personas.
- The rest of `guardrails.py`'s uncovered set is *not* unreachable and deserves
  tests on its own: the `make` recipe recursion (368–375, 437–447), the nested
  shell `-c` walk-back (461), interpreter `-c` detection (513), and `dd if=`/`of=`
  (776). Those are bypass-prevention branches — an untested branch there is an
  unverified security control.

---

## 7. Nothing in CI measures whether the tests assert anything

**Severity: medium** · `Makefile`, `pyproject.toml` · **new**

`[tool.mutmut]` names nine core seam modules and `make mutation` runs them. It
cannot fail:

```make
mutation:
	@uv run --extra dev --extra mutation mutmut run || true
	@uv run --extra mutation mutmut results
```

`|| true` swallows the exit code, and no workflow invokes the target. Combined
with finding 1, the repository currently has **no enforced signal on test
quantity and none on test quality**. Finding 5's four can't-fail tests are what
that absence looks like in practice.

**Proposal** — do not put mutmut in the PR path; it is far too slow. Run it on a
schedule (`continuous-security.yml` already runs nightly) over the two modules
where a surviving mutant is a security bug rather than a style question —
`agent/guardrails.py` and `web/server.py` — and fail on a survivor count above a
committed baseline. Drop the `|| true` so the local target reports honestly.

Also dead config in the same block: `[tool.mutmut]`'s
`pytest_add_cli_args_test_selection` still deselects
`test_serve_dashboard_starts_and_stops_on_interrupt` and
`test_dashboard_security_handler_sets_headers`; neither node exists.

---

## 8. Three test trees, two of which no workflow runs

**Severity: medium** · `sakthai-chat-cli/`, `services/teams-copilot-mcp/` ·
*carried and extended*

| Tree | Python test files | Run by |
|---|---:|---|
| `tests/` | 106 | `ci.yml` |
| `apps/agent_workflow_framework/tests/` | 7 | `apps.yml` (no coverage measured) |
| `apps/sak_agent_dashboard` (TS) | 14 | `apps.yml` |
| `sakthai-chat-cli/` | **86** | nothing — only `bandit.yml`/`codeql.yml` scan it |
| `services/teams-copilot-mcp/tests/` | **3** | nothing — only `bandit.yml` scans it |

The chat-CLI tree has grown from the 72 files the 27 Aug audit counted to 86, so
it is being actively written to while remaining unexecuted. `services/` is a
tree the previous audit missed entirely.

**Proposal** — `apps.yml` is the pattern: a paths-filtered job per tree. Either
add one for each, or state in `sakthai-chat-cli/MIGRATION_NOTE.md` that the tree
is archived and its suite unmaintained. Both are defensible; writing tests that
nothing runs is not. Expect breakage on the first run — `CLAUDE.md` notes that
tree's docs still describe a five-persona roster.

---

## 9. Still open, unchanged

Re-verified today at `1ebe527`, all as the 27 Aug audit left them:

- **`telegram/bot.py`** — omitted from coverage entirely, so it does not appear
  in the report at all. `_is_authorized()` is the only barrier between an
  arbitrary Telegram user and an in-process `run_agent()` call; it guards eight
  handlers; `tests/test_telegram_bot.py` has four tests and none of them touch
  it. Highest risk-per-line-of-test in the repo, and un-omitting the file is a
  one-line change.
- **`client/` and `cli/client.py`** (87.6% / 88.3% / 89.5% / 93.4%, 45 uncovered
  units) — every `except`/`sys.exit(1)` pair, the interactive `click.prompt`
  fallbacks, the malformed `--allowed-users` parse, the corrupt-`client.json`
  warning path, and the missing-price-book branch. The paths an operator hits on
  a first bad invocation. One `CliRunner` table over those failure modes,
  asserting exit code *and* message, closes most of it.
- **`team/engine.py`** (85.9%, 21 miss / 15 partial, the largest gap after
  guardrails) and `cli/team.py` (84.2%) — parallel-step failure handling
  (`259-277`), pipeline load errors, the SSE error event.
- **Permission-dependent tests** — `test_security_hardening.py:635` and
  `test_guardrails_hardened.py:419` self-skip when `chmod` cannot restrict the
  invoking user, so the measured total differs between a root run and an
  unprivileged one. Small, but once finding 1's gate is live, a threshold whose
  outcome depends on who invoked it is not a threshold.

---

## Weakest modules, 2026-08-28

| Module | Cover | Miss | Partial | Stmts |
|---|---:|---:|---:|---:|
| `telegram/bot.py` † | — | — | — | — |
| `cli/team.py` | 84.2% | 10 | 0 | 83 |
| `team/engine.py` | 85.9% | 21 | 15 | 188 |
| `cli/client.py` | 87.6% | 15 | 3 | 123 |
| `scripts/verify_hf_upload.py` | 87.6% | 7 | 5 | 69 |
| `agent/guardrails_hardened.py` | 88.0% | 10 | 8 | 123 |
| `client/verifier.py` | 88.3% | 6 | 3 | 61 |
| `agent/guardrails.py` | 89.2% | 44 | 36 | 514 |
| `web/server.py` | 89.3% | 15 | 16 | 288 |
| `client/manager.py` | 89.5% | 6 | 6 | 96 |
| `memory/session_search.py` | 90.9% | 2 | 5 | 57 |
| `memory/provider.py` | 92.1% | 1 | 2 | 32 |
| `client/models.py` | 93.4% | 3 | 3 | 81 |
| `cli/system.py` | 93.8% | 16 | 0 | 200 |
| `agent/security_hardening.py` | 94.1% | 14 | 5 | 248 |
| `agent/coordinator.py` | 95.3% | 2 | 2 | 71 |
| `config.py` | 95.4% | 10 | 3 | 227 |
| `agent/tools.py` | 95.7% | 16 | 12 | 520 |

† Excluded by `[tool.coverage.run] omit`; the 26 Aug audit measured it at 38%.

Apart from that one omission every file in the package is measured — there are no
dark modules. The gaps are shallow and wide, which is the cheap kind to close.

---

## Suggested order

1. **Land `--cov-fail-under=96` in `ci.yml` and prove it fails** (finding 1).
   Nothing below is enforceable until it does, and it is one line.
2. **Test the deployment env readers** (finding 2). ~30 lines of parametrized
   test, 10 statements, and it is the configuration surface every deployed
   persona boots through. Land it with step 1 — together they should clear the
   0.14pp gap.
3. **Write the web-auth matrix** (finding 3) and **pin the auth block across
   personas** (finding 4). One test function and one generalised parity test,
   covering the only authenticated surface in the product.
4. **Decide the hardened-security layer's fate** (finding 5). Wiring it in or
   deleting it is a bigger change than any test here, and it is blocking a clear
   read on the number.
5. **Resolve `guardrails.py` section 6** (finding 6) — delete or reorder, with
   the eight-case regression test either way.
6. **Un-omit `telegram/bot.py` and test `_is_authorized`** (finding 9).
7. **Backfill the `client/` and `team/` error paths** (finding 9) — the largest
   remaining coverage-per-test.
8. **Wire up or retire the unrun trees** (finding 8), **give mutation a schedule**
   (finding 7), and then refresh the figures in `CLAUDE.md`, `README.md` and
   `AGENTS.md` once the real number settles.

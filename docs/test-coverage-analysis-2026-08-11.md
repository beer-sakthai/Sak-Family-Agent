# Test coverage analysis — 2026-08-11

Suite state as measured on this branch (`uv run pytest tests/ -m "not integration"
--cov=sakthai --cov-branch`):

| Metric | Value |
|---|---|
| Total coverage (statements + branches) | **97.27%** |
| Statements | 6,395 (100 missed) |
| Branches | 2,300 (113 partial) |
| Test files | 98 |
| Coverage floor (`fail_under`) | 96 |

The headline number is healthy and the floor is met. **The problems this analysis
found are not visible in that number** — they are places where coverage is high
but not meaningful, where covered code is never reachable in production, and
where whole trees of code sit outside measurement entirely.

Two figures in `CLAUDE.md` are now stale: it reports 96.56% and claims
`telegram/bot.py` is omitted from measurement. `pyproject.toml` has `omit = []`
and `bot.py` is measured at 98%. Worth correcting.

---

## Finding 1 — `guardrails_hardened.py` is tested but never runs in production

**Severity: high.** This is the most important finding.

`personas/sakthai/sakthai/agent/guardrails_hardened.py` (183 statements +
branches, 40 tests, 88% coverage) is imported by **nothing outside its own test
file**. Repo-wide grep for `guardrails_hardened`, `HardenedGuardrailPolicy`, and
`initialize_hardened_guardrails` returns only `tests/test_guardrails_hardened.py`,
`tests/test_security_hardening.py`, and documentation.

Meanwhile `agent/loop.py:463` resolves its policy as:

```python
policy = guardrail_policy or DEFAULT_POLICY   # DEFAULT_POLICY comes from guardrails.py
```

Nothing in the CLI, the loop, or the MCP server ever constructs the hardened
policy. So the entire `security_hardening.py` primitive set — `EnhancedPathValidator`,
`SymlinkDetector`, `ShellCommandHardener`, `ConfigFileIntegrity` — is inert at
runtime, despite `README.md:251` and `docs/SECURITY_HARDENING_IMPLEMENTATION.md`
describing it as the composed defense-in-depth layer.

The coverage report corroborates this from the inside. In
`guardrails_hardened.py`, the uncovered lines are exactly the *integration*
points, not the leaf functions:

```
299-303   the `run_command` branch of check_pre_execution — calls
          check_shell_command_hardened(); never executed by any test
295       the symlink-safety DENY return path
126, 133  the glob-pattern and case-sensitivity-trick DENY returns
```

The leaf functions are tested directly (`check_shell_command_hardened("echo hello")`
etc.), which is what produces 88%. The policy object that is supposed to call
them is not.

**What to do**

1. Decide the question the tests can't answer: is the hardened layer meant to be
   live? If yes, wire it (or a `SAKTHAI_HARDENED=1` opt-in) and add an
   integration test that drives `run_agent` with the hardened policy and asserts
   a hardened-only rule fires. If no, mark it experimental in the README and docs
   so the security posture isn't overstated.
2. Either way, add tests that go through `HardenedGuardrailPolicy.check_pre_execution`
   rather than calling the leaf checkers directly — that is what covers 295–303
   and is the only thing that proves composition works.

---

## Finding 2 — rule 6 (container escape) is unreachable dead code

**Severity: medium.** Already characterized, but unresolved.

`guardrails.py:860-912` parses docker/podman/kubectl volume mounts (`-v`,
`-v=`, `--volume=`, `--mount source=`, `--mount src=`) and `cp` arguments. Every
one of those branches is in the coverage miss list (lines 866, 872, 877-879,
884-898, 906-910 — roughly 45 lines).

`tests/test_guardrails_containers.py` deserves credit here: it documents the
situation precisely and pins it with
`test_container_specific_rule_6_is_shadowed_by_rule_2`. Rule 2 lists
docker/podman/kubectl as destructive binaries and denies every input before rule
6 is reached.

That characterization test is the right holding pattern, but it has been holding
for a while. The two legitimate resolutions the test itself names are still open:
remove rule 6 as dead code, or narrow rule 2 so rule 6 actually runs. Leaving ~45
lines of unexercised security parsing in the file is the worst of the three
options — it reads as a defense in code review and in the coverage report's
"blocked" reasons, but it has never executed.

**What to do:** pick one. If rule 6 is kept, narrow rule 2's binary list and
convert the characterization test into direct assertions on rule 6's three
reason strings.

---

## Finding 3 — critical defenses are pinned by exactly one incidental assertion

**Severity: medium.** This is the test-quality finding, and it was verified by
injecting mutations rather than by reading.

I mutated `guardrails.py` and ran the suite:

| Mutation | Owning test files | Full suite |
|---|---|---|
| Delete `".." in path` from `_is_sensitive_path` | **survived** | caught |
| Delete `.casefold()` from path-part comparison | **survived** | caught |

"Owning test files" means `test_guardrails.py`, `test_guardrails_normalization.py`,
and `test_guardrails_relative_roots.py` — the three files whose names claim this
behavior. All passed with `..` traversal detection removed entirely.

Tracking down what actually caught it, the `..` mutant is killed by exactly two
assertions, both incidental:

- `test_guardrails_sentinel_bypasses.py::test_make_c_traversal_out_of_cwd_blocked`
  — a test about `make -C`, which happens to route through the traversal check
- `test_guardrails_wrappers.py::test_is_sensitive_path_separator_and_wildcard_branches[../secrets-True]`
  — one parametrize case in a test about separator/wildcard handling

So the single most classic path-traversal defense in the codebase has no test
that names it, and would survive a refactor of either of those two unrelated
tests. This is the same failure mode `CLAUDE.md` documents for rule 6, one level
deeper: not "the wrong rule fired" but "the right rule has no owner."

**What to do**

1. Add direct, reason-pinned tests for the primitives of `_is_sensitive_path` —
   traversal, case-folding, home-relative, separator recursion — in the file that
   owns them, asserting `result.reason`, not just `DENY`.
2. Enable mutation testing in CI for `guardrails.py` at minimum. `make mutation`
   is configured (`[tool.mutmut]` is well-tuned, with real effort in the
   `also_copy`/deselect comments) but is local-only and, by the evidence above,
   not being run. A weekly scheduled workflow scoped to `guardrails.py` +
   `memory/store.py` would catch this class of decay without slowing PRs.

Files where the outcome-only pattern is densest, by ratio of `DENY` assertions to
`.reason` assertions:

```
test_guardrails_hardened.py          29 DENY  /  7 reason
test_guardrails_sentinel_bypasses.py 19 DENY  /  4 reason
test_guardrails_env_leak.py          18 DENY  /  9 reason
```

---

## Finding 4 — a security-relevant property no functional test can express

**Severity: low-medium**, but worth handling deliberately.

`web/server.py` uses `secrets.compare_digest` for bearer-token comparison in five
places. Replacing it with `==` leaves every test in `test_web_auth.py` and
`test_web_server.py` green — as it must, since the two are functionally identical
and differ only in timing.

This is not a gap a better functional test can close. It needs a *structural*
assertion: an AST or grep-based test that fails if token comparison in
`web/server.py` uses `==` instead of `compare_digest`. Cheap to write, and it
protects a property that is otherwise silently loseable in any refactor.

The same technique is worth applying to the other "invariant by convention" rules
in this repo — e.g. that migrations in `memory/store.py` are `ALTER TABLE`-only.

---

## Finding 5 — `scripts/` is 28% covered and outside the coverage gate

**Severity: medium.**

`[tool.coverage.run] source = ["sakthai"]`, so the ~5,600 LOC under `scripts/`
is never measured, even though eight test files exercise parts of it. Measuring
it explicitly:

```
scripts/ TOTAL                          1600 stmts   28% covered
  serve_api.py                   224 stmts    0%
  regenerate-supermemory-canonicals.py  126     0%
  diagnose_personas.py           123 stmts    0%
  a2a-bus.py                     151 stmts    0%
  graph_device_login.py           89 stmts    0%
  telegram_send.py                82 stmts    0%
  rename_skills.py                67 stmts    0%
```

Two of these matter more than the rest:

- **`serve_api.py` (224 statements, 0%)** — an API server with no tests at all,
  in a repo that carefully auth-gates its *other* web server. Whatever this
  exposes is untested and unaudited by the suite.
- **`graph_device_login.py` (89 statements, 0%)** — seeds the Microsoft Graph
  refresh token that `agent/tools.py`'s four Graph tools depend on. Credential
  handling with zero coverage.

`rename_skills.py` and `finalize_skills.py` mutate the persona skill trees in
bulk; a bug there is a wide blast radius across 823 skill directories.

**What to do:** add `scripts` to the coverage source with a *separate, lower*
floor (start at the current 28% so it ratchets rather than blocks), and write
tests for `serve_api.py` and `graph_device_login.py` first. Don't fold `scripts/`
into the 96% package floor — that would force a large batch of low-value tests.

---

## Finding 6 — error paths in the Graph tools are untested

**Severity: low.**

`agent/tools.py` sits at 97%, and the misses cluster in one place: the Microsoft
Graph error handling.

```
435-436  _graph_refresh_token: malformed token cache JSON → return None
521-522  HTTPError with an unparseable JSON error body → fall back to exc.reason
526-527  the catch-all `except Exception` in _graph_safe
```

These are exactly the paths that run when Graph is misconfigured or returns an
unexpected shape — i.e. the paths a user actually hits first. They are pure
functions of their inputs and trivially testable with a stubbed `urlopen`.

Same pattern, lower stakes, in `security_hardening.py`: every uncovered line
(266-267, 329-330, 421-422, 454-455, 485-486, 525-526, 536-537) is an `except
OSError` / `except (TypeError, ValueError)` handler. The TOCTOU-prevention
handler at 525-526 and 536-537 is the one worth a test, since silently returning
`(False, "Could not read file")` on a race is a security-relevant outcome.

---

## Finding 7 — property-based testing is used in exactly one file

**Severity: low, high leverage.**

`hypothesis` is a `dev` dependency and appears only in
`tests/test_store_properties.py`. Three areas in this codebase are unusually good
fits for property tests and currently rely on hand-picked examples:

- **`_is_sensitive_path`** — the natural property is *normalization invariance*:
  for a sensitive path `p`, any encoding of `p` (case variants, `..` segments,
  separator mixes, unicode normal forms, quote wrapping) must also be denied.
  This is precisely the surface the sentinel bypass tests keep finding holes in
  one example at a time, and precisely where finding 3 showed the examples are
  thin.
- **`memory/store.py` dedup and consolidate** — round-trip and idempotence
  properties (`consolidate(consolidate(x)) == consolidate(x)`).
- **`config.redact_secrets`** — the property that no registered secret survives
  redaction regardless of surrounding text.

---

## Suggested order of work

Ranked by risk reduced per unit of effort:

1. **Resolve finding 1** — decide whether the hardened layer is live, then wire
   it or downgrade the docs. Everything else in the security suite is measuring a
   layer that may not run.
2. **Finding 3** — reason-pinned tests for `_is_sensitive_path` primitives, and a
   scheduled mutation workflow over `guardrails.py`.
3. **Finding 5** — measure `scripts/` with its own ratcheting floor; test
   `serve_api.py` and `graph_device_login.py`.
4. **Finding 2** — resolve rule 6 one way or the other.
5. **Findings 4, 6, 7** — structural invariant tests, Graph error paths, and
   extending hypothesis to `_is_sensitive_path`.

Note that (1), (2) and (4) all reduce *the same* underlying risk: the security
suite currently reports high confidence about code that is either unreachable,
unwired, or pinned by accident. Coverage percentage is not the metric that
would have surfaced any of them.

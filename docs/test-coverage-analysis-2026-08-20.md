# Test coverage analysis — 2026-08-20

A point-in-time reading of the `sakthai` package's test coverage: where it
actually stands, where the gap is concentrated, and which uncovered lines are
worth closing first. Nothing here changes behavior; the one code-adjacent
finding (§5) is reported, not fixed.

## 1. The headline numbers

Measured on `main` (`98bed5c9`) with the same invocation CI uses:

```bash
uv run pytest tests/ -q -m "not integration" --cov=sakthai --cov-branch
```

| | |
|---|---|
| Tests | **4,248 passed, 20 skipped, 6 deselected**, 267 subtests, 101s |
| Test files | 149 under `tests/`, 35,466 lines |
| Measured units | 9,873 statements + 3,146 branches = **13,019** |
| Uncovered | 252 statements + 208 partial branches = **460** |
| **Total coverage** | **96.22%** (branch coverage on, `omit = []`) |
| Floor | `fail_under = 96` |

**`CLAUDE.md` says 97.92% and "134 test files (~32,358 lines)".** All three
figures are stale — the suite has grown by 15 files and ~3,100 lines while
coverage fell about 1.7 points. This PR corrects those numbers; the correction
is the point, because the stale figure implies two points of headroom that do
not exist.

The real figure was not unknown, only unpropagated: `PLAN.md`'s
*Code-scanning sweep 2026-08-20* row already recorded "96.21% coverage" from its
own full-gate run on the same day `CLAUDE.md` still said 97.92%. Two documents in
the same repository, 400 lines apart, disagreeing by 1.7 points about the number
that gates every merge.

### Headroom is ~60 units, not two points

At 12,559 covered units, the floor is reached at a total of 13,082. That leaves
room for roughly **60 units of newly-added, wholly-uncovered code before
`ci.yml` goes red** — about one medium-sized module landing without tests. The
gate is real but it is close, and it will be tripped by ordinary feature work
rather than by anything anyone would recognise as a regression.

## 2. Where the gap actually is

Rolled up by subsystem, sorted by contribution to the 460-unit gap:

| Subsystem | Coverage | Units | Missing lines | Partial branches | Share of gap |
|---|---:|---:|---:|---:|---:|
| `agent/` | 96.6% | 3,285 | 51 | 60 | 24.1% |
| `memory/` | 94.8% | 1,324 | 43 | 26 | 15.0% |
| **`evolution/`** | **80.6%** | 289 | 38 | 18 | 12.2% |
| **`governance/`** | **81.6%** | 223 | 28 | 13 | 8.9% |
| **`hub/`** | 91.7% | 421 | 24 | 11 | 7.6% |
| `cli/` | 98.3% | 1,626 | 10 | 17 | 5.9% |
| `web/` | 95.7% | 441 | 8 | 11 | 4.1% |
| `healing/` | 96.2% | 447 | 13 | 4 | 3.7% |
| `mcp/` | 97.2% | 605 | 10 | 7 | 3.7% |
| `scripts/` | 87.6% | 97 | 7 | 5 | 2.6% |
| `selfheal/` | 99.0% | 1,064 | 6 | 5 | 2.4% |
| `telegram/` | 96.7% | 335 | 6 | 5 | 2.4% |
| `a2a/` | 96.0% | 175 | 3 | 4 | 1.5% |
| `billing/` | 98.7% | 308 | 2 | 2 | 0.9% |
| `agent/providers/` | 99.6% | 680 | 0 | 3 | 0.7% |
| `cycle/`, `lead/` | 100% | 85 | 0 | 0 | 0.0% |

The shape is not "coverage is slipping everywhere". The documented core holds
up well — providers 99.6%, `selfheal/` 99.0%, `cli/` 98.3%, `memory/store.py`
99%, `agent/loop.py` 98.6%. The gap is concentrated in newer subsystems:
**`evolution/` + `governance/` + `hub/` are 7.2% of the package by size and
28.7% of the gap.** Bringing just those three to 96% would put the package at
roughly 97.2% and restore about a point of headroom.

Those same three are also absent from `CLAUDE.md`'s architecture section, along
with `a2a/`, `billing/`, `agent/gateway_router.py`, `agent/session_gateway.py`,
`mcp/gateway.py`, `mcp/security.py`, `memory/vector_mesh.py`,
`memory/write_coalescer.py`, `telegram/gateway_bot.py` and `web/gateway_api.py`
— 24 modules in all. Undocumented and under-tested are the same list, which is
what one would expect: both are trailing indicators of code that landed faster
than the scaffolding around it.

## 3. Weakest modules, by uncovered units

| Module | Coverage | Uncovered | What is uncovered |
|---|---:|---:|---|
| `mcp/security.py` | **54.5%** | 6+1 | the `dict` and `list` recursion branches of `validate_tool_arguments` — see §5 |
| `governance/mutation_daemon.py` | **58.2%** | 14+5 | `mutate_source_code`: most operator branches |
| `evolution/evolver.py` | 76.2% | 10+5 | `generate_mutation` body |
| `evolution/feedback.py` | 76.3% | 9+5 | `__init__` on-disk path, `_get_connection` |
| `evolution/registry.py` | 75.8% | 15+8 | `__init__` on-disk path, `_get_connection`, `list_variants` |
| `memory/cache.py` | 79.8% | 30+4 | all of `DistributedMemoryCache`'s L2 path |
| `governance/doctor.py` | 82.0% | 10+8 | `auto_heal`, `check_package_parity` |
| `hub/scanner.py` | 82.9% | 13+7 | `_fetch_json`, `_get_token`, `scan_ecosystem` error paths |
| `hub/validator.py` | 83.3% | 4+2 | `validate_card` rejection branches |
| `agent/security_hardening.py` | 94.1% | 14+5 | error handlers across six methods |
| `agent/guardrails.py` | 95.2% | 16+35 | see §4 |

### Three recurring shapes

**a. On-disk persistence is untested because every test passes `:memory:`.**
`evolution/registry.py` and `evolution/feedback.py` both branch in `__init__`
between a `:memory:` shared connection and a real file, and only the first
branch is ever taken. Uncovered as a result: the `SAKTHAI_EVOLUTION_DB` env-var
path, the default `~/.sakthai/evolution.sqlite3` path, the parent `mkdir`, and
`_get_connection`'s `PRAGMA journal_mode=WAL` / `synchronous=NORMAL` setup.
Every one of those runs in production and none of it runs in CI. This is the
cheapest gap to close and the one with the worst failure mode: a `tmp_path`
parametrisation over the two modes would cover about 25 units.

**b. Pure functions with untested branch tables.**
`mutate_source_code` is a 25-line pure function over three operators and eight
string branches, of which most never execute. `validate_tool_arguments` is the
same shape. Both are table-test-shaped and could be taken to 100% in a few
dozen lines with no fixtures at all.

**c. Degraded-mode paths.** `memory/cache.py`'s `DistributedMemoryCache` has its
entire L2 tier untested — `_get_client`, `get`, `set`, `invalidate`, and every
`except` arm that trips the circuit breaker. `_get_client` returns `self._client`
early when it is already set, so a fake client assigned directly to that
attribute exercises the whole tier without a redis dependency. The circuit
breaker itself is at 100%; what is untested is whether anything ever calls it.
Same shape in `hub/scanner.py` (`_fetch_json`, `_get_token`) and in
`agent/security_hardening.py`, where the uncovered lines are exclusively the
`except` arms of `atomic_check_and_read`, `normalize_path_thoroughly`,
`is_symlink`, `_capture_hashes`, `verify` and `check_permissions`.

## 4. `agent/guardrails.py`

At 95.2% over 1,066 units this is the single largest uncovered block in the
package (51 units), and it is the most attacked surface. Two of the gaps are
worth naming:

- **`_check_nested_script_tokens`, lines 807 and 826–827.** Line 807 is the
  `continue` that skips a flag while walking backwards to find the shell binary
  before a `-c`. It never executes, meaning no test passes a flag between the
  binary and `-c` — `bash --norc -c '<destructive>'` and
  `python -E -c '<destructive>'` (line 856, same shape) take a code path CI has
  never run. The rule may well hold; nothing currently demonstrates that it does.
- **`_get_active_secrets`, lines 1430–1431 and 1440–1441.** Both `if isinstance(s, str) and len(s) > 5`
  bodies — the `config._EXTRA_SECRETS` registrations and the environment-variable
  sweep. The output filter's secret list is therefore only ever populated from
  its third source in tests. `tests/test_memory_secrets_redaction.py` covers
  redaction in the store; the guardrail-side collection of what to redact is the
  part that is unexercised.

Per the convention already recorded in `CLAUDE.md`, tests added here must pin
`result.reason`, not just `action == DENY` — a broader rule firing first is
exactly how the container battery stayed green while the rule it was named for
never ran.

## 5. One finding that is not just a coverage number

`mcp/security.py::validate_tool_arguments` is the sole argument gate on
`MCPGateway.invoke_tool`. Its `str` branch rejects control characters, DEL,
`../`, `..\`, and a leading `/etc` or `/root`. Its `list` branch — lines 33–38,
uncovered — checks only `../` and `ord(c) < 32`. The two are not equivalent:

```python
>>> validate_tool_arguments({"p": "/etc/shadow"})     # SecurityViolationError
>>> validate_tool_arguments({"p": ["/etc/shadow"]})   # returns, allowed
>>> validate_tool_arguments({"p": ["..\\windows"]})   # returns, allowed
>>> validate_tool_arguments({"p": ["a\x7fb"]})        # returns, allowed
```

(Verified against the working tree, not inferred from the source.) The `dict`
branch recurses and so is equivalent; only the list branch is weaker. Wrapping a
payload in a one-element list bypasses three of the four string checks.

This is a defect in the gate rather than in the tests, so it is out of scope for
an analysis PR — but it is the clearest illustration of why the number matters:
the asymmetry sits precisely on the lines coverage reports as never executed, and
would have been found the moment anyone wrote a test for them.

## 6. Suggested order of work

Roughly by value per unit of effort:

1. **Fix the list branch of `validate_tool_arguments`** and test all three
   branches to parity. Security defect first, coverage second.
2. **`evolution/` on-disk mode** — parametrise the existing tests over
   `:memory:` and `tmp_path`. ~25 units, no new fixtures.
3. **`governance/mutation_daemon.mutate_source_code`** — a table test over the
   three operators and their fallthroughs. ~19 units, pure function.
4. **`DistributedMemoryCache`** — a fake client assigned to `_client`, covering
   hit, miss, and each `except` arm. ~34 units, and it is what proves the
   circuit breaker is actually wired.
5. **`agent/guardrails.py` nested-script paths** — flag-then-`-c` for both the
   shell and interpreter walks, plus the two `_get_active_secrets` sources.
   Pin `result.reason`.
6. **`hub/scanner.py` and `agent/security_hardening.py` error arms** — the
   long tail; worth doing but each unit is dearer than the four above.

Items 2–4 alone are about 78 units, which would take the package to roughly
96.8% and roughly triple the current headroom above the floor.

## 7. Method

Full suite, integration tests deselected by marker (as CI does), branch coverage
on, `-p no:randomly` for a stable ordering. Per-module attribution of missing
lines to enclosing functions was done by mapping the JSON report's
`missing_lines` onto the AST of each source file. The run was green; no test was
modified, skipped, or added to produce these numbers.

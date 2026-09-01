# Test coverage audit — 2026-09-01

Analysis only; no production code changed. Fifth in a series, after
[`2026-08-26`](./test-coverage-audit-2026-08-26.md),
[`2026-08-27`](./test-coverage-audit-2026-08-27.md),
[`2026-08-28`](./test-coverage-audit-2026-08-28.md) and
[`2026-08-31`](./test-coverage-audit-2026-08-31.md), re-measured on
`claude/test-coverage-analysis-qjh3f1` at `3e89038`:

```bash
uv sync --all-extras
uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-report=term-missing
```

Python 3.11.15, 106 test files, 2,313 tests collected, **96.21% branch
coverage** — 191 uncovered statements and 156 partial branches out of 7,710
statements and 2,610 branches. `Required test coverage of 96.0% reached.`

**The package and test trees are byte-identical to the 31 Aug audit.** `git log
e10b47a..HEAD -- personas/sakthai/sakthai tests` is empty; everything since
landed in `apps/`, docs and workflow config. The number reproduces to the
digit, so this round does not re-litigate the standing findings — it re-verifies
them briefly at the end and spends its effort on three questions the series has
not asked.

| Measure | 26 Aug | 27 Aug | 28 Aug | 31 Aug | **1 Sep** |
|---|---:|---:|---:|---:|---:|
| Branch coverage | 96.018% | 95.849% | 95.862% | 96.211% | **96.211%** |
| Uncovered statements | 168 | 213 | 213 | 191 | **191** |
| Partial branches | 149 | 170 | 170 | 156 | **156** |

The three new questions: *does the suite actually stay in its sandbox* (§1),
*does the coverage it reports correspond to faults it would catch* (§2), and
*is the 96% discipline applied to the rest of the repo* (§4).

---

## 1. The suite is not hermetic: it downloads and executes npm packages mid-run

**Severity: high** · `tests/test_cli.py:1397` · **new**

CLAUDE.md states the suite is hermetic: "no network, no GCP credentials". It is
not. A single test in `tests/test_cli.py` reaches the public npm registry,
downloads packages, and executes them.

`test_run_persona_uses_persona_store_and_soul` invokes the real CLI:

```python
monkeypatch.setattr(agent_mod, "run_agent", fake_run_agent)
result = runner.invoke(main, ["run", "hi", "--persona", "sakking"])
```

Patching `run_agent` does not contain this, because the MCP connection happens
*before* `run_agent` is ever called. `cli/agent.py:280` opens
`_tool_context(...)` first, and `_tool_context` at `cli/agent.py:58-72` resolves
`config.persona_mcp_config_path("sakking")` and calls `connect_servers()`. With
no `SAKTHAI_MCP_CONFIG` set and no `PERSONAS_DIR` redirect, that resolves to the
repository's own `personas/sakking/config/mcp.json`, which declares four
servers, every one of them an `npx -y ...@latest`:

```json
"playwright":      {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]},
"chrome-devtools": {"command": "npx", "args": ["-y", "chrome-devtools-mcp@latest"]},
"huggingface":     {"command": "npx", "args": ["-y", "@huggingface/mcp-server"]},
"hf-media":        {"command": "npx", "args": ["-y", "@llmindset/mcp-hfspace", ...]}
```

Observed during the measurement run — `npm exec chrome-devtools-mcp@latest` and
`npm exec @llmindset/mcp-hfspace ...` as live children of the pytest process.

**It is also, on its own, most of the suite's wall-clock cost:**

```console
$ time uv run pytest "tests/test_cli.py::test_run_persona_uses_persona_store_and_soul" -q --no-cov
1 passed
real  4m43.671s
user  0m3.844s
sys   0m0.474s
```

Four minutes 43 seconds of wall time against 3.8 seconds of CPU — 99% of it
blocked on the network — inside a full-suite run that takes about 7.5 minutes
end to end. Both measurement runs stalled at the identical point (12%), so this
is deterministic, not an unlucky day.

**Confirmed independently on a GitHub runner.** The above was measured in a
sandbox whose egress is proxied. CI reaches the network differently, so the
`test (3.11)` job's StepSecurity Harden-Runner egress audit (`EgressPolicy:audit`
— it records, it does not block) is the better witness. During that job:

```
00:35:28  domain resolved: registry.npmjs.org., ip address: 104.16.0.34
00:35:29  endpoint called 104.16.0.34:443, registry.npmjs.org., pid 2963, process: node
00:35:34  endpoint called 104.16.0.34:443, registry.npmjs.org., pid 2985, process: node
00:35:36  endpoint called 104.16.0.34:443, registry.npmjs.org., pid 3012, process: node
00:35:36  endpoint called 104.16.0.34:443, registry.npmjs.org., pid 3034, process: node
00:35:37  endpoint called 104.16.0.34:443, registry.npmjs.org., pid 3056, process: node
00:35:43  domain resolved: huggingface.co., ip address: 3.170.185.14
00:35:43  domain resolved: black-forest-labs-flux-1-schnell.hf.space., ip 52.86.59.147
00:35:43  endpoint called 3.170.185.14:443, huggingface.co., pid 3095, process: node
00:35:43  endpoint called 52.86.59.147:443, black-forest-labs-flux-1-schnell.hf.space., pid 3095
00:35:44  endpoint called 172.217.112.4:443, play.googleapis.com., pid 3018, process: node
```

Five `node` processes fetching from the npm registry inside the unit-test job,
and it does not stop at the registry: the servers, once running, reach
`huggingface.co` and `black-forest-labs-flux-1-schnell.hf.space` — the
FLUX.1-schnell Space named in SakKing's `hf-media` spec — plus
`play.googleapis.com`. So the suite's egress is not one package download; it is
four MCP servers coming up and talking to their own backends, in CI, on every
push.

**Correction to the cost figure above.** That whole window is 00:35:28–00:35:44,
about **16 seconds** on the runner, against 4m43s in the sandbox. The wall-time
cost is therefore environment-specific — it is dominated by how fast `npx` can
reach the registry — and the "~63% of suite wall time" figure holds for a
proxied environment, not for CI, where the `test` jobs complete in 2m51s /
3m06s total. The hermeticity and supply-chain points do not depend on the
timing and are now demonstrated on CI rather than inferred: treat the runtime
saving as a local-developer benefit, and the unpinned egress as the reason to
fix it.

**And the test gains nothing from any of it.** `connect_servers` fails soft
(`mcp/manager.py:53-56` logs a warning and continues), so with the registry
unreachable it yields `[]` and the test passes exactly as it does with the
registry up. Its three assertions are about the memory shard and the SOUL
prefix; none of them touches MCP. The four minutes buy no signal.

Three separate problems fall out of one line:

- **Hermeticity** — a documented invariant of the suite is false, and CI's
  runtime depends on npm registry availability.
- **Supply chain** — `npx -y ...@latest` executes whatever the registry serves
  *today*, unpinned, on every contributor's machine and on every CI runner, as
  a side effect of running the tests.
- **Cost** — roughly 63% of suite wall time in a proxied environment (~16s on a
  GitHub runner) for zero assertions.

**Proposal** — the fix is already written three times in the same file. The
sibling tests at `test_cli.py:1460` and `1514` are the same shape and pass
`--no-mcp`; `test_run_persona_autoloads_own_mcp_config` at `1556` instead
redirects `PERSONAS_DIR` at `tmp_path` and points the spec at
`sys.executable -m sakthai.mcp`. Either works here. Then add a guard so it
cannot come back: a session-scoped autouse fixture that sets
`SAKTHAI_MCP_CONFIG` to an empty config unless a test opts out, which makes
"real MCP server" an explicit choice rather than the default.

---

## 2. Mutation spot-check: half the mutants survive, including two in web auth

**Severity: high** · `web/server.py`, `agent/guardrails.py` · **new**

`make mutation` is `|| true`-swallowed and in no workflow, so the series has
never had an assertion-strength signal to set against the coverage number. I
ran six hand-written mutants against the test files that own each seam —
19 guardrail/sentinel files for `guardrails.py`, `test_web_auth.py` +
`test_web_server.py` for `web/server.py` — reverting each afterwards.

| Mutant | Change | Result |
|---|---|---|
| M1 | drop `path.startswith("~")` from `_is_sensitive_path` | **killed** |
| M2 | make sensitive-dir matching case-**sensitive** again | **killed** |
| M3 | drop `","` from the separator list | **SURVIVED** |
| M4 | widen the bare-`tmp` exception to every `tmp` subpath | **killed** |
| M5 | Bearer compare → first-8-character prefix match | **SURVIVED** |
| M6 | fail **open** when no token is configured | **SURVIVED** |

The three kills are the good news, and they are exactly where someone wrote an
example: tilde, case, `/tmp`. The three survivors are the finding.

**M5 is an authentication bypass that the auth suite does not notice.**
Replacing `secrets.compare_digest(token, expected_token)` with
`token[:8] == expected_token[:8]` leaves every test in `test_web_auth.py` and
`test_web_server.py` green. The cause is visible in one line: the only
invalid-token test sends `"Bearer wrong_token_xyz"` — a string that differs from
the real token in its *first* character. **No test ever sends a near-miss
token**, so nothing pins the comparison to full length or to constant time.
Line 236 is *covered*; the behaviour it implements is not *verified*. That gap
is invisible to a coverage report by construction.

**M6 confirms the fail-closed guard is decorative.** Flipping
`if not expected_token: return False` to `return True` — serve every request
unauthenticated when no token is configured — is caught by nothing.
`web/server.py:230` is in the uncovered list, so this is a coverage gap the
report already showed; the mutant shows what that gap is worth.

**M3 shows the enumerated attack corpus has a hole in it.** `_is_sensitive_path`
splits on four separators, `("=", "@", ":", ",")`. Removing the comma survives
all nineteen guardrail and sentinel files, ~600 lines of literal attack strings
included, even though the comma path is live today:

```console
$ python -c 'from sakthai.agent.guardrails import _is_sensitive_path as f; print(f("src=/etc,dst=/x"))'
True
```

Three of four separators are tested. The fourth — the one that catches
`--mount src=/etc,dst=/x` — is held up by no test at all.

This is the 31 Aug audit's finding 6 ("enumeration cannot win") turned from an
argument into a measurement, and extended to `web/server.py`, which that audit
did not suspect. It also says something about where to spend effort: at 96.21%
coverage, the marginal uncovered line is worth less than the covered-but-
unverified one.

**Proposal**

- **Near-miss token matrix** for all three credential channels (header, query,
  cookie): right length/wrong last character, correct prefix + truncated,
  correct token + trailing whitespace, empty, and the empty-configured-token
  case from M6. This kills M5 and M6 and closes the carried-forward
  query/cookie gap (`web/server.py:213-224`) in the same table.
- **Property tests for `_is_sensitive_path`**, seeded from
  `_SENSITIVE_BASENAMES`/`_SENSITIVE_DIRS` and *parametrized over the separator
  tuple itself* so a fourth separator cannot be untested. `hypothesis` is
  already a dev dependency and is used on exactly one module.
- **Give mutation a schedule** — drop the `|| true`, fix the stale
  `pytest_add_cli_args_test_selection` entries (they still deselect two tests
  that do not exist), and run it weekly on the seam modules. Six hand-written
  mutants found three survivors in one sitting; a scheduled run would keep
  finding them.

---

## 3. The sandbox escape is three categories, not one — and one of them is agent-visible

**Severity: high** · `tests/conftest.py`, `tests/test_agent_loop.py` ·
*extends 2026-08-31 finding 1*

The 31 Aug audit found the suite creating two empty persona shards at
`~/.sakthai/{sakking,saksee}/memory.db`. Re-run from a genuinely pristine home,
the escape is larger:

```console
$ find ~/.sakthai            # HOME had no .sakthai before the run
~/.sakthai/eval.jsonl            42 records
~/.sakthai/sessions/             42 JSON session logs
~/.sakthai/sakking/memory.db     32 KB, schema-migrated, 0 rows
~/.sakthai/saksee/memory.db      32 KB, schema-migrated, 0 rows
```

Two categories the previous audit did not report: **42 session logs and 42 eval
records**. Attributed by running one file against a sentinel home,
`tests/test_agent_loop.py` alone accounts for 39 of each — it is the dominant
leaker, and it has no isolation fixture.

**The session logs matter more than the databases.** `~/.sakthai/sessions/` is
what `memory/session_search.py` reads, and it backs both `sakthai sessions` and
the **`search_sessions` built-in tool**. So running the test suite on a machine
where an agent also runs injects fabricated sessions — with `"task"` and full
message content — into that agent's live, searchable history. Unlike the two
empty databases, this is not a dormant path: it is test fixtures becoming
retrievable context at runtime. The sampled records are visibly synthetic
(`"task": "remember it"`, `"name": "sk__learn"`), which is precisely what makes
them undesirable in a real agent's recall.

Isolation is opt-in and thinly applied: **9 of 106 test files** define an
autouse fixture (`test_auth`, `test_chat`, `test_cli`, `test_cli_eval`,
`test_cli_system`, `test_memory_merged`, `test_provider_contracts`,
`test_provider_resilience`, `test_web_server`). `tests/conftest.py` still
defines `store` and `sakthai_home` with neither marked autouse, so the other 97
files inherit no isolation at all. `test_cli.py` *does* isolate `SAKTHAI_HOME` —
which is why §1's escape had to come through `Path.home()`-resolved persona
config rather than through `SAKTHAI_HOME`.

### The flap did not reproduce

The 31 Aug audit attributed the series' long-standing ±1-statement drift to this
leak — specifically to `memory/store.py:211-217` forking on whether the persona
DB file already exists (create at `0600` vs `chmod`). That did not reproduce
here. Two full runs, the first against a home with no `~/.sakthai` at all and
the second against the home the first run had just populated, returned
identical totals:

| Run | `HOME` state | Missing | Partial | Coverage |
|---|---|---:|---:|---|
| 1 | pristine | 191 | 156 | 96.211% |
| 2 | shards + sessions from run 1 | 191 | 156 | 96.211% |

So the create-vs-chmod fork does not by itself move the package total in this
environment, and the drift the series recorded has some other cause — or is
environment-specific. This does not weaken the finding: the leak is real,
measured above, and larger than previously reported. It narrows it. The reason
to fix the fixture is the write into `~/.sakthai/sessions/`, not the flap, and
the case for fixing it does not depend on the flap being explained.

**Proposal** — unchanged in shape from the 31 Aug audit, but the fixture has to
cover more than `SAKTHAI_HOME`: an autouse fixture in `tests/conftest.py`
pinning `HOME` *and* `SAKTHAI_HOME` at `tmp_path`, plus a guard test that fails
if a run creates anything under the invoking user's `~/.sakthai`. The guard is
what makes it stay fixed, and it would have caught all three categories.

---

## 4. The 96% floor covers 40% of the repository's test surface

**Severity: medium** · `.github/workflows/apps.yml` · **new**

`ci.yml` gates `sakthai` at `--cov-fail-under=96`. No other tree in the repo
measures coverage at all. `apps.yml` runs:

```yaml
- name: Test
  run: npm test                      # vitest run — no --coverage, no threshold
- name: Test
  run: python -m pytest tests/ -q    # agent_workflow_framework — no --cov
```

Both green on zero tests, and neither can regress. That would be an abstract
complaint except for what just landed: PR #1248 rewrote
`apps/sak_agent_dashboard` — 73 source files, 22 components — and touched no
Python and no `tests/`. It is the largest recent change in the repo and it
entered under no coverage accountability whatsoever, while the package it
renders is held to 96%.

Re-derived counts (all up since 31 Aug):

| Tree | Files | Run by | Coverage gate |
|---|---:|---|---|
| `tests/` | 106 | `ci.yml` | **96%** |
| `apps/agent_workflow_framework/tests/` | 13 *(was 7)* | `apps.yml` | none |
| `apps/sak_agent_dashboard` (TS) | 16 *(was 14)* | `apps.yml` | none |
| `personas/sakthai/agent-self-evolution/tests/` | 8 | `agent-self-evolution.yml` | none |
| `sakthai-chat-cli/` | 86 | **nothing** | — |
| `personas/*/skills/**` | 14 *(was 11)* | **nothing** | — |
| `personas/shared/agent-self-evolution/tests/` | 8 | **nothing** | — |
| `services/teams-copilot-mcp/tests/` | 3 | **nothing** | — |

**111 unrun Python test files against 106 that run**, and the gap widened
rather than closed since the 31 Aug audit asked for it.

**Proposal** — add `--coverage` to the dashboard's vitest step and `--cov` to
the framework's pytest step with a floor each, starting at whatever they measure
today so the step is a ratchet rather than a blocker. A tree with tests and no
floor is one refactor away from a tree with no tests.

---

## 5. Re-verified, unchanged

Measured again at `3e89038`, not restated from the previous write-up:

- **96.21% reproduces exactly** — 191 missing / 156 partial, identical to
  31 Aug, on an identical tree, and identical again across two back-to-back
  runs today (see §3). Derived from `coverage json`: 10,320 units, 9,929
  covered, 9,908 needed for 96% — headroom is still **21 units**.
- **Assertion hygiene is good.** An AST pass over all **1,899** `def test_*`
  (counting `assert`, `pytest.raises`, `self.assert*`, mock `.assert_*` and
  `assert_*` helpers) finds **7** with no possible failure check — the same six
  the 28 Aug audit named, plus the `test_tool` fixture pytest does not collect.
  Four of the six are the `initialize_hardened_guardrails` level tests in the
  dead hardened layer. This is not where the risk is; §2 is.
- **Weakest modules are unmoved.** Largest holes by uncovered units (missing
  statements plus missing branch exits, from `coverage json` — not the
  miss+partial columns of the terminal report, which undercount):
  `agent/guardrails.py` **98** (89.2%), `web/server.py` **43** (89.3%),
  `agent/tools.py` **30** (95.7%), `guardrails_hardened.py` **22** (88.0%),
  `security_hardening.py` **19** (94.1%), `cli/client.py` **18** (87.6%),
  `cli/team.py` and `cli/system.py` **16** each, `config.py` **13**.
  `guardrails.py` is still the largest single hole by more than double.
- **`web/server.py` uncovered lines are exactly as reported:** `42-44`, `85`,
  `213-217`, `220-224`, `230`, and the query/cookie loop partials at `243-259`.
- **Still open from earlier rounds, none closed:** the nine deployment env
  readers at `config.py:296-333`; `test_integration.py`'s unscoped
  `except Exception: pytest.skip(...)` around every live-provider call; 30 of
  168 exception handlers never executed, including all of `cli/client.py`,
  `cli/system.py`, `client/manager.py` and `client/verifier.py`; the
  `web/api.py` ↔ `agent_workflow.persistence` on-disk contract pinned on
  neither side; `web/server.py` persona parity unpinned; `guardrails.py`
  section 6 (`866-910`) unreachable; `telegram/bot.py` omitted from measurement
  with `_is_authorized` untested; the hardened layer still dead code
  (deleting it → 96.43%, headroom 42).

---

## Suggested order

Ranked by risk closed per hour, not by coverage points gained. The first two
change no coverage number at all.

1. **Add `--no-mcp` to `test_cli.py:1397`** (§1). One flag. Removes a live
   npm-registry dependency and an unpinned remote-code path from the suite —
   confirmed on CI by Harden-Runner's egress audit, which also caught the
   servers reaching `huggingface.co` and a HF Space. Returns ~63% of wall time
   in a proxied environment; on CI the saving is ~16s and the reason to do it is
   the egress, not the clock. Then add the `SAKTHAI_MCP_CONFIG` autouse guard so
   it cannot regress.
2. **Autouse `HOME`/`SAKTHAI_HOME` fixture + escape guard test** (§3). One
   fixture and one test. Stops 42 fabricated sessions per run entering the
   `search_sessions` corpus, and makes the gate's input reproducible.
3. **Near-miss token matrix for all three auth channels** (§2). Kills M5 and
   M6 and closes `web/server.py:213-224` and `230` in one table — the only item
   here that is both a real gap and cheap coverage.
4. **Property tests for `_is_sensitive_path`, parametrized over the separator
   tuple** (§2). Kills M3 and generalises the class instead of the instance.
5. **Cover the `cli/`/`client/` exception handlers** (carried, 31 Aug finding
   4). Eleven handlers that have never run, in the code an operator hits first.
6. **Coverage floors on the `apps/` trees** (§4), set at today's measurement as
   a ratchet.
7. **Un-swallow `make mutation` and schedule it** (§2), then **narrow the
   integration-tier `except`**, **test the nine env readers**, and **decide the
   hardened layer's fate** (all carried).

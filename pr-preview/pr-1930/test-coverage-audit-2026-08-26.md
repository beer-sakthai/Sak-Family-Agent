# Test coverage audit — 2026-08-26

Analysis only; no production code changed. Measured on branch
`claude/test-coverage-analysis-3u5ob4` with:

```bash
uv sync --all-extras
uv run pytest tests/ -m "not integration" --cov=sakthai --cov-branch --cov-report=term-missing
```

Python 3.11.15 — **2,004 passed, 2 skipped, 6 deselected** in 362s over 101 test
files.

## Headline numbers

| Metric | Value |
|---|---|
| Total branch coverage | **96.018%** |
| Floor (`fail_under`) | 96 |
| Headroom | **0.018pp** (≈1 statement) |
| Uncovered statements | 168 |
| Partial branches | 149 |

`CLAUDE.md` records 96.56% over 1,978 tests in 95 files. Both figures have
drifted (96.018%, 2,004 tests, 101 files) and the decline produced no CI signal,
because it stayed above the floor.

## The read

Coverage is not distributed along risk. The local CLI — the surface a developer
drives by hand — is at 98–100% almost everywhere. The surfaces that accept input
from someone else are where the gaps are: the Telegram bot (38%, excluded from
the floor), the web API's rejection paths, and the environment variables the
systemd deployment reads.

Three of the eight findings are not "write more tests" — they are decisions
about code that shouldn't be measured the way it currently is. Settling those
first changes what the percentage means.

---

## 1. The Telegram bot's authorization check has no tests, and a coverage `omit` hides it

**Severity: high** · `telegram/bot.py` · 38% covered · 98 statements uncovered

`pyproject.toml` sets `omit = ["*/telegram/bot.py"]`, so the module never reaches
the coverage floor. Measured directly it is at 38%, and what is missing is the
auth boundary itself — `_is_authorized()` and the whole `_run_task()` handler,
including the branch that turns an unauthorized user away:

```python
# telegram/bot.py:65 — uncovered
def _is_authorized(user_id: int | None) -> bool:
    allowed = telegram_allowed_user_ids()
    return user_id is not None and user_id in allowed

# telegram/bot.py:96 — uncovered
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
```

This is a polling bot that runs `run_agent()` in-process with the caller's task
text. The allowlist is the only thing between an arbitrary Telegram user and the
agent loop, and nothing asserts it works. The same module is also exempt from
mypy (`ignore_errors = true`), so neither gate covers it.

**Proposal**

- Drop the `omit`; give the module its own lower floor rather than excluding it,
  so erosion is visible instead of silent.
- Table-test `_is_authorized`: allowlisted id, non-allowlisted id, `None`, empty
  allowlist, id-as-string.
- Test `_run_task` with a fake `Update`: assert the reject path replies and
  returns *without* calling `run_agent` — that negative assertion is the one
  that matters.
- Cover `_session_key` returning `None`, and `_env_bool`'s parsing table.

## 2. 371 statements of security-hardening code are never imported outside their own test

**Severity: high** · `agent/guardrails_hardened.py`, `agent/security_hardening.py` · decision needed

```
$ grep -rn "guardrails_hardened" --include=*.py .
tests/test_guardrails_hardened.py:7:from sakthai.agent import guardrails_hardened as gh
tests/test_guardrails_hardened.py:9:from sakthai.agent.guardrails_hardened import (
— no production importer
```

`guardrails_hardened.py` (123 stmts) is imported by exactly one file: its own
test. `security_hardening.py` (248 stmts) is imported only by
`guardrails_hardened.py`. Nothing in the package wires either in — `run_agent`
uses `DEFAULT_POLICY` from `guardrails.py`.

So ~371 statements contribute to the 96% while never running in production. Even
within the subsystem the integration seam is untested: the hardened
`run_command` path (`:299-303`), the glob-pattern DENY (`:126`) and the
case-sensitivity-trick DENY (`:133`) are all uncovered — the three things the
module exists to add.

**Proposal** — this is a call for the maintainer, not a mechanical fix:

- If the hardening is meant to ship: wire it behind an env flag and test it as a
  *policy* (through `check_pre_execution`), not as loose helper functions. That
  also closes `:126`, `:133`, `:299-303`.
- If it isn't: delete it, or move it out of the measured package. Either way it
  should stop padding the denominator.

## 3. The container guardrails are unreachable — an earlier generic rule always fires first

**Severity: high** · `agent/guardrails.py` · 89% covered · lines 866–912

Section 6 of `_block_dangerous_shell_commands` has dedicated rules for `-v=`,
`--volume=`, `--mount source=`, `--mount src=` and `docker cp`. All are
uncovered. Tracing `check_pre_execution` shows why — every such command is
denied earlier, by `_check_destructive_tokens` at line 752:

```
$ docker run --mount type=bind,source=/etc/shadow,target=/mnt alpine
   DENY — denied at: _check_destructive_tokens:752
$ docker cp /etc/shadow c:/x
   DENY — denied at: _check_destructive_tokens:752
$ docker run -v /etc/shadow:/mnt alpine
   DENY — denied at: _check_destructive_tokens:752
```

The commands *are* blocked, so there is no live vulnerability. But the
specialized rules are dead branches that cannot be reached through the public
API, so they are unverified — and would stay unverified if the generic token
scan were ever narrowed, precisely the moment they are meant to be the backstop.
The same shape applies to `chroot` on a sensitive NEWROOT (`:1144`), `make`'s
attached `-C`/`-f` forms (`:368-375`), and the interpreter flag-skip loops
(`:461`, `:513`).

**Proposal**

- Test the section-6 logic directly as a unit, bypassing the earlier rules, so
  shadowing cannot hide a regression.
- Add an ordering test asserting *which* rule denies each command. Rule order is
  load-bearing and entirely implicit; a reorder today is invisible to CI.
- Then decide whether section 6 earns its keep, or whether the generic scan
  should absorb it.

## 4. Web auth tests cover acceptance only — every rejection path is untested

**Severity: medium** · `web/server.py` · 87% covered · `test_web_auth.py` has 7 tests

`_is_authenticated()` accepts a token via header, query string, or cookie. The
tests supply a *correct* token through each. The partial branches (`191→200`,
`202→210`, `226→225`, `230→225`) are the loop-exhaustion arms — meaning a
*wrong* token in a query param or cookie has never been exercised. Also fully
uncovered:

```python
# :178 — fail-closed when no token is configured
        if not expected_token:
            return False

# :161-172 — _has_auth_attempt(), which decides 401 vs 403
            for item in query.split("&"):
                if "=" in item:
                    k, _ = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        return True
```

So the 401-vs-403 distinction — the whole point of `_has_auth_attempt` — has no
test, and neither does the cached-token warm path (`:42-44`).

**Proposal** — one parametrized matrix: {absent, malformed, wrong-token,
correct-token} × {`Authorization` header, `?token=`, `Cookie:`} × {`/health`,
`/api/stages`, static path}, asserting status code *and* body shape. That single
test closes most of this module's gap and pins the 401/403 contract from
`docs/superpowers/specs/2026-08-03-sakthai-web-auth-design.md`.

## 5. The deployment env-var readers are at 0%

**Severity: medium** · `config.py` lines 270–307 · 5 functions

Every function in the `SAKTHAI_*` launch-override family is uncovered:
`sakthai_default_provider`, `sakthai_default_model`, `sakthai_fast_mode`,
`sakthai_skip_mcp`, `sakthai_with_skills`. Their own docstrings say what they are
for — "Telegram/systemd launches" — which is the same path finding 1 covers from
the consumer side.

```python
# config.py:304 — uncovered
def sakthai_with_skills() -> list[str]:
    raw = os.environ.get("SAKTHAI_WITH_SKILLS", "")
    return [item.strip() for item in raw.replace(",", " ").split() if item.strip()]
```

`sakthai_with_skills` is the interesting one: it accepts both comma- and
space-separated input, and `infra/vm-agents/env-templates/*.env.example` is what
feeds it. Nothing asserts that contract holds.

**Proposal**

- A parametrized `test_config_env_overrides.py`: unset, empty, whitespace-only,
  mixed casing (`"True"`, `"ON"`), and for the skills list both separators plus a
  trailing comma.
- One integration-flavoured test that loads a real
  `infra/vm-agents/env-templates/*.env.example` and asserts the resulting
  `run_agent` kwargs — that catches template drift, which unit tests will not.

## 6. The team pipeline's parallel path is tested happy-path only

**Severity: medium** · `team/engine.py` 86%, `cli/team.py` 84% — the two weakest modules

`test_run_pipeline_parallel_batch` exists and passes, but only drives success.
Uncovered in `engine.py`: the parallel step's exception handler (`:259-277`),
error propagation and batch abort (`:291-298`), the streaming `pipeline_error`
event (`:413-414`), and the group-boundary flush (`:115`, `:126`).
`load_pipeline_from_file` — YAML and JSON, `FileNotFoundError`, non-dict top
level — is untested end to end (`:61-83`).

```python
# team/engine.py:259 — uncovered: what happens when a parallel step raises
                except Exception as exc:  # noqa: BLE001
                    ...
                    return (step_item, sr, f"ERROR: {exc}")

# team/engine.py:293 — uncovered: does one failure abort the batch?
                    has_batch_error = True
                    all_success = False
```

Untested concurrency error-handling is the usual source of intermittent CI
failures, and `team/` is not yet described in `CLAUDE.md` — it is new enough that
the conventions have not caught up with it.

**Proposal**

- Inject a step whose fake client raises, inside a two-step parallel group;
  assert the sibling still completes, `all_success is False`, and the pipeline
  stops at the group boundary rather than continuing.
- Round-trip a pipeline through both `.yaml` and `.json` via `tmp_path`, plus the
  missing-file and non-dict error cases.
- In `cli/team.py`, drive `on_step_start`/`on_step_complete` in both `--json` and
  human modes, and the `get_pipeline` failure exit.

## 7. Two personas execute 13.5k lines that no test measures

**Severity: medium** · `personas/shared/sakthai/` · structural

SakJules and SakTan symlink `sakthai/` to `personas/shared/sakthai/`. Coverage
measures only `personas/sakthai/sakthai`, and only `guardrails.py` has a parity
test. The two trees have genuinely diverged:

```
config.py      148 changed lines
cli/agent.py    56 changed lines
auth.py         33 changed lines
agent/loop.py   33 changed lines
skills.py       25 changed lines
agent/chat.py    1 changed line
```

So two of six personas run credential resolution, config, and the agent loop in
versions no test has ever executed. `CLAUDE.md` already flags the divergence as a
known gap; this quantifies what it costs on the testing side.

**Proposal**

- Short term: extend the `tests/test_persona_guardrails_parity.py` pattern to the
  other diverged modules — as a *pinned* diff, so new drift fails CI while the
  known divergence stays green.
- Longer term: this is the reconciliation already tracked in `CLAUDE.md`.
  Collapsing the duplication is the real fix; the parity test is the guard rail
  until then.

## 8. The coverage floor cannot detect erosion — it already has eroded

**Severity: low** · `pyproject.toml` · 96.018% vs `fail_under = 96`

`CLAUDE.md` records 96.56%; the suite measures 96.018% today. The floor is 96, so
the decline produced no signal — and the remaining 0.018pp means the next
uncovered statement turns CI red for whoever happens to add it, regardless of
whether their change caused the problem.

**Proposal**

- After the work above, raise `fail_under` to sit ~0.5pp under the real number,
  and re-raise it deliberately rather than leaving slack.
- Add per-module floors for the security-relevant modules so a single large
  module cannot drop to zero while the global figure absorbs it — which is
  exactly what `telegram/bot.py` demonstrates today.
- Refresh the coverage and test-count figures in `CLAUDE.md` and `README.md`.

---

## Weakest modules

| Module | Cover | Miss | Partial | Why it matters |
|---|---:|---:|---:|---|
| `telegram/bot.py` † | 38% | 98 | 7 | Auth boundary; omitted from floor |
| `cli/team.py` | 84% | 10 | 0 | Step callbacks, error exit |
| `team/engine.py` | 86% | 21 | 15 | Parallel failure handling |
| `web/server.py` | 87% | 15 | 16 | Auth rejection paths |
| `agent/guardrails_hardened.py` | 88% | 10 | 8 | Not wired into production |
| `scripts/verify_hf_upload.py` | 88% | 7 | 5 | Network error paths |
| `agent/guardrails.py` | 89% | 44 | 36 | Largest absolute gap; shadowed rules |
| `memory/provider.py` | 92% | 1 | 2 | Context-window limiting |
| `agent/security_hardening.py` | 94% | 14 | 5 | Not wired into production |
| `config.py` | 95% | 10 | 3 | Deployment env overrides at 0% |
| `agent/coordinator.py` | 95% | 2 | 2 | Unknown-persona guard |
| `agent/tools.py` | 96% | 16 | 12 | MS Graph error handling |

† Measured with the `omit` removed; it does not appear in the default report at
all.

## Suggested order

1. **Settle the two decisions** — findings 2 and 3. Does the hardening subsystem
   ship or go? Does section 6 of the guardrails earn its place? Both change what
   you would write tests for.
2. **Un-omit the Telegram bot and test its auth** — finding 1. Highest
   risk-per-line-of-test in the repo.
3. **Write the web-auth rejection matrix** — finding 4. One parametrized test
   closes most of `web/server.py`.
4. **Cover the deployment env readers** — finding 5. Cheap, and it completes the
   deployment path started in step 2.
5. **Test parallel failure in the team engine** — finding 6. Most likely to save
   a future intermittent-CI investigation.
6. **Pin the shared-package divergence** — finding 7.
7. **Re-set the floor and refresh the docs** — finding 8, last, once the real
   number has moved.

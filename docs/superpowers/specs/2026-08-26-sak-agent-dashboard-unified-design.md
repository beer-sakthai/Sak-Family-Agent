# Sak Agent Dashboard — Unified System Design

**Date:** 2026-08-26
**Status:** Design
**Plan:** [`docs/superpowers/plans/2026-08-26-sak-agent-dashboard-unified.md`](../plans/2026-08-26-sak-agent-dashboard-unified.md)
**Supersedes nothing.** Builds on
[`2026-08-03-sakthai-web-auth-design.md`](./2026-08-03-sakthai-web-auth-design.md),
which established the bearer-token model this design extends.

---

## 1. Problem

Three subsystems exist that should be one system, and none of them know about
each other.

| Piece | Where | State |
|---|---|---|
| The agents | `personas/sakthai/sakthai/` | Six personas, writing runtime state to `~/.sakthai/` |
| The dashboard | `apps/sak_agent_dashboard/` | Next 16 + React 19 + Recharts, reads `~/.sakthai/` directly |
| The workflow engine | `apps/agent_workflow_framework/` | Stdlib DAG executor, runs stored relative to cwd |

The gaps are concrete, not aesthetic:

**1. The dashboard invents its persona data.** Neither `eval.jsonl` nor the
session logs carry a persona field. `src/lib/sakthai.ts:getPersonaIndexForRun()`
therefore guesses: it looks for `thai`/`king`/`see`/`sit`/`jules` in an optional
`entry.persona`, then falls back to matching the *model name*
(`claude`→SakThai, `gpt`→SakKing, `gemini`→SakSee, `llama`→SakSit,
`qwen`→SakJules), then finally to `index % 5` round-robin. Every per-persona
number on the dashboard is fabricated. The same file hardcodes **five**
personas; `config.PERSONA_NAMES` has **six** — SakTan is simply absent.

**2. Two parsers, two path conventions, no shared contract.** Python resolves
runtime state through `config.sakthai_home()` (honouring `$SAKTHAI_HOME`). The
TypeScript side hardcodes `process.env.SAKTHAI_DIR || ~/.sakthai` in *two*
separate modules (`src/lib/sakthai.ts`, `src/lib/db.ts`). The environment
variable names do not even match. Both sides parse the same four file formats
independently, and nothing detects when one drifts from the other.

**3. The Python API is not consumable.** `web/server.py` is a stdlib
`http.server` exposing three GET endpoints — `/health`, `/api/stages`,
`/api/ecosystem`. It has no CORS headers at all, its static root
(`dashboard/dist`) does not exist, and there is **no `sakthai web serve`
command**: the only way to start it is `python personas/sakthai/sakthai/web/server.py`.
Everything a dashboard actually wants — sessions, eval metrics, audit events,
per-persona memory — is reachable only from Python or the CLI.

**4. `apps/` is invisible to CI.** `ci.yml` scopes ruff, mypy, bandit, pytest
and coverage to `personas/sakthai/sakthai` and `tests/`; `pyproject.toml` sets
`testpaths = ["tests"]` and `mypy.files = ["personas/sakthai/sakthai"]`. No
workflow runs `next build`, `vitest`, or the framework's pytest. Dependabot
opens npm PRs against the dashboard that nothing verifies.

**5. The workflow framework is an island.** Zero imports outside its own
directory. No `pyproject.toml`, no console script, not a build target. Run
history lands in `.workflow_runs/` **relative to the current working
directory**, so nothing else can reliably find it.

---

## 2. Goals and non-goals

**Goals**

- One data contract, defined once, that both runtimes agree on by construction.
- An HTTP API that exposes what the dashboard needs, built by *reusing* the
  existing parsers rather than writing second copies.
- A dashboard that reads local state directly when it can, and falls back to
  that API when it cannot — and always says which it did.
- Honest persona attribution, fixed at the point of writing rather than guessed
  at the point of reading.
- Workflow runs visible next to agent runs.
- CI that builds and tests all three pieces.

**Non-goals**

- Replacing the stdlib `http.server` with a framework. It is small, audited,
  and loopback-bound; swapping it in would invalidate the existing web-auth
  security work for no benefit here.
- Making the workflow framework an installed `sakthai` subpackage.
- Any write path. The API stays GET-only and read-only.
- A hosted deployment. See §9.

---

## 3. The contract

**Decision: Python `TypedDict`s are the source of truth. The TypeScript types
are generated from them. CI fails if the generated file is stale.**

Alternatives weighed:

| Option | Why not |
|---|---|
| Hand-kept parallel types | This is exactly how we got five personas on one side and six on the other. Drift is silent and unbounded. |
| OpenAPI + codegen | Real machinery (spec file, generator, runtime validation) for a 355-line stdlib server with seven read-only endpoints. The spec becomes a third artifact to keep in sync. |
| JSON Schema as source | Neither runtime reads it natively; both sides still need generated types, and mypy-strict cannot check against it. |

Generation from `TypedDict`s wins because Python is already the writer of every
byte of this data, `mypy --strict` checks the definitions for free, and the
generator is a testable ~150-line script whose output diff is a hard CI signal.

### 3.1 Module

`personas/sakthai/sakthai/web/contracts.py` — pure types, no logic, no imports
beyond `typing`.

```python
class ApiEnvelope(TypedDict):
    ok: bool
    source: Literal["local", "api", "demo"]
    generated_at: str      # ISO-8601 UTC
    data: object
```

Every endpoint returns an envelope. `source` is carried all the way to the UI so
the dashboard can never again present demo data as real — the single most
important property of this design.

Payload types: `PersonaSummary`, `MetricsSummary`, `TrendPoint`, `TokenStats`,
`SessionSummary`, `SessionDetail`, `SessionMessage`, `MemoryPayload`,
`FactRecord`, `ObservationRecord`, `AuditEvent`, `WorkflowRunSummary`,
`WorkflowRunDetail`, `WorkflowStepResult`.

### 3.2 Generator

`scripts/gen_dashboard_types.py` emits
`apps/sak_agent_dashboard/src/lib/contracts.generated.ts` with a DO-NOT-EDIT
banner. It must `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`
before importing — there is no root-level `sakthai/` package, per the repo's
script convention.

Output is deterministic (declaration order preserved, no timestamps in the
banner) so `git diff --exit-code` is a valid staleness check.

### 3.3 Persona attribution

`PersonaSummary.name` is one of `config.PERSONA_NAMES` **or the literal
`"unattributed"`**. Records written before this change carry no persona, and
the honest representation of "we do not know who ran this" is a named bucket,
not a round-robin guess. `getPersonaIndexForRun()` is deleted outright.

---

## 4. The API

`web/server.py` stays a thin HTTP dispatcher. All payload construction moves to
a new pure module, `personas/sakthai/sakthai/web/api.py`, so it can be unit
tested without a socket — the same reason `mcp/server.py:handle_request` is a
pure function.

### 4.1 Endpoints

| Path | Backed by | Reuses |
|---|---|---|
| `/health` | unchanged | — |
| `/api/stages` | unchanged (back-compat) | `dashboard/data.py` |
| `/api/ecosystem` | unchanged (back-compat) | — |
| `/api/personas` | `personas_payload()` | `config.PERSONA_NAMES`, `persona_model_defaults()`, `persona_memory_db_path()`, `MemoryStore.stats()` |
| `/api/metrics?limit=N` | `metrics_payload()` | `agent.eval.summarize_evals()` |
| `/api/sessions?search=&limit=&offset=&id=` | `sessions_payload()` | the readers behind `cli/sessions.py`, `search_sessions()` |
| `/api/memory?query=&persona=` | `memory_payload()` | `memory.merged.FamilyMemoryView`, `MemoryStore.search_memory()`, `store.get_dashboard_aggregates()` |
| `/api/audit?severity=` | `audit_payload()` | new JSONL reader for `sakthai_home()/audit.log` |
| `/api/workflows` | `workflows_payload()` | §7 |
| `/api/workflows/<run_id>` | `workflow_detail()` | §7 |

**No parser is written twice.** `metrics_payload` wraps `summarize_evals()`
rather than re-reading `eval.jsonl`; `memory_payload` uses
`store.get_dashboard_aggregates()`, which already computes the 30-bin growth
series that `dashboard/data.py` today returns permanently empty.

### 4.2 Auth and CORS

Auth is unchanged: `/health` is open, everything else requires the bearer token
resolved by `_get_or_create_bearer_token()` (stored as a `web_auth` fact in
`memory.db`, managed with `sakthai web setup` / `web regen-token`).

CORS is **opt-in and exact-match only**, via `SAKTHAI_WEB_CORS_ORIGIN`:

- Unset (the default) → no CORS headers, behaviour byte-identical to today.
- Set → `Access-Control-Allow-Origin` echoes the configured origin **only when
  the request's `Origin` matches it exactly**. Never `*`.
- `Access-Control-Allow-Credentials` is **not** set. The bearer token travels in
  the `Authorization` header, so credentialed CORS is unnecessary — and setting
  it would expose the cookie auth path (`Cookie: token=`) to cross-origin use.
- `do_OPTIONS` answers preflight with `Allow-Methods: GET, OPTIONS` and
  `Allow-Headers: Authorization`.

This exists so `next dev` on :3000 can call the API on :3001 during local
development. It is not a production posture; the loopback guard and
`SAKTHAI_WEB_ALLOW_PUBLIC` opt-in are unchanged.

### 4.3 Serving

`sakthai web serve [--host 127.0.0.1] [--port 3001]` is added to the `web` group
in `cli/system.py`, calling the existing `serve()`. Today that group has only
`setup` and `regen-token` — the server has no CLI entry point at all.

---

## 5. Persona attribution, fixed at the source

`run_agent()` already accepts `persona: str | None` (`agent/loop.py:415`). It
simply never records it. The fix is small and backward-compatible:

- `EvalRecord` gains `persona: str | None = None` as a **trailing defaulted
  field**. `asdict()` picks it up automatically; `_read_records()` returns plain
  dicts, so legacy lines missing the key read back as `None`.
- `_save_session_log()` gains a `persona` parameter and writes a `"persona"`
  key. Two call sites (`loop.py:549`, `loop.py:567`).

The log is append-only. Mixed records — some with a persona, some without — are
the expected steady state, and the `"unattributed"` bucket is how they surface.
No migration, no rewrite of existing files.

### 5.1 Sharded runtime state

In production each persona runs with `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`
(`infra/vm-agents/sakthai-agent-run.sh`), so that persona's `sessions/`,
`eval.jsonl` and `audit.log` live **under its own shard**, not the unscoped
root. Any reader that scans only `~/.sakthai/sessions/` sees local dev runs and
nothing else.

Both `personas_payload()` and the TypeScript local source must therefore scan
the unscoped root *and* each `~/.sakthai/<persona>/` shard, exactly as
`FamilyMemoryView` already does for `memory.db`.

---

## 6. The hybrid data layer

The dashboard needs to work in two environments that share no filesystem:
a developer's machine, where `~/.sakthai/` is right there, and a hosted deploy,
where it does not exist.

**One seam, three implementations:**

```ts
interface DashboardSource {
  getPersonas(): Promise<...>;  getMetrics(): Promise<...>;
  getSessions(q): Promise<...>; getMemory(q): Promise<...>;
  getAudit(q): Promise<...>;    getWorkflows(): Promise<...>;
}
```

`resolveSource(request)` picks one, in order:

1. explicit `?demo=1` → `DemoSource`
2. `SAKTHAI_API_URL` set → `ApiSource` (bearer from `SAKTHAI_API_TOKEN`)
3. otherwise → `LocalFsSource`, which degrades to `DemoSource` **only** when the
   runtime directory is genuinely absent

Every response reports its `source`. A blanket `try/catch → demo` — which is
what all four routes do today — is what let a broken SQLite path serve
plausible fake memory data indefinitely.

**Environment variables** are read in exactly one place. `SAKTHAI_HOME` is
preferred, matching Python; `SAKTHAI_DIR` is retained as a deprecated alias so
existing setups keep working.

**Demo data is defined once**, in `src/lib/demo.ts`. It currently exists three
times — in `lib/sakthai.ts` (`benchmarkScore: 0.96`), in `app/page.tsx`
(`benchmarkScore: 96.5`), and inline in `src/tests/api.test.ts` — with the same
field on two different scales, rendered without normalisation.

### 6.1 Tests that can fail

The existing suite cannot detect a regression, for two structural reasons:

```ts
async function getApiRouteModule(routePath: string) {
  try { return await import(`../app/api/${routePath}/route`); } catch { return null; }
}
```

Every assertion in `api.test.ts` and `components.test.tsx` is wrapped in
`if (module) … else <assert on an inline literal>`. When the import fails, the
test asserts against a local object and reports green. And
`integration.test.ts:2` imports its types **from `./api.test`**, pulling that
file's twelve `describe` blocks into a second module graph so they execute twice.

Both go. Types come from `contracts.generated.ts`. Tests point `SAKTHAI_HOME` at
a seeded fixture tree so the **SQLite path actually executes** — today
`db.ts` calls CommonJS `require("better-sqlite3")` inside an ESM module, which
throws under Vitest and is swallowed into the demo fallback, meaning that code
has never once run under test.

---

## 7. Workflow runs

**Decision: relocate the run store under `~/.sakthai/workflow_runs/`. Do not
package the framework into `sakthai`.**

| Option | Assessment |
|---|---|
| Leave runs cwd-relative | The dashboard cannot reliably locate them. Rejected. |
| Make it a `sakthai` subpackage | Drags a 540-line executor and its own duplicated security helper under `mypy --strict` and the 96% branch floor. Large change, no dashboard benefit. Rejected. |
| **Relocate the default store** | One-line default change; puts workflow runs in the same well-known root as every other piece of runtime state. **Chosen.** |

`config.workflow_runs_dir()` → `sakthai_home() / "workflow_runs"`, alongside
`sessions_dir()`. `RunHistoryStore.DEFAULT_STORAGE_DIR` resolves to
`$SAKTHAI_HOME/workflow_runs` (or `~/.sakthai/workflow_runs`), falling back to
the current cwd-relative `.workflow_runs` when home resolution fails. The
framework reads the environment variable directly and does **not** import
`sakthai`, so it stays stdlib-only and independently runnable.

**Deferred, deliberately:** `executor.py:_validate_filepath()` duplicates path
validation that `agent/guardrails.py` already owns — a second, independently
maintained implementation of the repo's most attacked logic. Converging them
means bringing the framework under `tests/test_persona_guardrails_parity.py`
and the guardrails suite. That is real work and a real risk, and it is not a
prerequisite for displaying run history. It is recorded here so it is not lost.

---

## 8. CI

A new `.github/workflows/apps.yml` with `paths:` filters, so it stays off every
Python change:

- **dashboard** — `paths: apps/sak_agent_dashboard/**`. `npm ci` → `npm run lint`
  → `npm run build` → `tsc --noEmit` → `npm test`. Typecheck runs *after* build
  because `next-env.d.ts` imports `./.next/types/*.d.ts`, which only exists once
  a build has generated it.
- **workflow-framework** — `paths: apps/agent_workflow_framework/**`.
  `python -m pytest apps/agent_workflow_framework/tests`. Kept separate from the
  main suite, whose `testpaths = ["tests"]` deliberately excludes it.
- **contracts** — regenerates the TS types and `git diff --exit-code`.

**Lockfiles.** The dashboard commits both `package-lock.json` *and*
`pnpm-lock.yaml`, plus a nested `pnpm-workspace.yaml` declaring its own pnpm
workspace root inside `apps/`. Nothing declares which is authoritative, and
Dependabot updates only one. Keep npm (Dependabot is already configured for it
at `.github/dependabot.yml:38`), delete the pnpm pair, add `packageManager` and
`engines`.

**Build blockers** fixed in `next.config.mjs`: `swcMinify` was removed after
Next 14 and this is Next 16 (currently an invalid-config warning);
`better-sqlite3` needs `serverExternalPackages` so a native `.node` addon is not
bundled into a route handler.

---

## 9. Deployment, stated plainly

There is no hosted API and no `vercel.json`. On a hosted deploy the app has no
`~/.sakthai/`, so it runs in `ApiSource` mode against a reachable API, or in
`DemoSource` mode. Local end-to-end is `make dashboard-dev`: `sakthai web serve`
on :3001 and `next dev` on :3000 with `SAKTHAI_API_URL` and `SAKTHAI_API_TOKEN`
from `sakthai web setup`.

This design does not create a production deployment and does not imply one
exists.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Coverage floor is `fail_under = 96` with the suite at ~96.0–96.6% — almost no headroom | Every branch in `web/api.py` ships with its test in the same phase. `api.py` is pure functions specifically to make this cheap. |
| CORS widens the attack surface | Off by default; exact-match origin only; never `*`; credentials never allowed. Loopback guard unchanged. |
| Persona field breaks eval log readers | Trailing defaulted field; readers use `.get()`; mixed records are the designed steady state. |
| Relocating the workflow store orphans existing runs | The directory was emptied in the 2026-08-08 cleanup and is gitignored; the cwd-relative fallback remains. |
| Guardrails parity test | Nothing in this design touches `agent/guardrails.py`. |

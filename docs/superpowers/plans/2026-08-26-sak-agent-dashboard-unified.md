# Sak Agent Dashboard — Unified System Implementation Plan

**Goal:** Unify the three islands in this repo — the agent package
(`personas/sakthai/sakthai/`), the Next.js dashboard
(`apps/sak_agent_dashboard/`), and the workflow engine
(`apps/agent_workflow_framework/`) — into one system with a single shared data
contract, a consumable HTTP API, honest persona attribution, and CI coverage,
per the approved design at
[`docs/superpowers/specs/2026-08-26-sak-agent-dashboard-unified-design.md`](../specs/2026-08-26-sak-agent-dashboard-unified-design.md).

**Architecture:** Python `TypedDict`s in a new `sakthai/web/contracts.py` are the
single source of truth for every payload shape; `scripts/gen_dashboard_types.py`
generates the TypeScript equivalents and CI fails on drift. A new pure module
`sakthai/web/api.py` builds those payloads by *reusing* the existing parsers
(`summarize_evals`, the `cli/sessions.py` readers, `FamilyMemoryView`,
`store.get_dashboard_aggregates`) — no parser is written twice. `web/server.py`
stays a thin HTTP dispatcher. On the TypeScript side a single `DashboardSource`
seam picks between local filesystem reads, the HTTP API, and demo data, and
every response reports which it used.

**Tech Stack:** Python 3.11/3.12, stdlib `http.server`, Click, pytest, mypy
strict, ruff, bandit, uv · Next 16, React 19, TypeScript 6, Tailwind 3,
Recharts 3, Vitest 4, npm.

## Global Constraints

- `mypy strict = true` over `personas/sakthai/sakthai` — every new function fully
  annotated. `sakthai.telegram.*` is the only exemption and we are not touching it.
- Ruff: line-length 100, rules `["E","F","W","I","UP","B","SIM"]` (E501, SIM108
  ignored), `exclude = ["library","scripts"]` — so `scripts/gen_dashboard_types.py`
  is not linted, but keep it clean anyway.
- **Coverage floor is `fail_under = 96`** with branch coverage on, and the suite
  sits at ~96.0–96.6%. There is almost no headroom: every branch added to
  `web/api.py` must ship with its test in the same commit. This is why `api.py`
  is pure functions with no HTTP or I/O setup in them.
- Tests are hermetic — no network, no real `~/.sakthai`. Use the existing
  `sakthai_home` fixture (`tests/conftest.py:23`, monkeypatches `SAKTHAI_HOME`
  to a `tmp_path`) and the `store` fixture (`tests/conftest.py:14`).
- `apps/` is outside `testpaths`, `mypy.files`, and `coverage.source`. Keep it
  that way — the new CI job covers it separately.
- Do not touch `personas/sakthai/sakthai/agent/guardrails.py`;
  `tests/test_persona_guardrails_parity.py` fails CI on any drift across the
  five persona copies.
- **Never overwrite `PLAN.md` wholesale** — targeted chunk replacements only,
  then re-read to verify the surrounding content is intact (CLAUDE.md rule).
- Commit style: short imperative subject with a `feat:`/`fix:`/`docs:`/`test:`
  prefix, matching recent history.

---

## Phase 0 — Architecture documents

- [x] Design spec at `docs/superpowers/specs/2026-08-26-sak-agent-dashboard-unified-design.md`
- [x] This plan
- [ ] `docs/architecture.md` — add the HTTP API + Next.js dashboard + workflow
      runs layer above the CLI box; delete the stale `dashboard/` paragraph that
      still describes a **Streamlit** app (`app.py`) which no longer exists.
- [ ] `PLAN.md` — three targeted edits: fix the dead `| **Web dashboard** |
      dashboard/ |` link in *Where Things Live* to `apps/sak_agent_dashboard/`,
      append a *Current Status* row, append a *Sub-Plans* row pointing here.

**Verification:** links resolve to files that exist; `PLAN.md` re-read after
each chunk replacement.

---

## Phase 1 — One contract, defined once

- [ ] **New** `personas/sakthai/sakthai/web/contracts.py` — `TypedDict`s only,
      no logic: `ApiEnvelope` (`ok`, `source: Literal["local","api","demo"]`,
      `generated_at`, `data`), `PersonaSummary`, `TokenStats`, `TrendPoint`,
      `MetricsSummary`, `SessionMessage`, `SessionSummary`, `SessionDetail`,
      `FactRecord`, `ObservationRecord`, `MemoryPayload`, `AuditEvent`,
      `WorkflowStepResult`, `WorkflowRunSummary`, `WorkflowRunDetail`.
- [ ] **New** `scripts/gen_dashboard_types.py` — emits
      `apps/sak_agent_dashboard/src/lib/contracts.generated.ts` with a
      DO-NOT-EDIT banner. Deterministic output (declaration order preserved, no
      timestamp) so `git diff --exit-code` is a valid staleness check. Must
      `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` — there is no
      root-level `sakthai/` package.
- [ ] **New** `tests/test_web_contracts.py` — generator output is deterministic
      across two runs; every `TypedDict` maps to a TS interface; the committed
      generated file matches a fresh generation.

**Verification:** `uv run pytest tests/test_web_contracts.py -q`,
`uv run mypy personas/sakthai/sakthai`,
`python scripts/gen_dashboard_types.py && git diff --exit-code`.

---

## Phase 2 — A Python API worth consuming

- [ ] **New** `personas/sakthai/sakthai/web/api.py` — pure payload builders, each
      returning a `contracts.py` type, each taking an injectable store/path so it
      is testable without touching a real home:
      - `personas_payload(...)` — `config.PERSONA_NAMES` (**all six**),
        `persona_model_defaults()`, `persona_memory_db_path()` for shard
        presence, counts from `MemoryStore.stats()`. Must scan the unscoped root
        **and** each `~/.sakthai/<persona>/` shard (production sets
        `SAKTHAI_HOME=$HOME/.sakthai/$AGENT` per persona).
      - `metrics_payload(limit)` — wraps `agent.eval.summarize_evals()`, adds
        daily trend bins. Does not re-read `eval.jsonl` itself.
      - `sessions_payload(search, limit, offset, session_id)` — reuses the
        readers behind `cli/sessions.py` / `search_sessions()`.
      - `memory_payload(query, persona)` — `FamilyMemoryView`,
        `MemoryStore.search_memory()`, and `store.get_dashboard_aggregates()`
        for the growth series `dashboard/data.py` returns permanently empty.
      - `audit_payload(severity)` — new JSONL reader for
        `sakthai_home()/audit.log` (`{timestamp, type, severity, message, details}`,
        written by `agent/security_hardening.py:AuditLogger`).
- [ ] **Edit** `web/server.py` — add `/api/personas`, `/api/metrics`,
      `/api/sessions`, `/api/memory`, `/api/audit` to the `do_GET` dispatch chain
      (currently `server.py:289-304`). `/health`, `/api/stages`, `/api/ecosystem`
      unchanged.
- [ ] **Edit** `web/server.py` — opt-in CORS via `SAKTHAI_WEB_CORS_ORIGIN`:
      exact-match origin only, never `*`, `Allow-Credentials` **never** set (the
      token is in the `Authorization` header; allowing credentials would expose
      the `Cookie: token=` path cross-origin). Add `do_OPTIONS` for preflight.
      Unset → no CORS headers, byte-identical to today.
- [ ] **Edit** `cli/system.py` — add `sakthai web serve [--host] [--port]` to the
      `web` group, calling the existing `serve()`. Loopback guard and
      `SAKTHAI_WEB_ALLOW_PUBLIC` unchanged.
- [ ] **New** `tests/test_web_api.py` + additions to `tests/test_web_server.py`
      and `tests/test_web_auth.py` — payload shapes, empty-state and
      missing-file branches, route dispatch, auth on each new path (401 without
      credentials / 403 with wrong ones / 200 with right), CORS on and off,
      preflight.

**Verification:** full local gate — `uv run pytest tests/ -q`,
`ruff check`, `ruff format --check`, `mypy`, `bandit`. Coverage ≥ 96%.

---

## Phase 3 — Persona attribution, fixed at the source

- [ ] **Edit** `agent/eval.py` — `EvalRecord` gains `persona: str | None = None`
      as a **trailing defaulted field**. `asdict()` picks it up; `_read_records()`
      returns dicts so legacy lines read back `None`. Append-only log, no migration.
- [ ] **Edit** `agent/loop.py` — pass `persona=persona` into the `EvalRecord(...)`
      construction (`loop.py:475`); add a `persona` parameter to
      `_save_session_log()` (`loop.py:704`) and a `"persona"` key in its payload;
      update both call sites (`loop.py:549`, `loop.py:567`). `run_agent()` already
      takes `persona: str | None` (`loop.py:415`).
- [ ] **Tests** — `tests/test_eval.py` and `tests/test_agent_loop.py`: a record
      written with a persona round-trips; a legacy line without the key parses
      to `None`; `--persona X` reaches both the eval log and the session file.

**Verification:** `uv run pytest tests/test_eval.py tests/test_agent_loop.py -q`,
then the full gate.

---

## Phase 4 — The hybrid data layer (TypeScript)

- [ ] **New** `src/lib/source.ts` — `DashboardSource` interface
      (`getPersonas/getMetrics/getSessions/getMemory/getAudit/getWorkflows`) and
      `resolveSource(request)`: `?demo=1` → demo; `SAKTHAI_API_URL` set → api;
      else local, degrading to demo **only** when the runtime dir is absent.
- [ ] **New** `src/lib/sources/{local,api,demo}.ts` — `LocalFsSource` is today's
      `lib/sakthai.ts` + `lib/db.ts` behind the interface, plus an mtime-keyed
      cache for the sessions directory (currently an unbounded sync
      `readdir`+`readFile`+`parse` on *every* request). `ApiSource` fetches the
      Phase 2 endpoints with `SAKTHAI_API_TOKEN` as a bearer header.
- [ ] **Env reconciliation** — resolve the runtime root in **one** place, reading
      `SAKTHAI_HOME` first (matching Python) with `SAKTHAI_DIR` kept as a
      deprecated alias. It is currently hardcoded in two modules under the
      non-matching name.
- [ ] **New** `src/lib/demo.ts` — the single demo dataset. Delete the rival
      copies in `lib/sakthai.ts` (`benchmarkScore: 0.96`) and `app/page.tsx`
      (`defaultPersonas`, `benchmarkScore: 96.5`) — the same field on two scales,
      rendered without normalisation.
- [ ] **Edit** `src/lib/sakthai.ts` — **delete `getPersonaIndexForRun()`**.
      Records with a `persona` are attributed to it; the rest go to an explicit
      `"unattributed"` bucket the UI labels as such. Persona list comes from the
      contract, not a 5-element TS literal.
- [ ] **Edit** the four `src/app/api/*/route.ts` → thin
      `resolveSource(request).getX()`; add `api/audit/route.ts`; add
      `export const dynamic = "force-dynamic"` and `export const runtime = "nodejs"`
      to all (they touch `fs` and a native addon; none declares either today).
- [ ] **Tests** — remove the `if (module loaded) … else assert-on-inline-literal`
      escape hatch in `src/tests/api.test.ts` and `components.test.tsx` (green
      when the import fails); remove `import … from "./api.test"` at
      `integration.test.ts:2` (re-registers 12 tests twice). Point `SAKTHAI_HOME`
      at a seeded fixture tree so the **SQLite path actually executes** —
      `db.ts`'s CommonJS `require("better-sqlite3")` throws under Vitest's ESM
      and is swallowed into the demo fallback, so it has never run under test.
      Convert to a typed import; bump `@types/better-sqlite3` `^9` → `^13`.

**Verification:** `npm test` with a deliberately broken import must turn the
suite **red**; both source modes exercised against the fixture tree.

---

## Phase 5 — Workflow runs on the dashboard

- [ ] **Edit** `personas/sakthai/sakthai/config.py` — add `workflow_runs_dir()`
      → `sakthai_home() / "workflow_runs"`, next to `sessions_dir()`.
- [ ] **Edit** `apps/agent_workflow_framework/agent_workflow/persistence.py` —
      `RunHistoryStore.DEFAULT_STORAGE_DIR` resolves to
      `$SAKTHAI_HOME/workflow_runs` (or `~/.sakthai/workflow_runs`), falling back
      to the cwd-relative `.workflow_runs` when home resolution fails. Read the
      env var directly — **no `sakthai` import**, the framework stays stdlib-only.
- [ ] **Edit** `web/api.py` + `web/server.py` — `workflows_payload()` and
      `workflow_detail(run_id)`; routes `/api/workflows` and
      `/api/workflows/<run_id>`. Run ids are already sanitised against traversal
      by `persistence.py`; validate again at the route boundary.
- [ ] **New** `src/components/WorkflowRuns.tsx` — run list with status pills and
      a step-level detail modal reusing `SessionExplorer`'s modal pattern.

**Deferred (recorded, not dropped):** `executor.py:_validate_filepath()`
duplicates path validation `agent/guardrails.py` already owns. Converging them
means bringing the framework under the parity test and the guardrails suite —
separate work, not a prerequisite for displaying run history.

---

## Phase 6 — CI and deployment

- [ ] **New** `.github/workflows/apps.yml`, `paths:`-filtered so it stays off
      every Python change:
      - `dashboard` — `apps/sak_agent_dashboard/**`: `npm ci` → `npm run lint`
        → `npm run build` → `tsc --noEmit` → `npm test`. Typecheck runs **after**
        build because `next-env.d.ts` imports `./.next/types/*.d.ts`, which only
        exists once a build has generated it.
      - `workflow-framework` — `apps/agent_workflow_framework/**`:
        `python -m pytest apps/agent_workflow_framework/tests`.
      - `contracts` — regenerate the TS types, `git diff --exit-code`.
- [ ] **Lockfiles** — keep `package-lock.json`; delete `pnpm-lock.yaml` and the
      nested `pnpm-workspace.yaml` (which declares its own pnpm workspace root
      inside `apps/`). Dependabot is already configured for npm there
      (`.github/dependabot.yml:38`). Add `"packageManager"` and `"engines"`.
- [ ] **Build blockers** in `next.config.mjs` — drop `swcMinify` (removed after
      Next 14; this is Next 16, so it is an invalid-config warning today); add
      `serverExternalPackages: ["better-sqlite3"]` so the native addon is not
      bundled into a route handler.
- [ ] **`make dashboard-dev`** — `sakthai web serve` on :3001 and `next dev` on
      :3000 with `SAKTHAI_API_URL` / `SAKTHAI_API_TOKEN`. Document in
      `docs/workspace.md`.

**Deployment, stated plainly:** there is no hosted API and no `vercel.json`. On
a hosted deploy the app has no `~/.sakthai/`, so it runs in api mode against a
reachable API or in demo mode. This plan does not create a production deployment.

---

## Phase 7 — Scoped cleanup

**In scope** — each is a build blocker or a correctness lie:

- [ ] `AnalyticsCharts.tsx:42` — `Math.floor(Math.random() * 15 + 85)` as a
      fallback score makes the render non-deterministic.
- [ ] `?limit=abc` → `Math.max(1, NaN)` → `slice(0, NaN)` → silently empty page,
      still HTTP 200.
- [ ] `lib/db.ts` — `db.close()` skipped on the outer-catch path.
- [ ] `page.tsx` never sends the `severity`/`query` params its own API supports —
      dead server-side filtering.
- [ ] Remove `@google/stitch-sdk` (**zero imports** anywhere in `src/`) and the
      272-line hardcoded `StitchStudio.tsx` it exists for.
- [ ] Rewrite `TEST_INFRA.md` / `TEST_READY.md`, which claim Vitest 2, Next 14,
      and "4 files, 28 tests, exit code 0" against an actual Vitest 4, Next 16,
      5 files, 37 tests.

**Explicitly deferred:** the `.agents/` orchestration markdown; the
`personas/sakthai/sakthai` vs `personas/shared/sakthai` divergence; converging
the framework's path validation with the guardrails; `error.tsx`/`loading.tsx`/
`not-found.tsx` boundaries.

---

## Verification (end to end)

There is no `~/.sakthai` in a fresh container, so everything runs against a
seeded fixture root.

1. Seed `SAKTHAI_HOME=<tmp>/sakthai-fixture` with a real-schema `eval.jsonl`
   (**mixed**: some lines with `persona`, some legacy without), a few
   `sessions/*.json`, an `audit.log`, and a `memory.db` built through
   `MemoryStore` itself.
2. `uv run pytest tests/ -q` · `ruff check` · `ruff format --check` · `mypy` ·
   `bandit`. Coverage ≥ **96%** branch.
3. `sakthai web setup` for the token, `sakthai web serve`, then curl each
   endpoint: `/health` open; every `/api/*` 401 without credentials, 403 with
   wrong ones, 200 with the right one.
4. `python scripts/gen_dashboard_types.py && git diff --exit-code`.
5. `npm ci` · `npm run lint` · `npm run build` · `tsc --noEmit` · `npm test`.
6. `next dev` against the fixture (local mode), then against the running Python
   server (api mode); each route reports the correct `source` and both modes
   agree on the persona numbers.
7. `sakthai run --persona saksee "…"` → the new `eval.jsonl` line and session
   file carry `"persona": "saksee"`; the dashboard attributes it to SakSee while
   legacy lines land in `unattributed`.
8. A sample workflow run lands in `$SAKTHAI_HOME/workflow_runs/` and appears on
   `/api/workflows` and in the UI.
9. Push; `apps.yml` fires only on `apps/**` changes and `ci.yml` stays green.

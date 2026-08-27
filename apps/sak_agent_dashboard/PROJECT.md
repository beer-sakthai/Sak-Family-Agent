# Project: Sak-Agent-Family Dashboard

Read-only analytics UI over the SakThai agent family's runtime state.

## Architecture

- **Framework:** Next.js 16 (App Router) + React 19 + TypeScript 6
- **Styling:** Tailwind CSS 3, Inter & Outfit via `next/font/google`, dark
  glassmorphism (`#090d16` background, `bg-slate-900/80` cards)
- **Charts:** Recharts 3
- **Tests:** Vitest 4 + React Testing Library — see [`TESTING.md`](./TESTING.md)

### Data layer

One seam, `src/lib/source.ts`, with three implementations. `resolveSource()`
picks per request:

1. explicit `?demo=1` → `DemoSource`
2. `SAKTHAI_API_URL` set → `ApiSource` (the SakThai HTTP API; the hosted case)
3. otherwise → `LocalFsSource` reading `~/.sakthai/` directly, degrading to
   `DemoSource` only when the runtime directory genuinely is not there

Every response carries which source answered, and the header renders it, so
sample data can never be mistaken for live data.

Both `LocalFsSource` and the Python API walk the unscoped runtime root **and**
each `~/.sakthai/<persona>/` shard, because every deployed persona runs with its
own `SAKTHAI_HOME`.

### The contract

`src/lib/contracts.generated.ts` is generated from
`personas/sakthai/sakthai/web/contracts.py` by `scripts/gen_dashboard_types.py`.
That Python module is the single definition of every payload; CI regenerates the
TypeScript and fails on a diff. Do not edit the generated file.

## Environment

| Variable | Purpose |
|---|---|
| `SAKTHAI_HOME` | Runtime root (default `~/.sakthai`). Matches the Python package. |
| `SAKTHAI_DIR` | Deprecated alias for `SAKTHAI_HOME`. |
| `SAKTHAI_API_URL` | Base URL of a running `sakthai web serve`. Set it to use `ApiSource`. |
| `SAKTHAI_API_TOKEN` | Bearer token for that API, from `sakthai web setup`. |

## Routes

| Route | Payload |
|---|---|
| `/api/agents` | `PersonasPayload` — all six personas plus an unattributed-run count |
| `/api/metrics` | `MetricsPayload` — runs, latency, tokens, stop reasons, daily trends |
| `/api/sessions` | `SessionsPayload` — summaries; `?id=` adds one transcript |
| `/api/memory` | `MemoryPayload` — facts and observations merged across shards |
| `/api/audit` | `AuditPayload` — security events from `audit.log` |
| `/api/workflows` | `WorkflowsPayload` — `agent_workflow` runs; `?id=` for one run |

All are `runtime = "nodejs"` and `dynamic = "force-dynamic"`: they read the
filesystem and a native SQLite addon, and serve live state.

## Code layout

```
src/
├── app/
│   ├── layout.tsx · page.tsx · globals.css
│   └── api/{agents,metrics,sessions,memory,audit,workflows}/route.ts
├── components/
│   ├── shell/Sidebar.tsx · shell/TopBar.tsx      (the app chrome)
│   ├── CommandPalette.tsx · KpiStrip.tsx
│   ├── Skeletons.tsx · HostedNotice.tsx
│   ├── AgentCard.tsx · AgentOverview.tsx · AnalyticsCharts.tsx
│   ├── SessionExplorer.tsx · MemoryExplorer.tsx · AuditLogs.tsx
│   └── WorkflowRuns.tsx · DemoModeToggle.tsx · StitchStudio.tsx
├── lib/
│   ├── contracts.generated.ts   (generated — do not edit)
│   ├── source.ts · runtime.ts · demo.ts · db.ts
│   ├── nav.ts · format.ts · browser-state.ts
│   └── sources/{local,api,demo}.ts
└── tests/
```

### The shell

`layout.tsx` renders the document and an inert ambient background, nothing
else. All the chrome — sidebar, topbar, command palette — is composed in
`page.tsx`, because it is driven by the same client state as the panels it
frames. `lib/nav.ts` is the single definition of the seven sections; the
sidebar, the topbar heading, the command palette and the keyboard shortcuts
all read it.

Two pieces of state live in the browser rather than in React, and
`lib/browser-state.ts` reads both through `useSyncExternalStore` so the server
snapshot and the hydrating client agree:

- **the active section** is the URL fragment (`#memory`), so a section is
  linkable and the back button moves between them;
- **sample-data mode, sidebar collapse and the auto-refresh interval** are
  `localStorage` preferences, so they survive a reload.

Keyboard: `⌘K`/`Ctrl+K` opens the palette, `R` refreshes. Both are suppressed
while a text field has focus.

## Local development

From the repository root:

```bash
make dashboard-dev    # the Python API on :3001 and the dashboard on :3000
make dashboard-test   # the full CI sequence
make contract-types   # regenerate the TypeScript contract
```

Without `SAKTHAI_API_URL` the dashboard reads `~/.sakthai` directly, which needs
no server at all.

## Deployment

This app **is** deployed: a Vercel project (`houseofsak/sak-family-agent`) builds
it on every push, with its root directory set to `apps/sak_agent_dashboard` in
Vercel's settings — that part is still a project setting, because Vercel resolves
the root directory *before* reading any config file. Everything downstream of it
now lives in [`vercel.json`](./vercel.json): the framework, the install command,
and the response headers (CSP, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, and `Cache-Control: no-store` over `/api/*` so a CDN can
never serve a stale reading as a live one).

What does **not** exist is a hosted SakThai API. With no `~/.sakthai` on a Vercel
lambda and no `SAKTHAI_API_URL` configured, `resolveSource()` serves demo data —
labelled as sample data in the header, and now with an on-page notice saying how
to point it at a live agent. To show real data, stand up a reachable
`sakthai web serve` and set `SAKTHAI_API_URL` and `SAKTHAI_API_TOKEN` in the
Vercel project. Note that the API refuses non-loopback binds unless
`SAKTHAI_WEB_ALLOW_PUBLIC` is set: it serves personal memory, so exposing it is
a deliberate decision.

Full walkthrough, including the root-directory setting and how to verify a
deploy: [`DEPLOYMENT.md`](./DEPLOYMENT.md). Environment variables:
[`.env.example`](./.env.example).

## Status

M1–M3 (scaffold, data layer, UI) and M4 (testing and build) are complete: `npm
run lint`, `npm run build`, `tsc --noEmit` and `npm test` all pass, and
`.github/workflows/apps.yml` runs them on every change under `apps/`.

# Sak Agent Dashboard

An observability dashboard for the Sak Family agent runtime. It reads the artifacts the
`sakthai` CLI and agent loop write under `~/.sakthai/` and renders them as live panels:
agent status, run analytics, session transcripts, memory, security audit logs, traces,
evals, the MCP server inventory, and the spec-kit feature tree.

Read-only by design — the dashboard never writes to the agent's state.

## Quick start

```bash
pnpm install          # pnpm 9.15.9, node >= 18
pnpm dev              # http://localhost:3000
```

Other scripts:

```bash
pnpm lint             # eslint over src/
pnpm typecheck        # tsc --noEmit
pnpm test             # vitest run
pnpm build            # production build
```

CI runs all four in `.github/workflows/subprojects.yml` (job `sak-agent-dashboard`).

## Where the data comes from

Everything real is read server-side from the agent's home directory. Nothing is fetched from
a network service unless you configure the Python web API bridge below.

| Source file | Read by | Powers |
|---|---|---|
| `~/.sakthai/eval.jsonl` | `src/lib/sakthai.ts` | Agent overview, analytics, eval panel |
| `~/.sakthai/audit.log` | `src/lib/sakthai.ts` | Security audit log viewer |
| `~/.sakthai/sessions/*.json` | `src/lib/sakthai.ts` | Session explorer + transcript modal |
| `~/.sakthai/memory.db` and `~/.sakthai/<persona>/memory.db` | `src/lib/db.ts` | Memory explorer (facts + observations) |
| `~/.sakthai/traces.jsonl` | `src/lib/traces.ts` | Trace waterfall viewer |
| `<repo>/.specify/` and `<repo>/specs/` | `src/lib/speckit.ts` | Spec-kit panel |

Per-persona memory shards matter: deployed personas run with
`SAKTHAI_HOME=$HOME/.sakthai/$AGENT`, so each writes to `~/.sakthai/<persona>/memory.db`
rather than the legacy unscoped `memory.db`. The dashboard reads both and attributes each
fact to its persona, mirroring `sakthai memory family`.

The remaining panels (MCP servers, MCP SDK, ChatKit, Antigravity, Genkit, Conductor, Stitch)
are curated reference catalogs held in `src/lib/`, not live integrations.

## Data source badges

Each panel reports whether its numbers are `live`, `demo`, or `unavailable`. This is
load-bearing: the dashboard ships with demo data so it renders on a fresh checkout, and
without the badge a machine with no `~/.sakthai/` looks identical to a busy one. If a panel
says `unavailable`, the source file is missing — not empty.

The Demo toggle in the header forces every panel to demo data.

## Configuration

Copy `.env.example` to `.env.local` and edit as needed. Every variable is optional; the
defaults work for a local `sakthai` install.

| Variable | Default | Purpose |
|---|---|---|
| `SAKTHAI_DIR` | `~/.sakthai` | Agent home to read artifacts from |
| `SPECKIT_DIR` | `<repo>/.specify` | spec-kit installation to introspect |
| `SAKTHAI_WEB_URL` | _(unset)_ | Base URL of `sakthai web` for the `/api/stages` + `/api/ecosystem` bridge |
| `SAKTHAI_WEB_TOKEN` | _(unset)_ | Bearer token for that API (`sakthai web setup` prints it) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | _(unset)_ | Send dashboard server spans to a collector; falls back to a local file exporter |
| `OTEL_SERVICE_NAME` | `sak-agent-dashboard` | Service name on emitted spans |

`SAKTHAI_WEB_TOKEN` is read server-side only and never reaches the browser — the
`/api/stages` and `/api/ecosystem` routes proxy it.

## Layout

```
src/
├── app/
│   ├── layout.tsx            root layout, fonts, header
│   ├── page.tsx              tab shell
│   ├── globals.css
│   └── api/<name>/route.ts   one GET route per panel, all returning { success, ... }
├── components/               one panel component per tab
├── lib/                      data access — parsers, catalogs, types
├── instrumentation.ts        OpenTelemetry NodeSDK registration
└── tests/                    vitest + jsdom + React Testing Library
```

`src/lib/types/` is the shared contract between the parsers, the API routes, and the
components. Add a type to an appropriate domain module in `src/lib/types/` (runtime,
integrations, m365, ui) and export from the barrel at `src/lib/types/index.ts`.

## Adding a panel

1. Add the data function in `src/lib/<name>.ts`, returning `undefined` on any read failure.
2. Add its types plus a `<Name>ApiResponse` to the appropriate domain module in
   `src/lib/types/<domain>.ts` and export it from the barrel at `src/lib/types/index.ts`.
3. Add `src/app/api/<name>/route.ts` following the existing `{ success, ... }` + generic-500
   convention (real errors go to `console.error`, never to the client).
4. Add `src/components/<Name>Panel.tsx`.
5. Register the tab in `TABS` in `src/lib/tabs/registry.tsx`.
6. Add `src/tests/<name>.test.tsx`.

## Telemetry

Server spans follow the OpenTelemetry [GenAI semantic
conventions](https://github.com/open-telemetry/semantic-conventions-genai): `invoke_agent`,
`execute_tool`, and `generate_content` spans carrying `gen_ai.*` attributes. The agent-side
spans come from the Python package's `sakthai.telemetry` module, written to
`~/.sakthai/traces.jsonl` when `SAKTHAI_OTEL_ENABLED` is set; the Traces tab renders them as
a waterfall.

## Related

- `personas/sakthai/sakthai/dashboard/data.py` — the Python KPI collector behind `sakthai web`
- `personas/sakthai/sakthai/web/server.py` — the Python HTTP API this dashboard can bridge to
- `apps/agent_workflow_framework/` — sibling app, same doc conventions
- `PLAN.md` — this app's phased plan and checklist

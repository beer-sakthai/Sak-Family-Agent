# Project: Sak-Agent-Family Dashboard

Read-only analytics UI over the SakThai agent family's runtime state.

## Architecture

- **Framework:** Next.js 16 (App Router) + React 19 + TypeScript 6
- **Styling:** Tailwind CSS 3 over a semantic token layer (below); Inter,
  Outfit and JetBrains Mono via `next/font/google`, which self-hosts them
- **Charts:** Recharts 3, coloured from the same tokens via `lib/chart-theme.ts`
- **Tests:** Vitest 4 + React Testing Library — see [`TESTING.md`](./TESTING.md)

### Theming

No component names a palette shade. Every colour is a role — `bg-panel`,
`text-fg-3`, `border-hue-rose-line` — defined once per theme as CSS variables
in `globals.css` and bound into Tailwind in `tailwind.config.ts` with
`<alpha-value>`, so `bg-panel/70` composes exactly as `bg-slate-900/70` did.

- **Surfaces:** `canvas`, `sunken`, `panel`, `raised`, `raised-2`
- **Hairlines:** `line`, `line-strong`, `line-soft`
- **Text:** `fg` … `fg-5`
- **Brand:** `accent`, `accent-strong`, `accent-contrast`
- **Ten status/category hues,** three roles each: `hue-<name>` (readable text,
  icons, solid fills), `hue-<name>-tint` (the wash behind a pill),
  `hue-<name>-line` (its border)

The three-role split is what makes the light theme readable rather than
merely inverted: `text-hue-emerald` on `bg-hue-emerald-tint` is emerald-400 on
emerald-950 in dark and emerald-700 on emerald-50 in light.

Theme (`system`/`light`/`dark`) and density (`comfortable`/`compact`) are
stored per browser and written to `<html>` as `data-theme`/`data-density` by
an inline bootstrap in `<head>` — before first paint, so there is no flash.
`system` removes the attribute rather than resolving it, letting the
`prefers-color-scheme` block keep following the OS with no media listener.

Recharts takes colours as props, not classes, so `lib/chart-theme.ts` reads
the same variables back out of the computed style and re-reads them when
either the attribute or the OS preference changes.

### View state

The whole view — section, search, severity, page, persona filter, open
detail, demo flag — serialises into the URL fragment as
`#section?q=…&persona=…` (`lib/url-state.ts`), with defaults omitted. A view
is therefore linkable and survives a reload, and the back button walks it.
Panels do not own their open detail id; the page passes it down.

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
| `/api/sessions` | `SessionsPayload` — summaries; `?id=` adds one transcript; `?persona=a,b` filters |
| `/api/memory` | `MemoryPayload` — facts and observations merged across shards; `?persona=a,b` filters |
| `/api/audit` | `AuditPayload` — security events from `audit.log` |
| `/api/workflows` | `WorkflowsPayload` — `agent_workflow` runs; `?id=` for one run |
| `/api/health` | Liveness probe: which source *would* answer, and whether an API URL/token is configured. Names no path, host or token — anyone who can reach the deployment can read it |

`?persona=` is applied **at the source**, before the search and before the
offset, in all three implementations and in the Python API — so `total`
counts the filtered set and paging through it lands on the right rows. A
value naming no known persona means "no filter", never an empty result.
Under a filter the unscoped legacy `memory.db` is excluded: it is attributed
to no persona.

Static routes alongside them: `/robots.txt`, `/manifest.webmanifest`,
`/icon.svg`, and `/opengraph-image` (edge runtime).

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
│   ├── CommandPalette.tsx · ShortcutsOverlay.tsx · KpiStrip.tsx
│   ├── Drawer.tsx · Toasts.tsx · Skeletons.tsx · HostedNotice.tsx
│   ├── DisplayMenu.tsx · PersonaFilter.tsx · DemoModeToggle.tsx
│   ├── AgentCard.tsx · AgentOverview.tsx · AnalyticsCharts.tsx
│   ├── SessionExplorer.tsx · MemoryExplorer.tsx · AuditLogs.tsx
│   └── WorkflowRuns.tsx · StitchStudio.tsx
├── lib/
│   ├── contracts.generated.ts   (generated — do not edit)
│   ├── source.ts · runtime.ts · demo.ts · db.ts
│   ├── theme.ts · chart-theme.ts · url-state.ts · export.ts
│   ├── nav.ts · format.ts · persona.ts · browser-state.ts
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

See [Keyboard](#keyboard) for the shortcuts. The sidebar tablist is a **single
tab stop** with the arrow keys, `Home` and `End` moving between sections — the
WAI-ARIA authoring practice, and the difference between one Tab to reach the
panel and seven. Both modals, the drawer and the command palette, trap Tab and
return focus to whatever opened them; `lib/focus.ts` holds the one definition
of "what would Tab reach in here" that both use.

The palette matches on a **scored fuzzy subsequence** over each command's label
and description (`lib/fuzzy.ts`): "usd" finds *Use sample data*, "ovw" finds
*Overview*. Consecutive and word-initial characters score highest, a label hit
outranks a description hit, and the matched characters are underlined in the
row so a non-obvious match explains itself rather than looking like a bug.

### Presentation mode

A third document-level preference beside theme and density (`lib/theme.ts`),
mirrored onto `<html data-presentation="on">` and restored by the same
pre-paint bootstrap. It hides `[data-chrome="sidebar"]` and every
`[data-chrome="secondary"]` control — the palette trigger, persona filter,
sample toggle, display menu, auto-refresh, copy-link and export — leaving the
figures, the source badge and the refresh clock. For a wall-mounted tab, where
none of what it hides is reachable anyway. The topbar button also requests
fullscreen, ignoring its absence, and `Esc` leaves the mode: the one way out
that needs no visible control, which is the point of a mode that hides them.

`@media print` does the same thing for paper — chrome removed, panels forced
light and `break-inside: avoid` — so the dashboard prints as a report.

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
and the response headers (CSP, HSTS, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, `Cross-Origin-Opener-Policy`,
`Cross-Origin-Resource-Policy`, `X-DNS-Prefetch-Control`, `X-Robots-Tag`, and
`Cache-Control: no-store` over `/api/*` so a CDN can never serve a stale
reading as a live one).

The App Router conventions are all present, which is what keeps a bad deploy
legible rather than blank: `loading.tsx` (shaped like the real page),
`error.tsx` and `global-error.tsx` — both surfacing the digest that finds the
trace in the Vercel logs, and the latter carrying its own two-palette
stylesheet because it renders when the layout, the token layer and the theme
bootstrap have all failed — and `not-found.tsx`.

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


## Keyboard

| Key | Does |
|---|---|
| `⌘K` / `Ctrl+K` | Command palette |
| `1`–`7` | Jump to a section, in sidebar order |
| `R` | Refresh every panel |
| `E` | Export the current panel as JSON |
| `[` | Collapse or expand the sidebar |
| `?` | The shortcut list |
| `Esc` | Close a drawer, menu or overlay; leave presentation mode |
| `←` `→` `↑` `↓` `Home` `End` | Move between sections, with the sidebar focused |

Single letters and digits are suppressed while a text field has focus, so a
search box never eats a shortcut.

## The trend window

Analytics carries a 7d/14d/30d/All window over the recorded history. It lives
in the view state (`lib/url-state.ts`) like every other filter, so a link
carries it — `#analytics?trend=7` — and the back button walks it. The window
slices the `trends` series the payload already holds rather than re-requesting
it: a second fetch could return a different set from the one the KPI strip
above was drawn from, and the two would silently disagree. The scope pill under
the charts states how many days it actually drew, so a window wider than the
recorded history is visible as such rather than implied.

## Export

`lib/export.ts` writes JSON or RFC 4180 CSV of exactly the rows on screen,
from the payload already in the browser — an export never re-queries and can
never show a different set from the one being looked at. Column order is
passed explicitly rather than derived from the first row's keys, so a row
missing an optional field cannot shift every later column left by one.

# web-dashboard/

A Vite + React + TypeScript static dashboard for the SakThai memory store. It is
hydrated from a `data.json` snapshot the CLI exports — no backend, no live agent
(for the interactive app see `sakthai dashboard`).

This is the source published to GitHub Pages by
`.github/workflows/pages.yml` (it builds this folder and deploys `dist/`).

## Develop

```bash
cd web-dashboard
npm install
npm run dev            # http://localhost:5173/sakthai-agent-v2/
```

## Refresh the data snapshot

```bash
# from the repo root, with the dashboard extra installed
sakthai dashboard --export web-dashboard/public/data.json
```

The shape matches `sakthai/dashboard/data.py` (`collect_dashboard_data`):
`kpis`, `growth`, `categories`, `recent_facts`, `top_observations`, and
optionally `graph` / `evolution`. If `data.json` is missing or unreadable the
app falls back to a built-in demo sample so it still renders.

## Build

```bash
npm run build          # type-checks, then emits dist/
npm run preview        # serve the production build locally
```

`vite.config.ts` sets `base` to `/sakthai-agent-v2/` for the GitHub Pages
project site. Override with `VITE_BASE=/ npm run build` for a domain-root host.

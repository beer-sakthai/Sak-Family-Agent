---
name: SakSee-dashboard
description: "Set up and run the SakThai Agent dashboard."
---

> **⚠️ Distinction:** This skill covers the **SakThai-Agent Mission Control dashboard** (React + Vite analytics app). Beer's "dashboard" on GitHub refers to the **House of Sak landing page** at `beer-sakthai/house-of-sak` (static HTML/CSS site). These are separate projects — use this skill for the analytics dashboard, and the `vercel-deploy` + `github-repo-management` skills for the House of Sak site.

> **⚠️ Repository Confusion:** The dashboard may be located in different repositories depending on the context. In our session, we found the dashboard in the `Sak-Family-Agent` repository (`/opt/data/Sak-Family-Agent/dashboard/`) rather than the `sakthai-agent-v2` repository. Always verify the actual repository location before proceeding with dashboard operations.

> **⚠️ Static File Location:** The web server expects built files in `/opt/data/Sak-Family-Agent/personas/sakthai/sakthai/dashboard/dist`, but the build process creates files in `/opt/data/Sak-Family-Agent/dashboard/dist`. After building, the files must be copied to the correct location for the server to find them.

> **⚠️ Server Process Management:** The web server (`python -m sakthai.web.server`) is a long-running process that may die unexpectedly. Always start it as a background process with `notify_on_complete=true` and verify it's accessible with `curl -I http://localhost:3001/` after starting. If the process dies, restart it.

> **⚠️ Hardcoded Static Data:** The default dashboard (`src/main.js`) contains hardcoded static data. To make it production-ready, update it to fetch live data from the API endpoints (`/api/stages` and `/api/ecosystem`). See `references/live-api-integration.md` for the pattern.

# SakThai Dashboard

Set up and serve the SakThai-Agent Mission Control dashboard — a React + Vite + Tailwind CSS v4 single-page app that visualises the agent's memory, skills, session activity, and project architecture. Does **not** include the SakThai-Agent backend; only the static dashboard frontend.

## When to Use

- User says "show me the dashboard" or "start the SakThai dashboard".
- Setting up the dashboard from the `sakthai-agent-v2` repo.
- Running dashboard tests or developing new dashboard features.
- Deploying the dashboard to GitHub Pages or Vercel.
- Verifying which repository a dashboard is running from (see `references/dashboard-repo-verification.md`).

## Prerequisites

- Node.js >= 18 (LTS recommended)
- pnpm installed (`corepack enable && corepack prepare pnpm@latest --activate` or `npm i -g pnpm`)
- The dashboard source at `<repo-root>/dashboard/` with `package.json`, `vite.config.js`, and `src/`.

## How to Run

Invoke through the `terminal` tool from the `dashboard/` directory.

## Quick Reference

| Command | Action |
|---------|--------|
| `pnpm install` | Install dependencies |
| `pnpm dev` | Start dev server on port 3000 |
| `pnpm build` | Build to `dist/` |
| `pnpm preview` | Preview production build |
| `pnpm test` | Run Vitest suite |

## Procedure

1. **Navigate to dashboard and install**

   ```bash
   cd /path/to/sakthai-agent-v2/dashboard
   pnpm install
   ```

2. **Verify tailwind config exists**

   The project uses Tailwind CSS v4 with `@tailwindcss/postcss`. Confirm `tailwind.config.js` and `postcss.config.js` are present in the dashboard root.

3. **Start dev server**

   ```bash
   pnpm dev
   ```

   The dev server starts on `http://localhost:3000/sakthai-agent-v2/` (base path configured in `vite.config.js`). Use the `process` tool to manage the background process.

4. **Run tests**

   ```bash
   pnpm test
   ```

   Tests are written with Vitest + Testing Library. The test setup (`src/test/setup.js`) stubs `ResizeObserver` for recharts compatibility. Key test coverage:
   - Falls back to demo data when `data.json` is unreachable
   - Renders "Live" badge when live data loads
   - Switches all 7 tabs via sidebar navigation
   - Renders thought-process groups, fact tables, and version history

5. **Build for production**

   ```bash
   pnpm build
   ```

   Output goes to `dist/`. The base path `/sakthai-agent-v2/` is baked into the build — deploy to a subdirectory or override `base` in `vite.config.js` for root-level deployment.

6. **Provide live data (optional)**

   Place a `data.json` file at `<root>/public/data.json` (served as `./data.json` at runtime). The dashboard fetches it on mount and switches to "Live" mode. Use the same schema as `src/data/demo-data.js`.

## Pitfalls

- **pnpm, not npm/yarn.** The repo has a `pnpm-lock.yaml`. Using npm or yarn will produce a different lockfile and may break. Always use `pnpm install`.
- **Tailwind v4 changes.** This project uses Tailwind CSS v4 with `@tailwindcss/postcss` plugin — the old `@tailwindcss` utility classes and `tailwind.config.js` `@apply` directives still work, but PostCSS config changed (no `tailwindcss` PostCSS plugin, only `@tailwindcss/postcss`).
- **ResizeObserver in tests.** `jsdom` does not implement `ResizeObserver`. The test setup stubs it; if that stub breaks, tests for recharts components will fail with `ResizeObserver is not defined`.
- **Base path mismatch.** The default `base: '/sakthai-agent-v2/'` in `vite.config.js` means the dev server serves at `localhost:3000/sakthai-agent-v2/` and production build assets reference that prefix. For root-level deployment (e.g. custom domain), change `base` to `'/'`.
- **No backend.** This is a purely static frontend. Live data requires either manually placing `data.json` or connecting the SakThai-Agent backend's data export.
- **Repository confusion.** The dashboard may be located in different repositories depending on the context. Always verify the actual repository location before proceeding with dashboard operations. See `references/dashboard-repo-verification.md` for specific examples and verification techniques.
- **Missing tools.** Not all systems have `lsof` installed by default. Have alternative methods ready for checking port usage, such as `netstat` (if available) or checking process information directly with `ps`.

## Verification

```bash
cd /path/to/dashboard
pnpm test --run
```

All tests should pass. Then start the dev server and confirm the page loads at `http://localhost:3000/sakthai-agent-v2/` with the sidebar and Overview tab visible.

See `references/dashboard-repo-verification.md` for specific examples of repository verification and common pitfalls when identifying dashboard locations.
See `references/dashboard-fix-2026-07-07.md` for a detailed example of fixing dashboard accessibility issues.
See `references/live-api-integration.md` for the pattern to replace hardcoded static data with live API fetches.
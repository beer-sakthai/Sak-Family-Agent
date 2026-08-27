# Deploying the dashboard to Vercel

The dashboard is a standard Next.js App Router project living in a
subdirectory of a Python monorepo. Two things follow from that, and they are
the only two that make a deploy non-obvious.

## 1. Set the Root Directory

Vercel builds from the repository root by default, where there is no
`package.json` at all. In **Project Settings → General → Root Directory**, set:

```
apps/sak_agent_dashboard
```

Leave *Include files outside the root directory* **off** — the dashboard needs
nothing from the rest of the repo at build time. `vercel.json` (in this
directory, so Vercel reads it once the root is set) pins the framework, the
install command and the response headers; everything else is Vercel's default
Next.js pipeline.

Equivalent from the CLI, run from this directory:

```bash
npx vercel link
npx vercel --prod
```

## 2. Decide what it should show

`resolveSource()` (`src/lib/source.ts`) picks a data source per request, in
order:

| Condition | Source | What you see |
|---|---|---|
| `?demo=1` on the request | `DemoSource` | the sample dataset, on request |
| `SAKTHAI_API_URL` is set | `ApiSource` | live data over HTTP |
| `~/.sakthai/` exists | `LocalFsSource` | live data off the local disk |
| none of the above | `DemoSource` | the sample dataset, with a banner saying so |

A Vercel function has no `~/.sakthai`, so **a deploy with no environment
variables serves sample data**. That is a deliberate, visible outcome rather
than a broken one: the header pill reads "Sample data" and the page carries a
notice explaining how to connect a live agent. It makes the dashboard
demo-able from a URL without a running agent behind it.

For live data, set both in **Project Settings → Environment Variables**:

| Variable | Value |
|---|---|
| `SAKTHAI_API_URL` | Base URL of a reachable `sakthai web serve` |
| `SAKTHAI_API_TOKEN` | Bearer token from `sakthai web setup` |

See [`.env.example`](./.env.example) for the full list. Note that
`sakthai web serve` refuses non-loopback binds unless `SAKTHAI_WEB_ALLOW_PUBLIC`
is set, so exposing it to Vercel means a tunnel or a reverse proxy — not a
public bind on a whim.

## Runtime notes

- Every `/api/*` route is `runtime = "nodejs"` and `dynamic = "force-dynamic"`;
  `vercel.json` additionally sends `Cache-Control: no-store` so a CDN never
  serves a stale reading as a live one.
- `better-sqlite3` is a native addon and stays out of the bundle
  (`serverExternalPackages` in `next.config.mjs`). It is only ever imported by
  `LocalFsSource`, behind a dynamic `import()`, so a hosted deploy that never
  reaches the local source never loads it.
- The app is read-only. It has no mutating routes, no auth of its own, and no
  session state — anyone who can reach the deployment can read whatever the
  configured source returns. If that source is a live agent, put the
  deployment behind Vercel's [deployment
  protection](https://vercel.com/docs/deployment-protection).
- `robots` metadata is `noindex, nofollow`: an internal dashboard has no
  business in a search index.

## Verifying a deploy

```bash
curl -s https://<deployment>/api/agents | head -c 400   # envelope + `source`
```

The `source` field in the envelope is the authoritative answer to "is this
live?" — the UI renders exactly that value and nothing else.

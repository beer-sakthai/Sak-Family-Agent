---
name: SakKing-local-api-prototype
category: web
description: Class-level skill for spinning up a minimal, secure, stdlib HTTP API
  server on WSL/Ubuntu — no extra dependencies, suitable for dashboard/JSON endpoints.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    related_skills: []
    source: hermes:local-api-prototype
---

# Local API Prototype

Use when a project needs a quick `localhost:<port>` API surface with read-only JSON endpoints plus static frontend.

## Approach

1. **Routes first** — design the JSON endpoints before writing code.
2. **Static root secondary** — serve `/` from an existing `web/` or `dashboard/` dir.
3. **Security defaults** — implement `_json()` helper for JSON responses; never echo raw exceptions or secrets; prefer status strings over live token values in `/api/ecosystem`.
4. **Run + verify** — start server, curl each route, confirm JSON and static page load.

## Steps

1. Create `scripts/serve_api.py` from the bundled template.
2. Set `HOST`, `PORT`, and `STATIC_ROOT` at the top.
3. Implement `/api/...` handlers returning `dict`.
4. Start as a background process or foreground.
5. Validate:
   - `GET /` → static page loads
   - `GET /api/<name>` → valid JSON
   - error paths → safe default JSON, no leakage

## Pitfalls

- Server dies silently if started as background without lifecycle tracking.
- **Ports already in use** (`3001`, `3002` common). Stop the old process before bind.
- `SimpleHTTPRequestHandler` will **directory-list** when no `index.html`. Set safe fallback to `index.html`.
- Do not put secrets/credentials in `/api/ecosystem`. Use configured/not_configured or ready/not_ready flags only.

## Templates

- `templates/serve_api.py` — stdlib HTTPServer skeleton with `/api/stages` and `/api/ecosystem` routes, security-first.

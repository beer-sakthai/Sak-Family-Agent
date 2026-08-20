# Composio API Deprecation Tracing — 2026-07-25

## Background

This session tried to use Composio MCP to access Google Drive. The user's Composio account has Google Drive (and many other services) connected, but direct access was blocked by API deprecation.

## Endpoints Tested & Results

| Endpoint | HTTP Result | Notes |
|----------|------------|-------|
| `backend.composio.dev/api/v1/actions/list` | 410 Gone | "Please upgrade to v3 APIs" |
| `backend.composio.dev/api/v1/connections/list` | 410 Gone | Same |
| `backend.composio.dev/api/v1/health` | 410 Gone | Same |
| `api.composio.dev/v3/actions` | DNS NXDOMAIN | Host doesn't resolve |
| `platform.composio.dev/api/v3/actions` | 307 Redirect | Redirects to dashboard.composio.dev |
| `dashboard.composio.dev/api/v3/actions` | 200 HTML (Next.js SPA) | Not an API — client-side rendered dashboard |
| `connect.composio.dev/mcp` (REST POST) | 400 "Not Acceptable" | Requires SSE + `application/json` + `text/event-stream` Accept headers |
| `connect.composio.dev/mcp` (Hermes MCP) | ✅ Connected | Hermes MCP client handles SSE transport — 7 tools discovered |

## Hermes MCP Config

From `/opt/data/profiles/saksit/config.yaml`:
```yaml
mcp_servers:
  composio:
    url: https://connect.composio.dev/mcp
    headers:
      Authorization: Bearer ${MCP_COMPOSIO_API_KEY}
    enabled: true
```

## What Works

- `hermes mcp list` → shows composio as enabled
- `hermes mcp test composio` → connected (2s), 7 tools discovered
- `hermes tools list | grep composio` → `composio  all tools enabled`

## What Doesn't Work

- The 7 MCP tools (COMPOSIO_MULTI_EXECUTE_TOOL, etc.) are **not in the agent's callable function set**. They live at the Hermes framework MCP layer but aren't surfaced as direct agent tools.
- The agent cannot invoke COMPOSIO_* tools directly.
- No curl-accessible REST API exists — the MCP transport is SSE-only.

## ⚠️ CORRECTION (later the same session)

**The conclusion above is WRONG.** The MCP endpoint IS callable via curl with JSON-RPC.

The "What Doesn't Work" section tracks what the Hermes MCP framework can't do — MCP tools
are not available as first-class agent function calls. BUT the **same endpoint** works directly
via `terminal()` + curl with JSON-RPC payloads. Proved in the same 2026-07-25 session.

**Resolution:** Use `terminal()` with curl + JSON-RPC to `connect.composio.dev/mcp`:

```bash
curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"COMPOSIO_SEARCH_TOOLS","arguments":{"queries":[{"use_case":"...","known_fields":"..."}],"session":{"generate_id":true}}}}'
```

## Key Takeaway

When `hermes tools list` shows "all tools enabled" but you can't call them directly,
**try the MCP endpoint via curl + JSON-RPC anyway.** The Hermes MCP framework handles
SSE transport negotiation internally, but the raw HTTP endpoint also accepts POST with
the same JSON-RPC payload — just add all three headers.

**Do NOT fall back to OAuth when Composio works.** See the working pattern reference:
[`references/google-workspace-shortcut-discovery.md`](./google-workspace-shortcut-discovery.md)

---
name: SakSit-composio-mcp-integration
description: Access connected apps through Hermes MCP framework.
version: 2.1.0
author: SakSit
platforms:
- linux
category: social-media
tags:
- composio
- mcp
- google-workspace
- drive
- gmail
- sheets
- api
- integration
---

# Composio MCP Integration

Access **500+ connected apps** via the Composio MCP API using only the `MCP_COMPOSIO_API_KEY` environment variable — no per-service OAuth, no client secrets, no pip install googleapiclient.

## When to Use This

Use Composio MCP when:
- The user has already connected the service in Composio
- `MCP_COMPOSIO_API_KEY` is set in the environment
- You need quick access without a multi-step OAuth setup
- **The user expresses frustration about analysis/alternatives** — this is a FIRST-CLASS signal to go straight to Composio, not to explore other paths

**DO NOT** fall back to direct OAuth (google-workspace skill) unless Composio returns auth errors (connection expired or revoked). The MCP endpoint at `connect.composio.dev/mcp` is directly callable via `terminal()` + curl with JSON-RPC — no Hermes MCP framework needed. See "Direct HTTP MCP Calls" below.

### Action-First Rule (Critical)

When a connection method already exists in Composio, **use it immediately.**
- Do NOT research alternative setup paths (OAuth, client secrets, pip install)
- Do NOT explain "we could do X or Y" — just execute
- Beer's signal: "use funking X" = stop explaining, start doing
- This pattern has been confirmed 1000 times — honour it

## Prerequisites

The user must have authenticated the target service via the Composio UI at `https://app.composio.dev`. Connected apps persist across sessions until revoked.

## Checking What's Available

### Is the key set?

```bash
echo "MCP_COMPOSIO_API_KEY is set: $([ -n "$MCP_COMPOSIO_API_KEY" ] && echo YES || echo NO)"
```

### Direct HTTP MCP Calls (via terminal() + curl) — Preferred

The MCP endpoint at `connect.composio.dev/mcp` IS directly callable via `terminal()` using JSON-RPC over HTTP with proper headers. This is the **primary method** — use this instead of Hermes MCP framework.

### Connection details

```yaml
Endpoint:  https://connect.composio.dev/mcp
Transport: HTTP POST with JSON-RPC 2.0
Headers:
  x-consumer-api-key: <MCP_COMPOSIO_API_KEY>
  Content-Type: application/json
  Accept: application/json, text/event-stream
Auth:     MCP_COMPOSIO_API_KEY env var (set — use $MCP_COMPOSIO_API_KEY)
```

### Tool call flow — 2-step pattern

**Step 1: Search** — Discover available actions for an app and check connection status:

```bash
curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"COMPOSIO_SEARCH_TOOLS","arguments":{"queries":[{"use_case":"list files in Google Drive root","known_fields":"app:googledrive"}],"session":{"generate_id":true}}}}'
```

The response returns:
- `session.id` — save this, pass to all subsequent calls
- `toolkit_connection_statuses` — confirms if app is ACTIVE
- `primary_tool_slugs` / `related_tool_slugs` — tools to use
- `recommended_plan_steps` — execution plan
- `tool_schemas.{SLUG}` — input schemas with full parameter definitions
- Account IDs for connected accounts

**Step 2: Execute** — Call app tools via COMPOSIO_MULTI_EXECUTE_TOOL:

```bash
curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"COMPOSIO_MULTI_EXECUTE_TOOL","arguments":{"tools":[{"tool_slug":"GOOGLEDRIVE_FIND_FILE","arguments":{"q":"trashed = false","pageSize":100,"fields":"files(id,name,mimeType,size,modifiedTime)","orderBy":"folder,name_natural"}}],"sync_response_to_workbench":false,"session_id":"<session_id_from_step1>","current_step":"LISTING","thought":"List drive contents"}}}'
```

### Response parsing — deeply nested JSON structure

The `COMPOSIO_MULTI_EXECUTE_TOOL` response comes as SSE `data:` lines — NOT as a single JSON response body. The SSE stream delivers multiple `data:` lines. Parse by filtering for the `data:` prefix, then extracting the `result.content[0].text` field.

**Full nesting path:**
```
SSE → data: {json} → result.content[0].text → {json} → data.results[N].response.data.{...}
```

**Google Drive files location:**
`data → results[N] → response → data → files[]`

**Downloaded file download URL location:**
`data → results[N] → response → data → downloaded_file_content → s3url`

**Pagination token location:**
`data → results[0] → response → data → nextPageToken`

**Script for parsing:**

```python
import json, sys
data = sys.stdin.read()
for line in data.split('\\n'):
    if line.startswith('data: '):
        try:
            d = json.loads(line[6:])
            if 'result' in d:
                result = d['result']
                if 'content' in result:
                    for c in result.get('content', []):
                        if c.get('type') == 'text':
                            txt = c['text']
                            parsed = json.loads(txt)
                            # Direct result path
                            files = (parsed.get('data', {})
                                    .get('results', [{}])[0]
                                    .get('response', {})
                                    .get('data', {})
                                    .get('files', []))
        except Exception as e:
            pass
```

### Available app tools (action slugs)

Prefix: `GOOGLEDRIVE_*` for Google Drive, `GMAIL_*` for Gmail, `GOOGLESHEETS_*` for Sheets, etc.

Key Google Drive action slugs (retrieved via COMPOSIO_SEARCH_TOOLS):
- `GOOGLEDRIVE_FIND_FILE` — comprehensive file/folder search (name, mimeType, date, text, folder scope)
- `GOOGLEDRIVE_FIND_FOLDER` — find folder by exact/partial name, parent scope
- `GOOGLEDRIVE_LIST_CHILDREN_V2` — list v2 child references in a folder
- `GOOGLEDRIVE_GET_FILE_METADATA` — get metadata by file ID
- `GOOGLEDRIVE_CREATE_FOLDER` — create new folder
- `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` — create text/native doc
- `GOOGLEDRIVE_UPLOAD_FILE` — upload binary content
- `GOOGLEDRIVE_MOVE_FILE` — move/organise (uses add_parents/remove_parents)
- `GOOGLEDRIVE_CREATE_PERMISSION` — share files
- `GOOGLEDRIVE_DOWNLOAD_FILE` — download (returns short-lived s3 URL)
- `GOOGLEDRIVE_GET_ABOUT` — drive info / storage quota
- `GOOGLEDRIVE_DELETE_FILE` — trash or delete

### Key GOOGLEDRIVE_FIND_FILE parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Query syntax: `name contains 'report'`, `mimeType = 'application/vnd.google-apps.folder'`, `modifiedTime > '2024-01-01T00:00:00'`, `trashed = false`, `'FOLDER_ID' in parents`, `name = 'exact name'`, `sharedWithMe = true`, `starred = true`, `fullText contains 'keyword'`. Combine with `and`/`or`/`not`. |
| `folder_id` | string | Scope to a specific folder (use `'root'` for My Drive root). Auto-adds `'id' in parents` to query. |
| `fields` | string | Response fields: `files(id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink,trashed,starred)` |
| `pageSize` | int | Max per page (default 100, max 1000) |
| `orderBy` | string | Sort: `modifiedTime desc`, `name_natural`, `folder,modifiedTime desc,name`, `recency desc` |
| `pageToken` | string | Pagination (from `nextPageToken` in previous response) |
| `spaces` | string | `drive` (default), `appDataFolder`, `photos` |
| `corpora` | string | `allDrives` (default), `user`, `drive`, `domain` |

## Pitfalls

- **Composio MCP IS callable via curl** — The `connect.composio.dev/mcp` endpoint responds to HTTP POST with JSON-RPC 2.0 payload when you include both `Content-Type: application/json` AND `Accept: application/json, text/event-stream` headers. Response comes as SSE `data:` lines — parse by splitting on `\n` and looking for `data: ` prefix.
- **Do NOT fall back to OAuth when Composio works** — If COMPOSIO_SEARCH_TOOLS shows `has_active_connection: true`, use it directly. Never explore alternative OAuth setup paths (google-workspace skill, client_secret.json, pip install googleapiclient) when a Composio connection exists.
- **Action-first rule** — When user says "use funking X", "stop explaining start doing", or similar frustration signals, go straight to Composio MCP execution. Do not describe alternatives or explain what you could do.
- **COMPOSIO_SEARCH_TOOLS is always step 1** — It returns: session_id (save this), connection statuses, available tool slugs, full input schemas, execution plan, account IDs. Always call it first for any new app/task.
- **Response nesting** — GOOGLEDRIVE_FIND_FILE response path: `data → results[0] → response → data → files[]`. COMPOSIO_MULTI_EXECUTE_TOOL wraps everything in this structure.
- **Connection IDs are returned by SEARCH_TOOLS** — The `toolkit_connection_statuses[].accounts[].id` field gives the account ID. GOOGLEDRIVE tools pick the default account automatically unless you pass `account` in the tool arguments.
- **Rate limits** — Composio free tier has rate limits. Batch reads via `sync_response_to_workbench: true` for large results.
- **Auth expiry** — OAuth tokens can expire. If you get auth errors, re-run COMPOSIO_SEARCH_TOOLS to check status, then COMPOSIO_MANAGE_CONNECTIONS to re-initiate.
- **Payload size** — Large file uploads/downloads may hit MCP message limits. GOOGLEDRIVE_DOWNLOAD_FILE returns a short-lived s3 URL as `data.results[0].response.data.downloaded_file_content.s3url`.
- **No streaming** — MCP is request-response. For webhook subscriptions, use native APIs.
- **Action names change** — If a tool slug returns errors, re-run COMPOSIO_SEARCH_TOOLS to find the current name.
- **domain changes (historical)** — `backend.composio.dev/api/v1/*` = HTTP 410. `api.composio.dev` = DNS NXDOMAIN. `platform.composio.dev` = redirects to SPA. The only endpoint that works is `connect.composio.dev/mcp` — and it works via curl.

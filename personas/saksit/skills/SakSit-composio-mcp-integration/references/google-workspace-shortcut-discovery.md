# Google Drive via Composio MCP — Working Pattern (2026-07-25)

## History

Earlier versions of this file tracked the broken `backend.composio.dev/api/v1/*` REST API approach. That endpoint is HTTP 410 Gone. This file now documents the **working** pattern: JSON-RPC over HTTP to `connect.composio.dev/mcp`.

## Verified Working: MCP IS Callable via curl

**Claim from earlier session: "not accessible via curl"** → **FALSE.** Proven working 2026-07-25.

The `connect.composio.dev/mcp` endpoint accepts HTTP POST with:
- Header `x-consumer-api-key: $MCP_COMPOSIO_API_KEY`
- Header `Content-Type: application/json`
- Header `Accept: application/json, text/event-stream`
- JSON-RPC 2.0 body

The response comes as SSE (`event: message` / `data: {...}` format). Parse by splitting on `\n`, filtering for `data: ` prefix.

## Beer's Connected Apps (confirmed via COMPOSIO_SEARCH_TOOLS)

From the SEARCH_TOOLS response for Google Drive (2026-07-25):

| Service | Status | Account |
|---------|--------|---------|
| Google Drive | ✅ ACTIVE (2 accounts) | beernanthasit@gmail.com |
| Google Sheets | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Docs | ✅ ACTIVE | beernanthasit@gmail.com |
| Gmail | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Calendar | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Meet | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Photos | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Slides | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Maps | ✅ ACTIVE | beernanthasit@gmail.com |
| YouTube | ✅ ACTIVE | beernanthasit@gmail.com |
| Google Tasks | ✅ ACTIVE | beernanthasit@gmail.com |

Plus non-Google: GitHub, GitLab, Hugging Face, Instagram, LinkedIn, Canva, Vercel, and many more.

## Working MCP Call Pattern

### Step 1: SEARCH_TOOLS (discovery + plan + session)

```bash
curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "COMPOSIO_SEARCH_TOOLS",
      "arguments": {
        "queries": [{
          "use_case": "browse and organise Google Drive files",
          "known_fields": "app:googledrive"
        }],
        "session": {"generate_id": true}
      }
    }
  }'
```

### Step 2: MULTI_EXECUTE_TOOL (execute actions)

```bash
curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
      "arguments": {
        "tools": [{
          "tool_slug": "GOOGLEDRIVE_FIND_FILE",
          "arguments": {
            "q": "trashed = false and mimeType = \"application/vnd.google-apps.folder\"",
            "pageSize": 200,
            "fields": "files(id,name,mimeType,modifiedTime)",
            "orderBy": "folder,name_natural"
          }
        }],
        "sync_response_to_workbench": false,
        "session_id": "<session_id_from_step1>",
        "current_step": "LISTING_FOLDERS",
        "thought": "List all top-level folders"
      }
    }
  }'
```

### Response Parsing (Python)

```python
import json, sys
data = sys.stdin.read()
for line in data.split('\n'):
    if line.startswith('data: '):
        d = json.loads(line[6:])
        result = d.get('result', {})
        for c in result.get('content', []):
            if c.get('type') == 'text':
                txt = c['text']
                parsed = json.loads(txt)
                files = (parsed.get('data', {})
                        .get('results', [{}])[0]
                        .get('response', {})
                        .get('data', {})
                        .get('files', []))
                # files is a list of dicts with keys: id, name, mimeType, size, modifiedTime, parents, webViewLink, display_url
```

## Google Drive Structure (Beer's Drive — 2026-07-25)

**52 folders total at root level.**

### Core House of Sak
- Agent Profiles, House of Sak, House of Sak - Organized Content
- Knowledge Base, Sak Agent, Marketing Materials
- Business Development, Technical Documentation
- SakSit (x2 — Jul 7 + Jul 20 — duplicates need merging)
- SakSit-Learning-Journal, SakThai-Agent-Backup
- Videos & Multimedia

### Personal
- My CV, Paysilps (x2 — duplicate), Photos
- Desktop, My laptop, Saved from Chrome

### Tech / SDKs
- Colab Notebooks, Google AI Studio
- Google Tensor SDK, Latest_SDK_v1.1.0_2026_07_02
- SDK_v1.0.0_2026_05_20, Past Releases
- AI Safety

### Git backup artifacts (cluttering root — ~20 folders)
- `.git`, `.github`, `ce`, `d0`, `dd`, `fb`, `heads` (x2), `hooks`, `info` (x2)
- `ISSUE_TEMPLATE`, `logs`, `objects`, `origin` (x2), `pack`, `refs` (x2)
- `remotes` (x2), `tags`, `urban-succotash`
- Note: these look like Google Drive backups of git repos

## Critical Lessons

1. **MCP IS callable via curl** — contrary to earlier beliefs. The 3 headers (x-consumer-api-key + Content-Type + Accept) are all required.
2. **SEARCH_TOOLS first** — always call this before MULTI_EXECUTE_TOOL to get session_id, connection status, tool slugs, and plans.
3. **Action over analysis** — Beer's repeated signal: when a Composio connection exists, USE IT. Don't explore alternatives.
4. **No OAuth fallback needed** — the google-workspace skill (OAuth setup) is entirely skippable when Composio has active connections.
5. **Session IDs matter** — pass the same session_id across all calls in a workflow.

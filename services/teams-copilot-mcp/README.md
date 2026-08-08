# teams-copilot-mcp

Local stdio MCP server exposing Microsoft Teams (Graph API) and M365 Copilot
operations as tools, so SakThai/Hermes/Claude can drive Teams directly.

## Direction

This is the "agent calls Teams+Copilot" leg. It does **not** expose
Sak-Family-Agent's own tools *to* Copilot/Teams — Copilot Studio and Teams
apps need a remote HTTPS endpoint to call into, which a local stdio process
can't provide. See `docs/superpowers/specs/2026-08-03-cowork-plugin-design.md`
for that reverse leg (Copilot Cowork connectors).

## Auth

App-only (client-credentials) Microsoft Graph auth — no interactive login,
no per-user OAuth. Reuses the same Azure AD app registration convention as
the `hermes teams-pipeline` skill:

```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

`.env.example` documents the three variables the server reads, but the
server itself never loads `.env` files (`graph_client.py` calls
`os.environ.get(...)` directly, nothing more) — copying it to `.env` alone
does nothing. **Export these three vars in whatever shell/profile launches
the MCP server process.** This matters most for the Claude Code plugin path
(`.mcp.json`'s `env` block does `"MSGRAPH_TENANT_ID": "${MSGRAPH_TENANT_ID}"`
— a passthrough from Claude Code's own environment; if they're unset there,
`graph_client.py`'s `_require_config` still raises a clear `GraphAuthError`
naming the missing vars, but only on the *first tool call* rather than at
launch, so an unset var won't be obvious until something actually tries to
use it) and for `sakthai run`/Hermes the same way. If you
already have an app registration for the Teams meeting pipeline, reuse it —
just make sure it has the Graph **application permissions** the tools you
plan to use need (e.g. `Team.ReadBasic.All`, `Channel.ReadWrite.All`,
`ChannelMessage.Send`, `OnlineMeetings.Read.All`, `Calendars.ReadWrite`,
`User.Read.All`), with admin consent granted.

## Install

```bash
cd services/teams-copilot-mcp
uv sync
```

## Tests

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

26 unit tests across `test_catalog.py`, `test_graph_client.py`,
`test_server.py`. No real Graph/MSAL network calls — `msal.
ConfidentialClientApplication` and `httpx.Client.request` are mocked at the
boundary. Note: constructing a real `ConfidentialClientApplication` performs
OIDC tenant discovery over the network even before any token call, so tests
mock the whole class, not just `acquire_token_for_client`.

## Run standalone (for testing)

```bash
uv run teams-copilot-mcp
```

Speaks MCP over stdio — it's meant to be launched by an MCP host, not run
interactively.

## Register with SakThai

Add to `~/.sakthai/mcp.json` (sakthai's own outbound MCP server loader —
`servers` array format, see `sakthai/mcp/servers.py`):

```json
{
  "servers": [
    {
      "name": "teams-copilot",
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/Sak-Family-Agent/services/teams-copilot-mcp",
        "teams-copilot-mcp"
      ]
    }
  ]
}
```

Tools then appear namespaced as `teams-copilot__<tool_name>` in `sakthai run`
and `sakthai chat`.

To register it for a specific persona instead (Claude-style `mcpServers`
object format, matching `personas/<name>/config/mcp.json`):

```json
{
  "mcpServers": {
    "teams-copilot": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/Sak-Family-Agent/services/teams-copilot-mcp",
        "teams-copilot-mcp"
      ]
    }
  }
}
```

## Tools

Dedicated (most common operations):

- `list_channels(team_id)`
- `send_channel_message(team_id, channel_id, content)`
- `list_calendar_events(user_id, top=25)`
- `get_meeting_transcript(user_id, meeting_id, transcript_id)`
- `copilot_retrieval_query(...)` — **not usable yet.** The Copilot Retrieval
  API only supports delegated (signed-in-user) Graph auth; Application
  permissions are explicitly unsupported
  ([Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval)).
  This server only implements app-only auth, so the tool raises
  `NotImplementedError` before making any call — see "Known limitation"
  below.

Long tail (everything else in the curated catalog — teams, chats, meetings,
users, presence — see `src/teams_copilot_mcp/catalog.py`):

- `search_actions(query)` — find a catalog entry by keyword
- `execute_action(action_id, path_params, query_params, body)` — run one

Full escape hatch (anything not in the catalog at all):

- `execute_raw(method, path, query_params, body)` — arbitrary Graph v1.0 call

## Known limitation: Copilot Retrieval requires delegated auth

`copilot_retrieval_query` (both the dedicated tool and
`execute_action("copilot_retrieval_query", ...)`) always raises
`NotImplementedError` rather than calling Graph. Confirmed against Microsoft's
own API reference: the Retrieval API's permission table lists `Application: Not
supported` for both least- and higher-privileged permissions — only delegated
(interactive, signed-in-user) auth works. This server's `graph_client.py` only
implements client-credentials (app-only) auth, which every other tool relies
on, so it can't satisfy this one endpoint's requirement.

The request schema is otherwise implemented correctly and ready to use once
delegated auth exists: `POST /copilot/retrieval` (v1.0) with body
`{queryString, dataSource: "sharePoint"|"oneDriveBusiness"|"externalItem",
filterExpression?, dataSourceConfiguration?, maximumNumberOfResults?}` — see
the tool's docstring in `server.py` for field details. Adding delegated auth
(device-code flow, token caching) is a separate, larger feature, not a quick
patch — it changes this server's auth model for one endpoint only.

Beyond that: this Graph endpoint doesn't work for personal Microsoft accounts
at all (delegated auth for a personal MSA is also "Not supported" per the
same permissions table) — a work/school Entra ID tenant with Copilot
licensing is required regardless of auth mode. See
`docs/superpowers/specs/2026-08-03-cowork-plugin-design.md` for the fuller
research trail and the Copilot Cowork connector path that resulted from it.

## Notes / caveats

- `catalog.py` is a hand-picked subset of Graph, not a full mirror — entries
  marked `stability="verify"` (currently just Copilot retrieval) are newer
  Graph surfaces that move fast; check
  https://learn.microsoft.com/graph/api/overview before depending on them.
- App-only credentials have tenant-wide reach for whatever permissions the
  app registration was granted — there's no per-call scoping here. Keep the
  granted permissions to what you actually need.
- Not built for the Anthropic Directory / multi-tenant distribution — this is
  a personal/team tool, local stdio, one Azure app registration per install.

import fs from "fs";
import path from "path";
import {
  McpAction,
  McpActionCategory,
  McpServerSpec,
  McpServerStatus,
} from "./types";

const TEAMS_COPILOT_ACTIONS: McpAction[] = [
  {
    id: "list_joined_teams",
    method: "GET",
    pathTemplate: "/me/joinedTeams",
    description:
      "List teams the calling identity's delegated user is a member of. Note: app-only auth has no signed-in user — use list_teams_in_org or a specific /users/{id}/joinedTeams instead in that mode.",
    params: [],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "list_teams_in_org",
    method: "GET",
    pathTemplate: "/teams",
    description:
      "List all Teams-enabled groups in the tenant (requires Team.ReadBasic.All).",
    params: [],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "list_channels",
    method: "GET",
    pathTemplate: "/teams/{team_id}/channels",
    description: "List channels in a team.",
    params: ["team_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "list_channel_messages",
    method: "GET",
    pathTemplate: "/teams/{team_id}/channels/{channel_id}/messages",
    description: "List recent messages in a channel.",
    params: ["team_id", "channel_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "send_channel_message",
    method: "POST",
    pathTemplate: "/teams/{team_id}/channels/{channel_id}/messages",
    description:
      "Post a message to a channel. Body: {'body': {'content': '<html or text>'}}.",
    params: ["team_id", "channel_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "list_team_members",
    method: "GET",
    pathTemplate: "/teams/{team_id}/members",
    description: "List members of a team.",
    params: ["team_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "teams",
  },
  {
    id: "list_chat_messages",
    method: "GET",
    pathTemplate: "/chats/{chat_id}/messages",
    description: "List messages in a 1:1 or group chat.",
    params: ["chat_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "chats",
  },
  {
    id: "send_chat_message",
    method: "POST",
    pathTemplate: "/chats/{chat_id}/messages",
    description:
      "Send a message to a 1:1 or group chat. Body: {'body': {'content': '<html or text>'}}.",
    params: ["chat_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "chats",
  },
  {
    id: "create_online_meeting",
    method: "POST",
    pathTemplate: "/users/{user_id}/onlineMeetings",
    description: "Create a Teams online meeting on behalf of a user.",
    params: ["user_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "meetings",
  },
  {
    id: "get_online_meeting",
    method: "GET",
    pathTemplate: "/users/{user_id}/onlineMeetings/{meeting_id}",
    description: "Get details of an online meeting.",
    params: ["user_id", "meeting_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "meetings",
  },
  {
    id: "list_meeting_transcripts",
    method: "GET",
    pathTemplate: "/users/{user_id}/onlineMeetings/{meeting_id}/transcripts",
    description:
      "List transcript artifacts for a meeting (metadata only, not content).",
    params: ["user_id", "meeting_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "meetings",
  },
  {
    id: "get_meeting_transcript_content",
    method: "GET",
    pathTemplate:
      "/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content",
    description:
      "Fetch the actual transcript content (VTT format) for a meeting.",
    params: ["user_id", "meeting_id", "transcript_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "meetings",
  },
  {
    id: "list_calendar_events",
    method: "GET",
    pathTemplate: "/users/{user_id}/calendar/events",
    description: "List calendar events for a user.",
    params: ["user_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "calendar",
  },
  {
    id: "create_calendar_event",
    method: "POST",
    pathTemplate: "/users/{user_id}/calendar/events",
    description: "Create a calendar event for a user.",
    params: ["user_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "calendar",
  },
  {
    id: "get_user",
    method: "GET",
    pathTemplate: "/users/{user_id}",
    description: "Get a user's profile by id or userPrincipalName.",
    params: ["user_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "users",
  },
  {
    id: "list_users",
    method: "GET",
    pathTemplate: "/users",
    description:
      "List users in the tenant (supports $filter, $search via execute_action params).",
    params: [],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "users",
  },
  {
    id: "get_user_presence",
    method: "GET",
    pathTemplate: "/users/{user_id}/presence",
    description:
      "Get a user's Teams presence (available/busy/away/offline).",
    params: ["user_id"],
    stability: "stable",
    requiresDelegatedAuth: false,
    category: "users",
  },
  {
    id: "copilot_retrieval_query",
    method: "POST",
    pathTemplate: "/copilot/retrieval",
    description:
      "Query the Microsoft Graph Copilot Retrieval API for grounding content across connected data sources. Requires delegated (signed-in-user) auth — Application permissions are not supported by this endpoint.",
    params: [],
    stability: "verify",
    requiresDelegatedAuth: true,
    category: "copilot",
  },
];

function detectStatus(): { status: McpServerStatus; reason: string } {
  const tenant = process.env.MSGRAPH_TENANT_ID;
  const clientId = process.env.MSGRAPH_CLIENT_ID;
  const secret = process.env.MSGRAPH_CLIENT_SECRET;
  const missing: string[] = [];
  if (!tenant) missing.push("MSGRAPH_TENANT_ID");
  if (!clientId) missing.push("MSGRAPH_CLIENT_ID");
  if (!secret) missing.push("MSGRAPH_CLIENT_SECRET");
  if (missing.length === 0) {
    return {
      status: "healthy",
      reason:
        "All Microsoft Graph app-only credentials are present in the environment.",
    };
  }
  if (missing.length === 3) {
    return {
      status: "unconfigured",
      reason:
        "No Microsoft Graph credentials detected — export MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, and MSGRAPH_CLIENT_SECRET.",
    };
  }
  return {
    status: "degraded",
    reason: `Missing environment variables: ${missing.join(", ")}.`,
  };
}

function resolveRepoPath(): string {
  const candidate = path.resolve(
    process.cwd(),
    "..",
    "..",
    "services",
    "teams-copilot-mcp"
  );
  try {
    if (fs.existsSync(candidate)) return candidate;
  } catch {
    // ignore
  }
  return "services/teams-copilot-mcp";
}

export function getMcpServers(): McpServerSpec[] {
  const { status, reason } = detectStatus();
  const repoPath = resolveRepoPath();

  const teamsCopilot: McpServerSpec = {
    id: "teams-copilot-mcp",
    name: "teams-copilot-mcp",
    displayName: "Teams + M365 Copilot",
    description:
      "Local stdio MCP server that exposes Microsoft Teams (Graph API) and M365 Copilot operations as tools so SakThai/Hermes/Claude can drive Teams directly.",
    category: "Microsoft 365 / Teams",
    transport: "stdio",
    language: "Python 3.11+ (fastmcp + msal + httpx)",
    repoPath,
    command: "uv",
    args: ["run", "--project", repoPath, "teams-copilot-mcp"],
    entrypoint: "teams_copilot_mcp.server:main",
    status,
    statusReason: reason,
    envVars: [
      {
        key: "MSGRAPH_TENANT_ID",
        purpose: "Azure AD tenant id for client-credentials auth.",
        required: true,
      },
      {
        key: "MSGRAPH_CLIENT_ID",
        purpose: "Azure AD app registration client id.",
        required: true,
      },
      {
        key: "MSGRAPH_CLIENT_SECRET",
        purpose: "Azure AD app registration client secret.",
        required: true,
      },
    ],
    tools: [
      {
        name: "list_channels",
        signature: "list_channels(team_id)",
        description: "List channels in a Team.",
      },
      {
        name: "send_channel_message",
        signature: "send_channel_message(team_id, channel_id, content)",
        description:
          "Post a message to a Teams channel. `content` may be plain text or HTML.",
      },
      {
        name: "list_calendar_events",
        signature: "list_calendar_events(user_id, top=25)",
        description:
          "List upcoming calendar events for a user (by id or userPrincipalName).",
      },
      {
        name: "get_meeting_transcript",
        signature:
          "get_meeting_transcript(user_id, meeting_id, transcript_id)",
        description:
          "Fetch a Teams meeting transcript's content (VTT format).",
      },
      {
        name: "copilot_retrieval_query",
        signature:
          "copilot_retrieval_query(query_text, data_source, filter_expression?, connection_id?, maximum_number_of_results?)",
        description:
          "Query the M365 Copilot Retrieval API for grounding content.",
        disabled: true,
        disabledReason:
          "Requires delegated (signed-in-user) Graph auth; this server only implements app-only auth. Tool raises NotImplementedError before any network call.",
      },
      {
        name: "search_actions",
        signature: "search_actions(query)",
        description:
          "Search the curated catalog of Teams/Graph/Copilot actions by keyword.",
      },
      {
        name: "execute_action",
        signature:
          "execute_action(action_id, path_params?, query_params?, body?)",
        description:
          "Run a catalog action by id (from search_actions) against Graph.",
      },
      {
        name: "execute_raw",
        signature: "execute_raw(method, path, query_params?, body?)",
        description:
          "Call an arbitrary Microsoft Graph v1.0 endpoint not in the catalog.",
      },
    ],
    actions: TEAMS_COPILOT_ACTIONS,
    registrationTargets: [
      {
        label: "SakThai global outbound MCP",
        path: "~/.sakthai/mcp.json",
        format: "servers[]",
        snippet: JSON.stringify(
          {
            servers: [
              {
                name: "teams-copilot",
                command: "uv",
                args: ["run", "--project", repoPath, "teams-copilot-mcp"],
              },
            ],
          },
          null,
          2
        ),
      },
      {
        label: "Per-persona (Claude-style mcpServers)",
        path: "personas/<persona>/config/mcp.json",
        format: "mcpServers{}",
        snippet: JSON.stringify(
          {
            mcpServers: {
              "teams-copilot": {
                command: "uv",
                args: ["run", "--project", repoPath, "teams-copilot-mcp"],
              },
            },
          },
          null,
          2
        ),
      },
      {
        label: "Claude Code plugin (.mcp.json)",
        path: `${repoPath}/.mcp.json`,
        format: "mcpServers{}",
        snippet: JSON.stringify(
          {
            "teams-copilot-mcp": {
              command: "uv",
              args: ["run", "--project", "${CLAUDE_PLUGIN_ROOT}", "teams-copilot-mcp"],
              env: {
                MSGRAPH_TENANT_ID: "${MSGRAPH_TENANT_ID}",
                MSGRAPH_CLIENT_ID: "${MSGRAPH_CLIENT_ID}",
                MSGRAPH_CLIENT_SECRET: "${MSGRAPH_CLIENT_SECRET}",
              },
            },
          },
          null,
          2
        ),
      },
    ],
    docsUrl:
      "https://github.com/beer-sakthai/Sak-Family-Agent/tree/main/services/teams-copilot-mcp",
    knownLimitations: [
      "copilot_retrieval_query requires delegated auth (not app-only). The Retrieval API lists Application permissions as Not supported.",
      "App-only credentials have tenant-wide reach for the granted Graph permissions; scope the app registration accordingly.",
      "Not built for multi-tenant distribution — one Azure AD app registration per install.",
    ],
  };

  const composio: McpServerSpec = {
    id: "composio",
    name: "composio",
    displayName: "Composio (1000+ SaaS apps)",
    description:
      "Hosted MCP server exposing Composio's catalog of 1000+ business-app integrations (Gmail, Slack, GitHub, Notion, Linear, Jira, HubSpot, …). Agents call seven meta-tools that discover, connect, and dispatch against the underlying tool set; OAuth and remote execution live on Composio's side, not on this host.",
    category: "SaaS toolkits (hosted)",
    transport: "http",
    language: "Remote HTTP endpoint (no local runtime)",
    repoPath: "https://github.com/ComposioHQ/composio-mcp-plugin",
    command: "n/a (URL-served)",
    args: [],
    entrypoint: "https://connect.composio.dev/mcp",
    status: "healthy",
    statusReason:
      "Hosted MCP endpoint — no local credentials or subprocess. Per-app OAuth is negotiated on demand via COMPOSIO_MANAGE_CONNECTIONS at tool-call time.",
    envVars: [],
    tools: [
      {
        name: "COMPOSIO_SEARCH_TOOLS",
        signature: "COMPOSIO_SEARCH_TOOLS(query)",
        description:
          "Semantic search over the Composio tool catalog. Returns the most relevant tool ids for a natural-language task; feed those into COMPOSIO_MULTI_EXECUTE_TOOL.",
      },
      {
        name: "COMPOSIO_MANAGE_CONNECTIONS",
        signature: "COMPOSIO_MANAGE_CONNECTIONS(app, action)",
        description:
          "Initiate or refresh an OAuth connection for a specific app (e.g. Slack, Gmail). Returns an authorization URL the user visits once per app.",
      },
      {
        name: "COMPOSIO_WAIT_FOR_CONNECTIONS",
        signature: "COMPOSIO_WAIT_FOR_CONNECTIONS(request_ids)",
        description:
          "Block until pending OAuth connection requests either complete or time out — pair with COMPOSIO_MANAGE_CONNECTIONS at the start of any flow that needs a new app.",
      },
      {
        name: "COMPOSIO_MULTI_EXECUTE_TOOL",
        signature: "COMPOSIO_MULTI_EXECUTE_TOOL(calls[])",
        description:
          "Batch-execute one or more Composio tools by id. Each call carries its own tool_id + arguments; results come back in one payload for reduced round trips.",
      },
      {
        name: "COMPOSIO_REMOTE_WORKBENCH",
        signature: "COMPOSIO_REMOTE_WORKBENCH(operation, …)",
        description:
          "Persistent remote scratch space for multi-step work — read/write files, keep session state across tool calls without shipping bytes over the wire each turn.",
      },
      {
        name: "COMPOSIO_REMOTE_BASH_TOOL",
        signature: "COMPOSIO_REMOTE_BASH_TOOL(command)",
        description:
          "Execute a shell command inside Composio's remote sandbox. Runs off-host — never touches the local system running the agent.",
      },
    ],
    actions: [],
    registrationTargets: [
      {
        label: "Cursor / Claude Desktop (mcpServers)",
        path: "~/.cursor/mcp.json  or  claude_desktop_config.json",
        format: "mcpServers{}",
        snippet: JSON.stringify(
          {
            mcpServers: {
              composio: {
                url: "https://connect.composio.dev/mcp",
              },
            },
          },
          null,
          2
        ),
      },
      {
        label: "SakThai global outbound MCP",
        path: "~/.sakthai/mcp.json",
        format: "servers[]",
        snippet: JSON.stringify(
          {
            servers: [
              {
                name: "composio",
                url: "https://connect.composio.dev/mcp",
                transport: "http",
              },
            ],
          },
          null,
          2
        ),
      },
      {
        label: "Per-persona (Claude-style mcpServers)",
        path: "personas/<persona>/config/mcp.json",
        format: "mcpServers{}",
        snippet: JSON.stringify(
          {
            mcpServers: {
              composio: {
                url: "https://connect.composio.dev/mcp",
              },
            },
          },
          null,
          2
        ),
      },
    ],
    docsUrl: "https://github.com/ComposioHQ/composio-mcp-plugin",
    knownLimitations: [
      "URL-served (hosted) — outbound network access to connect.composio.dev is required at every tool call; there is no offline / air-gapped mode.",
      "Per-app OAuth flows require an interactive browser step the first time each app is connected; agents block on COMPOSIO_WAIT_FOR_CONNECTIONS until the user completes the redirect.",
      "Tool discovery is dynamic — the concrete tool ids returned by COMPOSIO_SEARCH_TOOLS change as Composio's catalog evolves; do not hardcode ids in prompts.",
      "COMPOSIO_REMOTE_BASH_TOOL runs off-host in Composio's sandbox — output is real, but nothing it writes lands on the local filesystem.",
    ],
  };

  return [teamsCopilot, composio];
}

export function summarizeActions(server: McpServerSpec): {
  total: number;
  byCategory: Record<McpActionCategory, number>;
  delegatedOnly: number;
  verify: number;
} {
  const byCategory = {
    teams: 0,
    chats: 0,
    meetings: 0,
    calendar: 0,
    users: 0,
    copilot: 0,
    other: 0,
  } as Record<McpActionCategory, number>;
  let delegatedOnly = 0;
  let verify = 0;
  for (const a of server.actions) {
    byCategory[a.category] += 1;
    if (a.requiresDelegatedAuth) delegatedOnly += 1;
    if (a.stability === "verify") verify += 1;
  }
  return { total: server.actions.length, byCategory, delegatedOnly, verify };
}

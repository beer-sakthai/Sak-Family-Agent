# Managed HTTP MCP Integrations (Composio)

This reference captures the successful pattern for adding a managed HTTP MCP
server to Hermes Agent. The provider runs the remote server and is responsible
for auth/session handling.

## Server Setup

- Name: `composio`
- Transport: HTTP
- URL: `https://connect.composio.dev/mcp`
- Auth: not set through local header config; use the server’s login flow.

Config entry:
```yaml
mcp_servers:
  composio:
    url: https://connect.composio.dev/mcp
```

## Verification

```bash
hermes mcp test composio
```

## Fixes and Notes

- If Hermes cannot see the server after saving config, restart the agent;
  MCP discovery happens at startup.
- If the URL becomes unreachable later, prefer Investigating with the provider
  docs instead of guessing alternate endpoints.
- Known usable endpoints: `https://connect.composio.dev/mcp` and
  `https://mcp.composio.dev`.

# Live Agent Runtime for the Sak Family

This directory holds the runtime configuration for the live Telegram agents.

## How It Works

The Sak Family project uses a split between persona content and runtime:

- `sakthai-agent` (this monorepo) contains the core logic, shared memory, and
  `SOUL.md` persona definitions for all six agents.
- The live runtime loads a persona and connects it to chat platforms such as
  Telegram.

The files here tell the runtime how to load and run each agent.

## Directory Structure

- `profiles/{agent_name}/SOUL.md`: Persona definition loaded by the runtime.
- `profiles/{agent_name}/config.yaml`: Runtime config, including model and
  platform integration settings.
- `systemd/`: Example service files for running agents persistently.

## MCP Client

The runtime can connect to MCP servers at startup and expose their tools to the
agent.

### Quick Start

Add servers under `mcp_servers` in the runtime config:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

When the agent starts, it discovers the server tools and registers them with a
prefix such as `mcp_time_*`.

## Security

For stdio servers, the runtime only passes a small baseline environment to the
subprocess. Add secrets explicitly with `env` to avoid leaking credentials.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

## Troubleshooting

- `MCP SDK not available`: install `mcp` in the agent environment.
- `No MCP servers configured`: add entries under `mcp_servers`.
- `Failed to connect`: confirm the command exists and increase timeouts if
  needed.

## Example

```yaml
mcp_servers:
  sakthai:
    command: "/path/to/Sak-Family-Agent/.venv/bin/sakthai"
    args: ["mcp"]
    env:
      SAKTHAI_HOME: "/home/beer/.sakthai"
```

This exposes shared-memory tools to the running agent.

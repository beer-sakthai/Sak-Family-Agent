# Hermes Agent Runtime for the Sak Family

This directory contains the configuration for running the Sak Family agents on the **Hermes Agent framework**.

## How It Works

The Sak Family project follows a "brain in a jar" model:

- **`sakthai-agent` (This Monorepo):** Contains the core logic, shared memory, and the `SOUL.md` persona definitions for all six agents. It is the "brain."
- **Hermes Agent Framework:** An external runtime that loads a persona and connects it to chat platforms like Telegram. It is the "body."

The configurations in this directory tell the Hermes framework how to load and run each Sak Family agent.

## Directory Structure

- `profiles/{agent_name}/SOUL.md`: The specific persona definition loaded by Hermes. These are often copies or specializations of the main `SOUL.md` files in the root `personas/` directory.
- `profiles/{agent_name}/config.yaml`: The runtime configuration for the Hermes agent, specifying the model, enabled tools, and platform integrations (e.g., Telegram token).
- `systemd/`: Example `systemd` service files for running the agents as persistent services on a Linux machine.

## Native MCP Client for Hermes

The Hermes Agent has a built-in MCP (Model Context Protocol) client that connects to MCP servers at startup, discovers their tools, and makes them available to the running agent. This is the primary way to extend the capabilities of a deployed agent.

### When to Use

Use this whenever you want to:

- Connect to MCP servers and use their tools from within a deployed Hermes Agent.
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP.
- Run local stdio-based MCP servers (`npx`, `uvx`, or any command).

### Quick Start

Add MCP servers to the Hermes Agent's configuration file at `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

When the Hermes Agent starts, it will automatically connect to the server, discover its tools (e.g., `get_current_time`), and register them with the prefix `mcp_time_*`.

### Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config.

#### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

#### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### Tool Naming Convention

MCP tools are registered with the naming pattern `mcp_{server_name}_{tool_name}`. Hyphens and dots in names are replaced with underscores.

### Security

For stdio servers, Hermes does **not** pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited (`PATH`, `HOME`, `USER`, etc.).

To pass secrets like API keys, you **must** add them explicitly via the `env` config key. This prevents accidental credential leakage.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Troubleshooting

**"MCP SDK not available"**: The `mcp` Python package is not installed in the Hermes Agent's environment. Install it with `pip install mcp`.

**"No MCP servers configured"**: The `mcp_servers` key is missing or empty in `~/.hermes/config.yaml`.

**"Failed to connect to MCP server 'X'"**:

- **Command not found**: The `command` (e.g., `npx`, `uvx`) isn't on the `PATH` for the user running the Hermes service.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.

**Tools not appearing**:

- Check that the server is listed under the `mcp_servers` key in the correct `config.yaml`.
- Ensure the YAML indentation is correct.
- Look at the Hermes Agent's startup logs for connection messages.

### Examples

#### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

#### SakThai Memory Server

This is how you would give a deployed Hermes agent access to the shared Sak-Family memory store.

```yaml
mcp_servers:
  sakthai:
    command: "/path/to/your/Sak-Family-Agent/.venv/bin/sakthai"
    args: ["mcp"]
    env:
      # Ensure the MCP server can find the memory database
      SAKTHAI_HOME: "/home/beer/.sakthai"
```

This would expose tools like `mcp_sakthai_learn`, `mcp_sakthai_recall`, and `mcp_sakthai_search` to the running Hermes agent, allowing it to access the family's shared brain.

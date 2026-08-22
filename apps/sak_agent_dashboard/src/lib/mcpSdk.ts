import fs from "fs";
import path from "path";
import {
  McpSdkData,
  SdkPackage,
  SdkPrimitive,
  SdkScaffoldFile,
  SdkUsageSite,
} from "./types";

function resolveRepoRoot(): string {
  // `turbopackIgnore` on the traversals: without it Turbopack's static analysis
  // sees an unbounded `process.cwd()/..` and traces the *entire monorepo* into
  // every serverless function (121 MB locally — `personas/` and the vendored
  // M365 SDK included). The files these readers actually need are declared
  // explicitly by `outputFileTracingIncludes` in `next.config.mjs`.
  const candidates = [
    path.resolve(/* turbopackIgnore: true */ process.cwd(), "..", ".."),
    path.resolve(/* turbopackIgnore: true */ process.cwd(), ".."),
    process.cwd(),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(path.join(c, "personas")) && fs.existsSync(path.join(c, "services"))) {
        return c;
      }
    } catch {
      // ignore
    }
  }
  return path.resolve(/* turbopackIgnore: true */ process.cwd(), "..", "..");
}

const PRIMITIVES: SdkPrimitive[] = [
  {
    id: "server-init",
    name: "FastMCP server",
    kind: "server",
    summary:
      "Instantiate a FastMCP server; register tools/resources/prompts by decorating callables on it.",
    language: "python",
    snippet: `from fastmcp import FastMCP

mcp = FastMCP("my-mcp-server")

def main() -> None:
    # Speaks MCP over stdio by default; hosts launch this as a subprocess.
    mcp.run()

if __name__ == "__main__":
    main()`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#quickstart",
  },
  {
    id: "tool-decorator",
    name: "@mcp.tool()",
    kind: "tool",
    summary:
      "Expose a Python function as a callable tool. Type hints become the JSON schema; the docstring becomes the description.",
    language: "python",
    snippet: `from typing import Any
from fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
def list_channels(team_id: str) -> dict[str, Any]:
    """List channels in a Team."""
    return {"team_id": team_id, "channels": []}`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#tools",
  },
  {
    id: "resource-decorator",
    name: "@mcp.resource()",
    kind: "resource",
    summary:
      "Expose read-only data behind a URI. Hosts fetch it on demand; useful for large context that shouldn't live in the tool call.",
    language: "python",
    snippet: `@mcp.resource("teams://channels/{team_id}")
def get_channels_resource(team_id: str) -> str:
    """Return the channel list as a text resource."""
    return "\\n".join(channel_names_for(team_id))`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#resources",
  },
  {
    id: "prompt-decorator",
    name: "@mcp.prompt()",
    kind: "prompt",
    summary:
      "Expose a reusable prompt template. Hosts surface these as slash-commands / user-selectable prompts.",
    language: "python",
    snippet: `@mcp.prompt()
def channel_digest(team_id: str, days: int = 7) -> str:
    """Summarize the last N days of channel activity for a team."""
    return f"Summarize the past {days} days of activity in team {team_id}."`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#prompts",
  },
  {
    id: "context-injection",
    name: "Context injection",
    kind: "context",
    summary:
      "Add a Context argument to any tool/resource to reach the running server — for logging, progress reporting, or requesting more input.",
    language: "python",
    snippet: `from fastmcp import Context, FastMCP

mcp = FastMCP("demo")

@mcp.tool()
async def slow_scan(target: str, ctx: Context) -> dict[str, str]:
    await ctx.info(f"Scanning {target}…")
    await ctx.report_progress(0.5, 1.0)
    return {"target": target, "status": "ok"}`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#context",
  },
  {
    id: "stdio-transport",
    name: "stdio transport (default)",
    kind: "transport",
    summary:
      "Line-delimited JSON-RPC over stdin/stdout; hosts launch the server as a subprocess. What sakthai's outbound MCP loader uses.",
    language: "python",
    snippet: `# Default — no argument needed.
mcp.run()

# Explicit:
mcp.run(transport="stdio")`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#transports",
  },
  {
    id: "sse-transport",
    name: "SSE / HTTP transport",
    kind: "transport",
    summary:
      "Server-sent events over HTTP for remote hosts. Requires an ASGI runner and a URL a host can reach — Copilot Studio / Teams need this leg.",
    language: "python",
    snippet: `# Serve over SSE (needs an ASGI runner like uvicorn behind it).
mcp.run(transport="sse", host="0.0.0.0", port=8000)

# Or expose the ASGI app directly:
app = mcp.sse_app()`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#sse",
  },
  {
    id: "client-usage",
    name: "MCP client (outbound)",
    kind: "client",
    summary:
      "Programmatically connect to another MCP server — what sakthai/mcp/client.py does by hand today.",
    language: "python",
    snippet: `from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(
    command="uv",
    args=["run", "--project", "services/teams-copilot-mcp", "teams-copilot-mcp"],
)

async def main() -> None:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])`,
    docsUrl:
      "https://github.com/modelcontextprotocol/python-sdk#client",
  },
];

function pkgVersionSpec(pyproject: string, dep: string): string | undefined {
  const re = new RegExp(`['\"]${dep}([><=~!].*?)['\"]`);
  const match = pyproject.match(re);
  return match ? match[1] : undefined;
}

function detectPackages(repoRoot: string): SdkPackage[] {
  let fastmcpVersion: string | undefined;
  const teamsPyproject = path.join(
    repoRoot,
    "services",
    "teams-copilot-mcp",
    "pyproject.toml"
  );
  try {
    const raw = fs.readFileSync(teamsPyproject, "utf8");
    fastmcpVersion = pkgVersionSpec(raw, "fastmcp");
  } catch {
    // ignore
  }

  const packages: SdkPackage[] = [
    {
      name: "mcp",
      displayName: "modelcontextprotocol/python-sdk",
      role:
        "Official Python SDK for the Model Context Protocol. Ships the FastMCP server, low-level server/client APIs, and stdio/SSE transports.",
      pypi: "https://pypi.org/project/mcp/",
      repoUrl: "https://github.com/modelcontextprotocol/python-sdk",
      license: "MIT",
      installCommand: "uv add mcp",
      usedInRepoAs:
        "Not imported by name today — sakthai/mcp/server.py + sakthai/mcp/client.py implement the wire protocol themselves. Reachable indirectly via fastmcp.",
    },
    {
      name: "fastmcp",
      displayName: "fastmcp",
      role:
        "Ergonomic decorator API layered on top of the official mcp SDK. What teams-copilot-mcp uses today.",
      pypi: "https://pypi.org/project/fastmcp/",
      repoUrl: "https://github.com/jlowin/fastmcp",
      license: "MIT",
      installCommand: "uv add fastmcp",
      usedInRepoAs:
        "services/teams-copilot-mcp — from fastmcp import FastMCP; mcp = FastMCP('teams-copilot-mcp').",
      detectedVersionSpec: fastmcpVersion,
    },
  ];
  return packages;
}

function detectUsageSites(repoRoot: string): SdkUsageSite[] {
  const sites: SdkUsageSite[] = [];

  const teamsServer = path.join(
    repoRoot,
    "services",
    "teams-copilot-mcp",
    "src",
    "teams_copilot_mcp",
    "server.py"
  );
  if (fs.existsSync(teamsServer)) {
    sites.push({
      path: "services/teams-copilot-mcp/src/teams_copilot_mcp/server.py",
      kind: "import",
      detail: "from fastmcp import FastMCP — dedicated + catalog Teams/Graph tools.",
    });
  }

  const teamsPyproject = path.join(
    repoRoot,
    "services",
    "teams-copilot-mcp",
    "pyproject.toml"
  );
  if (fs.existsSync(teamsPyproject)) {
    sites.push({
      path: "services/teams-copilot-mcp/pyproject.toml",
      kind: "pyproject",
      detail: "Declares fastmcp>=2.0.0 as a runtime dependency.",
    });
  }

  const sakthaiMcpServer = path.join(
    repoRoot,
    "personas",
    "sakthai",
    "sakthai",
    "mcp",
    "server.py"
  );
  if (fs.existsSync(sakthaiMcpServer)) {
    sites.push({
      path: "personas/sakthai/sakthai/mcp/server.py",
      kind: "custom-implementation",
      detail:
        "Hand-rolled MCP stdio server (JSON-RPC 2.0, protocol version 2024-11-05). No SDK dependency — reuses BUILTIN_TOOLS from agent/tools.py.",
    });
  }
  const sakthaiMcpClient = path.join(
    repoRoot,
    "personas",
    "sakthai",
    "sakthai",
    "mcp",
    "client.py"
  );
  if (fs.existsSync(sakthaiMcpClient)) {
    sites.push({
      path: "personas/sakthai/sakthai/mcp/client.py",
      kind: "custom-implementation",
      detail:
        "Hand-rolled outbound stdio MCP client. Uses select-based timeouts, no asyncio, no SDK dependency.",
    });
  }
  return sites;
}

function buildScaffold(): { name: string; description: string; files: SdkScaffoldFile[] } {
  const name = "my-mcp-server";
  const files: SdkScaffoldFile[] = [
    {
      path: `services/${name}/pyproject.toml`,
      language: "toml",
      content: `[project]
name = "${name}"
version = "0.1.0"
description = "New MCP server for Sak-Family-Agent"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]

[project.scripts]
${name} = "${name.replace(/-/g, "_")}.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/${name.replace(/-/g, "_")}"]
`,
    },
    {
      path: `services/${name}/src/${name.replace(/-/g, "_")}/__init__.py`,
      language: "python",
      content: `"""Package initializer."""\n`,
    },
    {
      path: `services/${name}/src/${name.replace(/-/g, "_")}/server.py`,
      language: "python",
      content: `"""MCP server: ${name}."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("${name}")


@mcp.tool()
def echo(message: str) -> dict[str, Any]:
    """Return the message back — replace with your first real tool."""
    return {"echo": message}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
`,
    },
    {
      path: `services/${name}/.mcp.json`,
      language: "json",
      content: JSON.stringify(
        {
          [name]: {
            command: "uv",
            args: ["run", "--project", "${CLAUDE_PLUGIN_ROOT}", name],
          },
        },
        null,
        2
      ) + "\n",
    },
    {
      path: `services/${name}/README.md`,
      language: "markdown",
      content: `# ${name}\n\nMCP server built with fastmcp. Register with sakthai via ~/.sakthai/mcp.json:\n\n\`\`\`json\n{\n  "servers": [\n    {\n      "name": "${name}",\n      "command": "uv",\n      "args": ["run", "--project", "services/${name}", "${name}"]\n    }\n  ]\n}\n\`\`\`\n`,
    },
  ];
  return {
    name,
    description:
      "Minimal fastmcp-based server matching the teams-copilot-mcp layout — pyproject entry-point, one @mcp.tool, .mcp.json for Claude Code plugin registration.",
    files,
  };
}

export function getMcpSdkData(): McpSdkData {
  const repoRoot = resolveRepoRoot();
  return {
    overview: {
      title: "Model Context Protocol — Python SDK",
      description:
        "The official Python SDK for MCP. It ships the FastMCP high-level server, the low-level protocol implementation, both stdio and SSE transports, and a client API for calling other MCP servers.",
      protocolVersion: "2024-11-05",
      docsUrl: "https://github.com/modelcontextprotocol/python-sdk",
    },
    packages: detectPackages(repoRoot),
    primitives: PRIMITIVES,
    usageSites: detectUsageSites(repoRoot),
    scaffold: buildScaffold(),
  };
}

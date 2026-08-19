# PRD 0005: Remote MCP Tool Federation & Dynamic Secure Agent Gateway

## 1. Project Overview
The **Remote MCP Tool Federation & Dynamic Secure Agent Gateway** provides a unified Model Context Protocol (MCP) gateway that aggregates, filters, authenticates, and routes tool calls across local stdio tools and remote HTTP/SSE MCP servers for all 6 Sak-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`).

---

## 2. Problem Statement
1. **Tool Namespace Collisions**: As multi-agent systems grow, different MCP servers may register conflicting tool names (e.g. `read_file`, `fetch_web`).
2. **Missing Security Boundaries**: Direct execution of remote MCP tools without AST validation or permission gating poses sandbox escape risks.
3. **Dynamic Discovery Gaps**: Personas cannot discover, connect, or disconnect MCP servers at runtime without restarting processes.

---

## 3. Goals
- **Unified Tool Registry**: Aggregate multiple MCP servers under namespace isolation (`server_slug::tool_name`).
- **Zero-Tolerance Security Filter**: Intercept and validate arguments against path traversal, ASCII control characters, and dangerous shell commands.
- **Dynamic Tool Dispatcher**: Route tool invocation requests asynchronously to the appropriate stdio / HTTP MCP transport.
- **War Room MCP Tool Matrix**: Expose active servers, tool schemas, and execution latency on the Next.js dashboard (`/api/mcp/gateway`).

---

## 4. Functional Requirements (P0)
- [ ] **MCP Gateway & Registry (`personas/sakthai/sakthai/mcp/gateway.py`)**:
  - `register_server(server_id, transport_type, tools)`
  - `discover_tools(persona_filter=None)`
  - `invoke_tool(tool_id, arguments, persona)` with security validation.
- [ ] **Security AST Filter (`personas/sakthai/sakthai/mcp/security.py`)**:
  - Path traversal and control char rejection.
- [ ] **Next.js Dashboard Gateway Route (`apps/sak_agent_dashboard/src/app/api/mcp/gateway/route.ts`)**:
  - MCP server health status and dynamic tool schema introspection.

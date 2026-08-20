# Track 005 Specification: Remote MCP Tool Federation & Dynamic Gateway

## Overview
Unified MCP tool gateway providing namespace federation, dynamic tool routing, and AST security containment for multi-agent execution.

## PRD Reference
[`docs/prds/0005_prd_remote_mcp_tool_federation.md`](file:///home/beern/Sak-Family-Agent/docs/prds/0005_prd_remote_mcp_tool_federation.md)

## Core Requirements
1. `MCPGateway` supporting multi-server tool registration.
2. `invoke_tool` with security containment.
3. Dashboard `/api/mcp/gateway` route handler.
4. Hermetic unit & integration tests.

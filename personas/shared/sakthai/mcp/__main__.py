"""Entry point: ``python -m sakthai.mcp`` runs the stdio MCP server."""

from __future__ import annotations

from .server import serve

if __name__ == "__main__":
    serve()

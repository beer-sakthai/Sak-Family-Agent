"""MCP stdio server exposing the memory tools."""

from __future__ import annotations

from .server import handle_request, serve

__all__ = ["handle_request", "serve"]

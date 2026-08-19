"""Domain models for Remote MCP Tool Federation & Gateway."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class TransportType(enum.StrEnum):
    STDIO = "stdio"
    HTTP_SSE = "http_sse"
    WEBSOCKET = "websocket"


@dataclass
class MCPToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MCPServerRegistration:
    server_id: str
    transport: TransportType
    endpoint: str | None = None
    tools: list[MCPToolDefinition] = field(default_factory=list)
    healthy: bool = True
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_id": self.server_id,
            "transport": self.transport.value,
            "endpoint": self.endpoint,
            "healthy": self.healthy,
            "tools": [t.to_dict() for t in self.tools],
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }

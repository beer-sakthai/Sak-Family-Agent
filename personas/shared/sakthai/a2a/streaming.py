"""Reactive in-memory pub/sub broker and SSE streaming generator for A2A communication."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from .models import StreamChunk

logger = logging.getLogger(__name__)


class A2AMeshBroker:
    """Central event broker coordinating real-time token streaming across agent personas."""

    def __init__(self, max_history_size: int = 1000) -> None:
        self._seq = 0
        self._subscribers: list[tuple[asyncio.Queue[StreamChunk], str | None]] = []
        self._history: list[StreamChunk] = []
        self._max_history = max_history_size

    def subscribe(self, persona: str | None = None) -> asyncio.Queue[StreamChunk]:
        """Register a subscriber queue. If persona is specified, only that persona's chunks are delivered."""
        q: asyncio.Queue[StreamChunk] = asyncio.Queue()
        self._subscribers.append((q, persona))
        return q

    def unsubscribe(self, q: asyncio.Queue[StreamChunk]) -> None:
        self._subscribers = [s for s in self._subscribers if s[0] is not q]

    async def publish_chunk(self, chunk: StreamChunk) -> StreamChunk:
        """Assign monotonic sequence number and fan-out chunk to all matching subscribers."""
        self._seq += 1
        chunk.seq = self._seq
        self._history.append(chunk)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        for q, filter_persona in list(self._subscribers):
            if filter_persona is None or filter_persona == chunk.persona:
                try:
                    q.put_nowait(chunk)
                except asyncio.QueueFull:
                    logger.warning("Subscriber queue full for persona %s", filter_persona)

        return chunk

    async def sse_generator(self, queue: asyncio.Queue[StreamChunk]) -> AsyncIterator[str]:
        """Format chunks into standard W3C Server-Sent Events stream."""
        while True:
            chunk = await queue.get()
            data = json.dumps(chunk.to_dict(), ensure_ascii=False)
            yield f"id: {chunk.seq}\nevent: agent_delta\ndata: {data}\n\n"
            if chunk.stop_reason:
                break

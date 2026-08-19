# tests/test_a2a_streaming.py
import asyncio
import pytest
from sakthai.a2a.models import ChunkType, StreamChunk
from sakthai.a2a.streaming import A2AMeshBroker


@pytest.mark.asyncio
async def test_streaming_broker_publish_and_subscribe():
    broker = A2AMeshBroker()
    queue = broker.subscribe(persona="saksee")

    chunk = StreamChunk(
        seq=0,
        persona="saksee",
        turn=1,
        chunk_type=ChunkType.TOKEN,
        delta="Hello from SakSee",
    )
    published_chunk = await broker.publish_chunk(chunk)
    assert published_chunk.seq == 1

    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received.seq == 1
    assert received.delta == "Hello from SakSee"


@pytest.mark.asyncio
async def test_streaming_broker_sse_generator():
    broker = A2AMeshBroker()
    queue = broker.subscribe()

    chunk = StreamChunk(
        seq=0,
        persona="sakking",
        turn=1,
        chunk_type=ChunkType.TOOL_CALL,
        delta="ast_security_scan",
    )
    await broker.publish_chunk(chunk)

    gen = broker.sse_generator(queue)
    sse_text = await anext(gen)
    assert "id: 1" in sse_text
    assert "event: agent_delta" in sse_text
    assert "ast_security_scan" in sse_text

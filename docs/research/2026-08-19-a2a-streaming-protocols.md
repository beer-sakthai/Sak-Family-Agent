# Research Brief: Cross-Persona A2A Distributed Streaming Protocols

**Status:** Completed  
**Domain:** Multi-Agent Architecture & Distributed Streaming  
**Target Ecosystem:** Python 3.11+ (Agent Core) ↔ Next.js 15 App Router (War Room Dashboard)  
**Author:** SakJules · Master of Automation & CI/CD  

---

### Summary
This research brief evaluates **Server-Sent Events (SSE)**, **WebSockets (WS)**, and **gRPC / Protocol Buffers** for real-time inter-agent streaming, token arbitration, and consensus voting across the 6 Sak-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`). We recommend a **Hybrid Reactive Model**: in-memory async event emitters for intra-process CLI execution paired with **HTTP/2 Chunked SSE Envelopes** for Next.js web dashboard consumption and inter-process agent federation.

---

### Key Findings & Comparative Analysis

#### 1. Protocol Comparison Matrix

| Dimension | Server-Sent Events (SSE) | WebSockets (WS) | gRPC / HTTP/2 |
|---|---|---|---|
| **Directionality** | Unidirectional (Server $\to$ Client) | Full Duplex (Bi-directional) | Bidirectional Streaming |
| **Transport / Standard** | Standard HTTP/1.1 or HTTP/2 | Custom `ws://` / `wss://` upgrade | HTTP/2 + Binary Protobuf |
| **Next.js 15 App Router** | Native support via `ReadableStream` | Requires custom server or external proxy | Requires client wrapper / Node gRPC bindings |
| **Reconnection & Resilience** | Native browser auto-reconnect (`EventSource`, `Last-Event-ID`) | Manual ping/pong & reconnect logic | Built-in backoff in gRPC channels |
| **Corporate Firewalls / Proxies** | 100% transparent (standard HTTPS port 443) | Frequently blocked or degraded by enterprise proxies | May require explicit HTTP/2 proxy configuration |
| **Memory / CPU Overhead** | Ultra-low (stateless text chunk framing) | Moderate (persistent socket state) | Low (binary serialization) |
| **Backpressure Handling** | Native TCP window + pull stream flow control | Manual queue buffer watermark gating | Native HTTP/2 stream-level flow control |

---

#### 2. Deep Dive: Why SSE + REST Command RPC Outperforms Full Duplex WebSockets for A2A
1. **Firewall & Cloud Run/Vercel Compatibility:** Modern serverless and container runtimes (Cloud Run, Vercel Edge) support streaming HTTP chunk responses natively up to 60 minutes without WebSocket disconnection timeouts.
2. **Deterministic Sequence Recovery:** By indexing chunks with monotonic `seq` IDs and `Last-Event-ID`, dropped connections resume immediately from the exact token delta without losing state.
3. **Clean Asymmetry:** Agent-to-Agent streaming is primarily **producer-to-subscriber emission** (agent generation $\to$ observers) rather than high-frequency bi-directional socket chatter. Command dispatches (votes, interruptions) are clean atomic HTTP POST requests.

---

### Recommended Chunk Envelope Specification

```json
{
  "jsonrpc": "2.0",
  "event": "agent_delta",
  "id": "evt_01J...",
  "seq": 42,
  "timestamp": "2026-08-19T02:53:00Z",
  "data": {
    "persona": "saksee",
    "turn": 3,
    "chunk_type": "token",
    "delta": "Analyzing accessibility tree for DOM elements...",
    "stop_reason": null,
    "metrics": {
      "tokens_per_sec": 48.5,
      "latency_ms": 112
    }
  }
}
```

---

### Python & Next.js Implementation Blueprint

#### Python Async Streaming Generator (`personas/sakthai/sakthai/a2a/streaming.py`)
```python
import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

async def sse_event_generator(stream_queue: asyncio.Queue[dict[str, Any]]) -> AsyncIterator[str]:
    seq = 0
    while True:
        item = await stream_queue.get()
        if item.get("type") == "EOF":
            yield "event: done\ndata: {}\n\n"
            break
        seq += 1
        item["seq"] = seq
        payload = json.dumps(item, ensure_ascii=False)
        yield f"id: {seq}\nevent: agent_delta\ndata: {payload}\n\n"
```

#### Next.js 15 Edge Route Handler (`apps/sak_agent_dashboard/src/app/api/a2a/stream/route.ts`)
```typescript
import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const encoder = new TextEncoder();
  const customReadable = new ReadableStream({
    start(controller) {
      const sendEvent = (event: string, data: any) => {
        controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      };

      sendEvent("connected", { status: "ready", timestamp: Date.now() });

      req.signal.addEventListener("abort", () => {
        controller.close();
      });
    },
  });

  return new Response(customReadable, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
    },
  });
}
```

---

### Gotchas & Common Mistakes
1. **Next.js Buffering & Response Compression:** Cloudflare or reverse proxies will buffer SSE chunks if the `Cache-Control: no-transform` or `X-Accel-Buffering: no` headers are missing.
2. **EventSource Connection Limit:** HTTP/1.1 limits browsers to 6 concurrent SSE connections per domain. Always ensure HTTP/2 or multiplex multi-agent channels into a single SSE stream with topic multiplexing (`persona: sakking`, `persona: saksee`).
3. **Heartbeat Keepalive:** Middlebox routers drop idle TCP connections after 30-60s. The Python/Next.js publisher must emit a `: keepalive\n\n` ping every 15 seconds.

---

### Sources & Reference Standards
- [W3C Server-Sent Events Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Next.js 15 App Router Streaming Architecture](https://nextjs.org/docs/app/building-your-application/routing/route-handlers#streaming)
- [RFC 6455 - The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [RFC 7540 - Hypertext Transfer Protocol Version 2 (HTTP/2)](https://datatracker.ietf.org/doc/html/rfc7540)

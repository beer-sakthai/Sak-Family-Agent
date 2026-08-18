import { NextRequest } from "next/server";
import { telemetryBus } from "@/lib/telemetryBus";
import { TelemetryEvent } from "@/lib/types";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const personaFilter = searchParams.get("persona")?.toLowerCase();
  const severityFilter = searchParams.get("severity")?.toLowerCase();

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      // 1. Initial connection payload
      const initialEvent = telemetryBus.createConnectedEvent();
      controller.enqueue(
        encoder.encode(`event: connected\ndata: ${JSON.stringify(initialEvent)}\n\n`)
      );

      // 2. Flush recent buffered events matching filter
      const recent = telemetryBus.getRecentEvents(personaFilter, 15);
      for (const ev of recent) {
        controller.enqueue(
          encoder.encode(`event: ${ev.type}\ndata: ${JSON.stringify(ev)}\n\n`)
        );
      }

      // 3. Listener callback for live incoming events
      const onTelemetry = (event: TelemetryEvent) => {
        if (personaFilter && event.persona && event.persona.toLowerCase() !== personaFilter) {
          return;
        }
        if (severityFilter && event.type !== "agent_error" && event.type !== "guardrail_check") {
          return;
        }

        try {
          controller.enqueue(
            encoder.encode(`event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`)
          );
        } catch {
          // Controller might be closed
        }
      };

      telemetryBus.on("telemetry", onTelemetry);

      // 4. Heartbeat keepalive every 15s to prevent proxy timeouts
      const heartbeatTimer = setInterval(() => {
        try {
          controller.enqueue(
            encoder.encode(`event: heartbeat\ndata: ${JSON.stringify({ timestamp: new Date().toISOString() })}\n\n`)
          );
        } catch {
          clearInterval(heartbeatTimer);
        }
      }, 15000);

      // 5. Cleanup on connection abort
      req.signal.addEventListener("abort", () => {
        clearInterval(heartbeatTimer);
        telemetryBus.off("telemetry", onTelemetry);
        try {
          controller.close();
        } catch {
          // ignore if already closed
        }
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform, no-store",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

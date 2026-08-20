import { describe, it, expect } from "vitest";
import { telemetryBus } from "@/lib/telemetryBus";
import { GET as streamHandler } from "@/app/api/telemetry/stream/route";
import { POST as emitHandler } from "@/app/api/telemetry/emit/route";
import { NextRequest } from "next/server";

describe("Real-Time Telemetry & SSE Streaming Pipeline", () => {
  it("telemetryBus broadcasts events and stores in ring buffer", () => {
    const event = telemetryBus.emitEvent({
      type: "tool_call",
      persona: "SakThai",
      data: {
        toolName: "run_command",
        message: "Executing security check",
      },
    });

    expect(event.id).toBeDefined();
    expect(event.timestamp).toBeDefined();
    expect(event.type).toBe("tool_call");
    expect(event.persona).toBe("SakThai");
    expect(event.data.toolName).toBe("run_command");

    const recent = telemetryBus.getRecentEvents("SakThai");
    expect(recent.some((e) => e.id === event.id)).toBe(true);
  });

  it("telemetryBus filters history accurately by persona", () => {
    telemetryBus.emitEvent({
      type: "agent_start",
      persona: "SakKing",
      data: { message: "Starting vision analysis" },
    });

    const sakKingEvents = telemetryBus.getRecentEvents("SakKing");
    const sakSeeEvents = telemetryBus.getRecentEvents("SakSee");

    expect(sakKingEvents.every((e) => e.persona.toLowerCase() === "sakking")).toBe(true);
    expect(sakSeeEvents.every((e) => e.persona.toLowerCase() === "saksee")).toBe(true);
  });

  it("POST /api/telemetry/emit handles valid telemetry emission", async () => {
    const req = new NextRequest("http://localhost:3000/api/telemetry/emit", {
      method: "POST",
      body: JSON.stringify({
        type: "guardrail_check",
        persona: "SakJules",
        data: {
          guardrailAction: "ALLOW",
          guardrailRule: "rule_1_sensitive_paths",
        },
      }),
    });

    const res = await emitHandler(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.event.type).toBe("guardrail_check");
    expect(json.event.persona).toBe("SakJules");
    expect(json.event.data.guardrailAction).toBe("ALLOW");
  });

  it("POST /api/telemetry/emit rejects invalid requests missing required fields", async () => {
    const req = new NextRequest("http://localhost:3000/api/telemetry/emit", {
      method: "POST",
      body: JSON.stringify({
        // missing type & persona
        data: { foo: "bar" },
      }),
    });

    const res = await emitHandler(req);
    expect(res.status).toBe(400);

    const json = await res.json();
    expect(json.success).toBe(false);
  });

  it("GET /api/telemetry/stream returns SSE headers and readable stream", async () => {
    const req = new NextRequest("http://localhost:3000/api/telemetry/stream");
    const res = await streamHandler(req);

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain("text/event-stream");
    expect(res.headers.get("cache-control")).toContain("no-cache");
    expect(res.headers.get("connection")).toBe("keep-alive");
    expect(res.body).toBeDefined();
  });
});

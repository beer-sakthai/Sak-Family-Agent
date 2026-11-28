import { describe, expect, it, vi } from "vitest";
import { EventEmitter } from "node:events";

interface MockChildProcess extends EventEmitter {
  stdout: EventEmitter;
  stderr: EventEmitter;
  killed: boolean;
  kill: (signal?: string) => boolean;
}

const mockChild = new EventEmitter() as unknown as MockChildProcess;
mockChild.stdout = new EventEmitter();
mockChild.stderr = new EventEmitter();
mockChild.killed = false;
mockChild.kill = vi.fn().mockReturnValue(true);

vi.mock("node:child_process", () => ({
  spawn: vi.fn(() => mockChild),
}));

import { POST as runnerPOST } from "@/app/api/gateway/runner/route";

describe("POST /api/gateway/runner", () => {
  it("rejects invalid JSON request body with 400", async () => {
    const req = new Request("http://localhost/api/gateway/runner", {
      method: "POST",
      body: "invalid-json",
      headers: { "Content-Type": "application/json" },
    });
    const res = await runnerPOST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/Invalid JSON/i);
  });

  it("rejects invalid or missing persona with 400", async () => {
    const req = new Request("http://localhost/api/gateway/runner", {
      method: "POST",
      body: JSON.stringify({ persona: "unknown_bot", task: "Check status" }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await runnerPOST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/Invalid persona/i);
  });

  it("rejects empty or whitespace-only task with 400", async () => {
    const req = new Request("http://localhost/api/gateway/runner", {
      method: "POST",
      body: JSON.stringify({ persona: "sakthai", task: "   " }),
      headers: { "Content-Type": "application/json" },
    });
    const res = await runnerPOST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/Task must be a non-empty string/i);
  });

  it("streams starting status and child stdout/stderr events over SSE", async () => {
    const req = new Request("http://localhost/api/gateway/runner", {
      method: "POST",
      body: JSON.stringify({
        persona: "sakjules",
        task: "Check status",
        dryRun: true,
        fast: true,
      }),
      headers: { "Content-Type": "application/json" },
    });

    const res = await runnerPOST(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toContain("text/event-stream");

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();

    // 1. Read the initial "starting" status event
    const firstRead = await reader.read();
    expect(firstRead.done).toBe(false);
    const firstText = decoder.decode(firstRead.value);
    expect(firstText).toContain('"status":"starting"');
    expect(firstText).toContain('"persona":"sakjules"');
    expect(firstText).toContain('"dryRun":true');

    // 2. Emit simulated stdout from subprocess
    setTimeout(() => {
      mockChild.stdout.emit("data", Buffer.from("Preflight validation complete.\n"));
      mockChild.stderr.emit("data", Buffer.from("Warning: verbose flag active.\n"));
      mockChild.emit("close", 0, null);
    }, 10);

    let streamOutput = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      streamOutput += decoder.decode(value, { stream: true });
    }

    expect(streamOutput).toContain('"type":"stdout"');
    expect(streamOutput).toContain("Preflight validation complete.");
    expect(streamOutput).toContain('"type":"stderr"');
    expect(streamOutput).toContain("Warning: verbose flag active.");
    expect(streamOutput).toContain('"type":"exit"');
    expect(streamOutput).toContain('"code":0');
  });
});

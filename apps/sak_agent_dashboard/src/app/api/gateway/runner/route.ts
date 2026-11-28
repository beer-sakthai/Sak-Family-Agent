/**
 * `POST /api/gateway/runner` — Direct subprocess execution engine with streaming SSE.
 *
 * When the standalone Runtime Gateway (:8080) is offline, this route spawns
 * `sakthai run "<task>" --persona <persona>` as a secure child process and streams
 * stdout/stderr lines as Server-Sent Events directly to the dashboard terminal drawer.
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const VALID_PERSONAS = new Set([
  "sakthai",
  "sakking",
  "saksee",
  "sakjules",
  "saksit",
  "saktan",
]);

const VALID_PROVIDERS = new Set([
  "anthropic",
  "google",
  "openai",
  "ollama",
  "gateway",
  "huggingface",
]);

interface RunnerRequestBody {
  persona?: string;
  task?: string;
  dryRun?: boolean;
  fast?: boolean;
  stateless?: boolean;
  maxIterations?: number;
  model?: string;
  provider?: string;
}

function findRepoRoot(): string {
  let curr = process.cwd();
  for (let i = 0; i < 5; i++) {
    if (
      fs.existsSync(path.join(curr, "pyproject.toml")) &&
      fs.existsSync(path.join(curr, "personas"))
    ) {
      return curr;
    }
    const parent = path.dirname(curr);
    if (parent === curr) break;
    curr = parent;
  }
  return process.cwd();
}

export async function POST(request: Request): Promise<Response> {
  let body: RunnerRequestBody;
  try {
    body = (await request.json()) as RunnerRequestBody;
  } catch {
    return Response.json(
      { error: "Invalid JSON request body." },
      { status: 400 }
    );
  }

  const persona = body.persona?.trim().toLowerCase();
  if (!persona || !VALID_PERSONAS.has(persona)) {
    return Response.json(
      {
        error: `Invalid persona '${body.persona}'. Must be one of: ${Array.from(VALID_PERSONAS).join(", ")}`,
      },
      { status: 400 }
    );
  }

  const task = body.task?.trim();
  if (!task || task.length === 0) {
    return Response.json(
      { error: "Task must be a non-empty string." },
      { status: 400 }
    );
  }

  const repoRoot = findRepoRoot();
  const args: string[] = [
    "run",
    "sakthai",
    "run",
    task,
    "--persona",
    persona,
  ];

  if (body.dryRun) {
    args.push("--dry-run");
  }
  if (body.fast) {
    args.push("--fast");
  }
  if (body.stateless) {
    args.push("--stateless");
  }
  if (
    typeof body.maxIterations === "number" &&
    Number.isInteger(body.maxIterations) &&
    body.maxIterations >= 1 &&
    body.maxIterations <= 50
  ) {
    args.push("--max-iterations", String(body.maxIterations));
  }
  if (
    typeof body.model === "string" &&
    /^[a-zA-Z0-9_\-./:]+$/.test(body.model.trim())
  ) {
    args.push("--model", body.model.trim());
  }
  if (
    typeof body.provider === "string" &&
    VALID_PROVIDERS.has(body.provider.trim().toLowerCase())
  ) {
    args.push("--provider", body.provider.trim().toLowerCase());
  }

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      const sendEvent = (eventData: Record<string, unknown>) => {
        try {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(eventData)}\n\n`)
          );
        } catch {
          // Stream controller may be closed if client disconnected
        }
      };

      sendEvent({
        type: "status",
        status: "starting",
        persona,
        dryRun: Boolean(body.dryRun),
        cmd: `uv ${args.join(" ")}`,
        cwd: repoRoot,
        timestamp: new Date().toISOString(),
      });

      let child: ReturnType<typeof spawn> | null = null;
      try {
        child = spawn("uv", args, {
          cwd: repoRoot,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: "1",
          },
          shell: false,
        });

        child.stdout?.on("data", (chunk: Buffer) => {
          sendEvent({
            type: "stdout",
            text: chunk.toString("utf-8"),
          });
        });

        child.stderr?.on("data", (chunk: Buffer) => {
          sendEvent({
            type: "stderr",
            text: chunk.toString("utf-8"),
          });
        });

        child.on("error", (err: Error) => {
          sendEvent({
            type: "error",
            error: err.message,
          });
          sendEvent({
            type: "exit",
            code: 1,
          });
          controller.close();
        });

        child.on("close", (code: number | null, signal: string | null) => {
          sendEvent({
            type: "exit",
            code: code ?? 0,
            signal: signal ?? null,
            timestamp: new Date().toISOString(),
          });
          controller.close();
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        sendEvent({
          type: "error",
          error: `Failed to spawn process: ${message}`,
        });
        sendEvent({
          type: "exit",
          code: 1,
        });
        controller.close();
      }

      // Handle client cancellation/abort
      request.signal.addEventListener("abort", () => {
        if (child && !child.killed) {
          try {
            child.kill("SIGTERM");
          } catch {
            // ignore
          }
        }
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

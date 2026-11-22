import { NextRequest } from "next/server";

const DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080";

function getGatewayConfig() {
  const baseUrl = (
    process.env.SAKTHAI_GATEWAY_URL ||
    process.env.NEXT_PUBLIC_GATEWAY_URL ||
    DEFAULT_GATEWAY_URL
  ).replace(/\/$/, "");
  const token =
    process.env.SAKTHAI_GATEWAY_TOKEN ||
    process.env.SAKTHAI_API_TOKEN ||
    process.env.SAKTHAI_GATEWAY_BEARER_TOKEN ||
    "";
  return { baseUrl, token };
}

export async function GET(request: NextRequest) {
  const { baseUrl, token } = getGatewayConfig();
  const searchParams = request.nextUrl.searchParams;
  const pipeline = searchParams.get("pipeline") || "code-review";
  const task = searchParams.get("task") || "Audit repository";

  const targetUrl = new URL(`${baseUrl}/v1/team/pipelines/stream`);
  targetUrl.searchParams.set("pipeline", pipeline);
  targetUrl.searchParams.set("task", task);

  const headers: Record<string, string> = {
    Accept: "text/event-stream",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const upstreamRes = await fetch(targetUrl.toString(), {
      method: "GET",
      headers,
      cache: "no-store",
    });

    if (!upstreamRes.ok || !upstreamRes.body) {
      return new Response(
        `event: pipeline_error\ndata: ${JSON.stringify({ error: `Upstream error: ${upstreamRes.status}` })}\n\n`,
        {
          headers: {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        }
      );
    }

    return new Response(upstreamRes.body, {
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return new Response(
      `event: pipeline_error\ndata: ${JSON.stringify({ error: msg })}\n\n`,
      {
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      }
    );
  }
}

export async function POST(request: NextRequest) {
  const { baseUrl, token } = getGatewayConfig();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const body = await request.json();
    const upstreamRes = await fetch(`${baseUrl}/v1/team/pipelines/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!upstreamRes.ok || !upstreamRes.body) {
      return new Response(
        `event: pipeline_error\ndata: ${JSON.stringify({ error: `Upstream error: ${upstreamRes.status}` })}\n\n`,
        {
          headers: {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        }
      );
    }

    return new Response(upstreamRes.body, {
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return new Response(
      `event: pipeline_error\ndata: ${JSON.stringify({ error: msg })}\n\n`,
      {
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      }
    );
  }
}

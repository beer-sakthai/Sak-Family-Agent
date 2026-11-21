/**
 * `POST /api/gateway/chat` — Proxy chat completions to the SakThai Runtime Gateway.
 * Supports both streaming SSE (stream: true) and buffered JSON responses.
 */

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request): Promise<Response> {
  const gatewayUrl = (
    process.env.SAKTHAI_GATEWAY_URL ||
    process.env.NEXT_PUBLIC_GATEWAY_URL ||
    "http://127.0.0.1:8080"
  ).replace(/\/+$/, "");

  const token =
    process.env.SAKTHAI_GATEWAY_TOKEN ||
    process.env.SAKTHAI_GATEWAY_BEARER_TOKEN ||
    process.env.SAKTHAI_API_TOKEN;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { error: "Invalid JSON request body." },
      { status: 400 }
    );
  }

  const isStream =
    typeof body === "object" && body !== null && Boolean((body as Record<string, unknown>).stream);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token.trim()}`;
  }

  try {
    const upstreamRes = await fetch(`${gatewayUrl}/v1/chat/completions`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!upstreamRes.ok) {
      const errText = await upstreamRes.text();
      return Response.json(
        {
          error: `Upstream gateway error (HTTP ${upstreamRes.status})`,
          detail: errText,
        },
        { status: upstreamRes.status }
      );
    }

    if (isStream && upstreamRes.body) {
      // Pipe the SSE stream straight through to the browser
      return new Response(upstreamRes.body, {
        headers: {
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    const data = await upstreamRes.json();
    return Response.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      {
        error: "Failed to connect to Runtime Gateway.",
        detail: message,
        gateway_url: gatewayUrl,
      },
      { status: 502 }
    );
  }
}

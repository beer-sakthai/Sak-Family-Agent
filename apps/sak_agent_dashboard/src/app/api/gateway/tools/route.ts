/**
 * `GET /api/gateway/tools` — List tools exposed by the Runtime Gateway.
 * `POST /api/gateway/tools` — Execute a tool with DataLossGuardrail security.
 */

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function getGatewayConfig() {
  const gatewayUrl = (
    process.env.SAKTHAI_GATEWAY_URL ||
    process.env.NEXT_PUBLIC_GATEWAY_URL ||
    "http://127.0.0.1:8080"
  ).replace(/\/+$/, "");

  const token =
    process.env.SAKTHAI_GATEWAY_TOKEN ||
    process.env.SAKTHAI_GATEWAY_BEARER_TOKEN ||
    process.env.SAKTHAI_API_TOKEN;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token.trim()}`;
  }

  return { gatewayUrl, headers };
}

export async function GET(): Promise<Response> {
  const { gatewayUrl, headers } = getGatewayConfig();
  try {
    const res = await fetch(`${gatewayUrl}/v1/tools`, { headers, cache: "no-store" });
    if (!res.ok) {
      return Response.json(
        { error: `Upstream error ${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return Response.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      { error: "Could not reach Gateway /v1/tools", detail: message },
      { status: 502 }
    );
  }
}

export async function POST(request: Request): Promise<Response> {
  const { gatewayUrl, headers } = getGatewayConfig();
  try {
    const body = await request.json();
    const res = await fetch(`${gatewayUrl}/v1/tools/execute`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      { error: "Could not execute tool via Gateway", detail: message },
      { status: 502 }
    );
  }
}

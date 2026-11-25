import { NextRequest, NextResponse } from "next/server";

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
  const persona = request.nextUrl.searchParams.get("persona") || "sakjules";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${baseUrl}/v1/personas/${encodeURIComponent(persona)}/memory`, {
      method: "GET",
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        {
          ok: false,
          persona,
          error: `Gateway returned status ${res.status}: ${errText}`,
          facts_count: 0,
          observations_count: 0,
          facts: [],
          observations: [],
        },
        { status: 200 }
      );
    }
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        ok: false,
        persona,
        error: message,
        facts_count: 0,
        observations_count: 0,
        facts: [],
        observations: [],
      },
      { status: 200 }
    );
  }
}

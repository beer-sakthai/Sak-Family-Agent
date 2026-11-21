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

export async function GET() {
  const { baseUrl, token } = getGatewayConfig();
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${baseUrl}/v1/team/pipelines`, {
      method: "GET",
      headers,
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, error: message, count: 0, pipelines: [] },
      { status: 200 }
    );
  }
}

export async function POST(request: NextRequest) {
  const { baseUrl, token } = getGatewayConfig();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const body = await request.json();
    const res = await fetch(`${baseUrl}/v1/team/pipelines`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, status: "error", error: message },
      { status: 500 }
    );
  }
}

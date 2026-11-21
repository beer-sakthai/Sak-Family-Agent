/**
 * `GET /api/gateway/health` — Probe the local SakThai Runtime Gateway.
 */

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const gatewayUrl = (
    process.env.SAKTHAI_GATEWAY_URL ||
    process.env.NEXT_PUBLIC_GATEWAY_URL ||
    "http://127.0.0.1:8080"
  ).replace(/\/+$/, "");

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const res = await fetch(`${gatewayUrl}/health`, {
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      return Response.json({
        ok: true,
        gateway_url: gatewayUrl,
        ...data,
      });
    }

    return Response.json(
      {
        ok: false,
        gateway_url: gatewayUrl,
        status: "unhealthy",
        error: `HTTP ${res.status} from gateway`,
      },
      { status: 200 }
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return Response.json(
      {
        ok: false,
        gateway_url: gatewayUrl,
        status: "offline",
        message: `Gateway is offline or unreachable on ${gatewayUrl}. Start with: uv run sakthai gateway serve`,
        error: message,
      },
      { status: 200 }
    );
  }
}

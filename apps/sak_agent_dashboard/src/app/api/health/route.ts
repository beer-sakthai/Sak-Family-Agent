/**
 * `GET /api/health` — a liveness and configuration probe.
 *
 * Uptime monitors, and a `curl` after a deploy, need one URL that answers
 * without reading a memory shard. It reports which source *would* serve a data
 * request and why, which is the question a hosted deploy actually raises: a
 * page full of sample data looks identical to a page full of real data unless
 * you read the badge.
 *
 * It deliberately reports no paths, tokens or hostnames — only whether each is
 * configured. The dashboard has no auth of its own, so anything this returns
 * is public to whoever can reach the deployment.
 */

import { resolveSource } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const apiConfigured = Boolean(process.env.SAKTHAI_API_URL?.trim());

  let source: string;
  try {
    source = (await resolveSource(request)).kind;
  } catch {
    // A source that cannot even be constructed is worth reporting as such
    // rather than as a 500: the deployment is up, its data path is not.
    source = "unavailable";
  }

  const body = {
    ok: source !== "unavailable",
    status: source === "unavailable" ? "degraded" : "ok",
    source,
    /** Why that source: what a hosted deploy needs in order to show live data. */
    configuration: {
      api_url_configured: apiConfigured,
      api_token_configured: Boolean(process.env.SAKTHAI_API_TOKEN?.trim()),
      live: source === "local" || source === "api",
    },
    generated_at: new Date().toISOString(),
  };

  return Response.json(body, { status: body.ok ? 200 : 503 });
}

/** `GET /api/metrics` — run, latency and token aggregates over the eval log. */

import { intParam, respond } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const params = new URL(request.url).searchParams;
  const limit = intParam(params.get("limit"), 2000, 1, 20_000);
  return respond(request, (source) => source.getMetrics(limit));
}

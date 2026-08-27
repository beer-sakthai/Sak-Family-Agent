/**
 * `GET /api/audit` — security audit events from `audit.log`.
 *
 * Previously served from `/api/memory` alongside facts and observations, which
 * meant the severity filter could not be applied without also re-reading the
 * memory shards.
 */

import { intParam, respond } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const params = new URL(request.url).searchParams;
  return respond(request, (source) =>
    source.getAudit({
      severity: params.get("severity"),
      limit: intParam(params.get("limit"), 200, 1, 1000),
    }),
  );
}

/** `GET /api/memory` — facts and observations merged across persona shards. */

import { intParam, parsePersonas, respond } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const params = new URL(request.url).searchParams;
  return respond(request, (source) =>
    source.getMemory({
      query: params.get("query"),
      limit: intParam(params.get("limit"), 100, 1, 500),
      personas: parsePersonas(params.get("persona")),
    }),
  );
}

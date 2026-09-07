/** `GET /api/sessions` — session summaries, and one transcript via `?id=`. */

import { intParam, parsePersonas, respond } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const params = new URL(request.url).searchParams;
  return respond(request, (source) =>
    source.getSessions({
      // `search` is the documented name; `query` stays accepted since the
      // existing frontend sends it.
      search: params.get("search") ?? params.get("query"),
      limit: intParam(params.get("limit"), 20, 1, 100),
      offset: intParam(params.get("offset"), 0, 0, 1_000_000),
      id: params.get("id"),
      personas: parsePersonas(params.get("persona")),
    }),
  );
}

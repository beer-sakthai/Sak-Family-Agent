import { createApiHandler } from "@/lib/api/handler";
import { getSessionTranscripts } from "@/lib/sakthai";

export const GET = createApiHandler("/api/sessions", async (ctx) => {
  const search = ctx.params.search || ctx.params.query || undefined;
  const id = ctx.params.id || undefined;

  const rawLimit = ctx.params.limit;
  const rawOffset = ctx.params.offset;

  const limit = rawLimit !== undefined ? parseInt(rawLimit, 10) : 20;
  const offset = rawOffset !== undefined ? parseInt(rawOffset, 10) : 0;

  const result = await getSessionTranscripts({
    demo: ctx.demo,
    search,
    limit,
    offset,
    id,
  });

  return {
    sessions: result.sessions,
    total: result.total,
    dataSource: result.dataSource,
    ...(result.detail ? { detail: result.detail } : {}),
  };
});

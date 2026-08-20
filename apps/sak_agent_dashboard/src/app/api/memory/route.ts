import { createApiHandler } from "@/lib/api/handler";
import { getMemoryData } from "@/lib/db";
import { getAuditLogs } from "@/lib/sakthai";

export const GET = createApiHandler("/api/memory", async (ctx) => {
  const query = ctx.params.query || undefined;
  const severity = ctx.params.severity || undefined;

  const { memory, dataSource } = await getMemoryData(ctx.demo, query);
  const { logs: auditLogs, dataSource: auditDataSource } = await getAuditLogs(
    ctx.demo,
    severity
  );

  return { memory, auditLogs, dataSource, auditDataSource };
});

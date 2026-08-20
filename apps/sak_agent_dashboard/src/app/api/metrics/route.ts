import { createApiHandler } from "@/lib/api/handler";
import { getMetricsSummary } from "@/lib/sakthai";

export const GET = createApiHandler("/api/metrics", async (ctx) => {
  const { metrics, dataSource } = await getMetricsSummary(ctx.demo);
  return { metrics, dataSource };
});

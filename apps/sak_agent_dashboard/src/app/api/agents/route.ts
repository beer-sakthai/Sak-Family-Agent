import { createApiHandler } from "@/lib/api/handler";
import { getAgentOverview } from "@/lib/sakthai";

export const GET = createApiHandler("/api/agents", async (ctx) => {
  const { agents, dataSource, unattributedRuns } = await getAgentOverview(ctx.demo);
  return { agents, dataSource, unattributedRuns };
});

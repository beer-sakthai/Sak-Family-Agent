import { createApiHandler } from "@/lib/api/handler";
import { getGatewayData } from "@/lib/agentGateway";

export const GET = createApiHandler("/api/agent-gateway", async () => {
  const gateway = getGatewayData();
  return { gateway };
});

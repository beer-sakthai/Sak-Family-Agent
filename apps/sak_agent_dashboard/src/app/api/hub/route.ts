import { createApiHandler } from "@/lib/api/handler";
import { getHubEcosystemData } from "@/lib/hub";

export const GET = createApiHandler("/api/hub", async () => {
  const data = getHubEcosystemData();
  return { data };
});

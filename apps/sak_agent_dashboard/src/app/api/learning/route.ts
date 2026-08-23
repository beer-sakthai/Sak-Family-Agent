import { createApiHandler } from "@/lib/api/handler";
import { getSelfEvolutionData } from "@/lib/selfEvolution";

export const GET = createApiHandler("/api/learning", async () => {
  const data = getSelfEvolutionData();
  return { data };
});

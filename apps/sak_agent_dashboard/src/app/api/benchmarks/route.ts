import { createApiHandler } from "@/lib/api/handler";
import { getBenchmarkArenaData } from "@/lib/benchmarks";

export const GET = createApiHandler("/api/benchmarks", async () => {
  const data = getBenchmarkArenaData();
  return { data };
});

import { createApiHandler } from "@/lib/api/handler";
import { getSpecKitData } from "@/lib/speckit";

export const GET = createApiHandler("/api/speckit", async () => {
  const speckit = getSpecKitData();
  return { speckit };
});

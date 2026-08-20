import { createApiHandler } from "@/lib/api/handler";
import { getAntigravityData } from "@/lib/antigravity";

export const GET = createApiHandler("/api/antigravity", async () => {
  const antigravity = getAntigravityData();
  return { antigravity };
});

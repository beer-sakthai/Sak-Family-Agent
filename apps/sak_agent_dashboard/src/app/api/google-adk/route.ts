import { createApiHandler } from "@/lib/api/handler";
import { getAdkData } from "@/lib/googleAdk";

export const GET = createApiHandler("/api/google-adk", async () => {
  const adk = getAdkData();
  return { adk };
});

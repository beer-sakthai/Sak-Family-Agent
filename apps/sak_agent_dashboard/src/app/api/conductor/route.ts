import { createApiHandler } from "@/lib/api/handler";
import { getConductorData } from "@/lib/conductor";

export const GET = createApiHandler("/api/conductor", async () => {
  const conductor = getConductorData();
  return { conductor };
});

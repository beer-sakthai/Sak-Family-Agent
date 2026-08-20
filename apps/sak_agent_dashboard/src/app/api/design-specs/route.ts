import { createApiHandler } from "@/lib/api/handler";
import { getDesignSpecsData } from "@/lib/designSpecs";

export const GET = createApiHandler("/api/design-specs", async () => {
  const specs = getDesignSpecsData();
  return { specs };
});

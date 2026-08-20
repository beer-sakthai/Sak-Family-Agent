import { createApiHandler } from "@/lib/api/handler";
import { getGcpLearningData } from "@/lib/gcpLearning";

export const GET = createApiHandler("/api/gcp-learning", async () => {
  const learning = getGcpLearningData();
  return { learning };
});

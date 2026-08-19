import { createApiHandler } from "@/lib/api/handler";
import { getGenkitData } from "@/lib/genkit";

export const GET = createApiHandler("/api/genkit", async () => {
  const genkit = getGenkitData();
  return { genkit };
});

import { createApiHandler } from "@/lib/api/handler";
import { getChatKitData } from "@/lib/chatkit";

export const GET = createApiHandler("/api/chatkit", async () => {
  const chatkit = getChatKitData();
  return { chatkit };
});

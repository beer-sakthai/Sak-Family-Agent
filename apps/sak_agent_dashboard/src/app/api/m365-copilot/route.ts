import { createApiHandler } from "@/lib/api/handler";
import { getM365CopilotData } from "@/lib/m365Copilot";

export const GET = createApiHandler("/api/m365-copilot", async () => {
  const m365 = getM365CopilotData();
  return { m365 };
});

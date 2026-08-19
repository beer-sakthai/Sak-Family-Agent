import { createApiHandler } from "@/lib/api/handler";
import { getMcpSdkData } from "@/lib/mcpSdk";

export const GET = createApiHandler("/api/mcp-sdk", async () => {
  const sdk = getMcpSdkData();
  return { sdk };
});

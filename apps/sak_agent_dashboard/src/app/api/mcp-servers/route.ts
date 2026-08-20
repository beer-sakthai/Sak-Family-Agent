import { createApiHandler } from "@/lib/api/handler";
import { getMcpServers } from "@/lib/mcpServers";

export const GET = createApiHandler("/api/mcp-servers", async () => {
  const servers = getMcpServers();
  return { servers };
});

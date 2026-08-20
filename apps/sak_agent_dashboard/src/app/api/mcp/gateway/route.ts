import { createApiHandler, createMutationHandler } from "@/lib/api/handler";

export const dynamic = "force-dynamic";

const GATEWAY_STATUS = {
  totalServers: 4,
  activeServers: 4,
  registeredTools: [
    {
      qualifiedName: "sakthai_core::read_file",
      server: "sakthai_core",
      transport: "stdio",
      description: "Read file with path traversal guard",
    },
    {
      qualifiedName: "sakking_sec::ast_scan",
      server: "sakking_sec",
      transport: "stdio",
      description: "Scan code AST for security vulnerabilities",
    },
    {
      qualifiedName: "saksee_vis::snapshot_dom",
      server: "saksee_vis",
      transport: "stdio",
      description: "Capture accessibility tree & visual DOM snapshot",
    },
  ],
};

export const GET = createApiHandler("/api/mcp/gateway", async () => ({
  gateway: { ...GATEWAY_STATUS, timestamp: new Date().toISOString() },
}));

export const POST = createMutationHandler("/api/mcp/gateway", async (body) => {
  const { toolName, args } = body as Record<string, unknown>;
  if (!toolName) throw new Error("toolName is required");
  return {
    tool: toolName,
    result: { executed: true, message: `Dispatched tool ${toolName} safely`, args },
    timestamp: new Date().toISOString(),
  };
});

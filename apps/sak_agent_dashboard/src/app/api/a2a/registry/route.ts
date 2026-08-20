import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";
import { ServiceRegistry } from "@/lib/a2a/serviceRegistry";
import { A2AEngine } from "@/lib/a2a/a2aEngine";
import { A2ACapabilityDescriptor, A2ADelegationRequest } from "@/lib/a2a/types";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/a2a/registry", async () => {
  const fleet = ServiceRegistry.getAllAgents();
  const health = ServiceRegistry.getFleetHealth();
  const delegations = A2AEngine.getRecentDelegations();
  return { data: { fleet, health, delegations } };
});

export const POST = createMutationHandler(
  "/api/a2a/registry",
  async (body) => {
    const { action } = body as Record<string, string>;

    if (action === "delegate") {
      const delegationReq: A2ADelegationRequest = {
        agentFrom: String(body.agentFrom ?? ""),
        agentTo: String(body.agentTo ?? ""),
        capabilityId: String(body.capabilityId ?? ""),
        payload: (body.payload as Record<string, unknown>) ?? {},
      };
      const result = await A2AEngine.delegateTask(delegationReq);
      return { result };
    }

    if (action === "heartbeat") {
      ServiceRegistry.recordHeartbeat(String(body.agentSlug ?? ""));
      return { recorded: true };
    }

    if (action === "discover") {
      const capabilities = ServiceRegistry.discoverCapabilities(
        body.category as A2ACapabilityDescriptor["category"],
      );
      return { capabilities };
    }

    throw new ApiError(400, `Invalid action: ${action}`);
  },
);

import { createApiHandler, createMutationHandler, ApiError } from "@/lib/api/handler";
import { getWorkflows, getWorkflowById, executeWorkflow } from "@/lib/workflowEngine";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/workflow", async (ctx) => {
  const id = ctx.params["id"];

  if (id) {
    const workflow = getWorkflowById(id);
    if (!workflow) throw new ApiError(404, `Workflow with id '${id}' not found`);
    return { workflow };
  }

  const workflows = getWorkflows();
  return { workflows, total: workflows.length, timestamp: new Date().toISOString() };
});

export const POST = createMutationHandler("/api/workflow", async (body) => {
  const { workflowId } = body as Record<string, unknown>;
  if (!workflowId) throw new ApiError(400, "Missing required field 'workflowId'");
  return { result: await executeWorkflow(String(workflowId)) };
});

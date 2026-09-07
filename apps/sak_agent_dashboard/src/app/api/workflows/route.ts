/** `GET /api/workflows` — agent_workflow run history; `?id=` for one run. */

import type { WorkflowRunDetail, WorkflowsPayload } from "@/lib/contracts.generated";
import { intParam, respond } from "@/lib/source";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const params = new URL(request.url).searchParams;
  const runId = params.get("id");
  // The two branches return different shapes, so the union is spelled out
  // rather than left to inference over the ternary.
  return respond<WorkflowsPayload | WorkflowRunDetail | null>(request, (source) =>
    runId
      ? source.getWorkflow(runId)
      : source.getWorkflows(intParam(params.get("limit"), 100, 1, 500)),
  );
}

import { NextRequest, NextResponse } from "next/server";
import {
  getWorkflows,
  getWorkflowById,
  executeWorkflow,
  validateWorkflowDAG,
  getRunHistories,
  getRunHistoryById,
} from "@/lib/workflowEngine";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    const runs = searchParams.get("runs");
    const runId = searchParams.get("runId");

    if (runId) {
      const history = getRunHistoryById(runId);
      if (!history) {
        return NextResponse.json(
          { success: false, error: `Run history for '${runId}' not found` },
          { status: 404 }
        );
      }
      return NextResponse.json({ success: true, run: history });
    }

    if (runs === "true") {
      const runList = getRunHistories();
      return NextResponse.json({
        success: true,
        runs: runList,
        total: runList.length,
      });
    }

    if (id) {
      const wf = getWorkflowById(id);
      if (!wf) {
        return NextResponse.json(
          { success: false, error: `Workflow with id '${id}' not found` },
          { status: 404 }
        );
      }
      return NextResponse.json({ success: true, workflow: wf });
    }

    const workflows = getWorkflows();
    return NextResponse.json({
      success: true,
      workflows,
      total: workflows.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch workflows",
      },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { workflowId, customWorkflow, params, validateOnly } = body;

    if (!workflowId && !customWorkflow) {
      return NextResponse.json(
        { success: false, error: "Missing required field 'workflowId' or 'customWorkflow'" },
        { status: 400 }
      );
    }

    const targetWorkflow = customWorkflow || (workflowId ? getWorkflowById(String(workflowId)) : undefined);
    if (!targetWorkflow) {
      return NextResponse.json(
        { success: false, error: `Workflow with id '${workflowId}' not found` },
        { status: 404 }
      );
    }

    const validation = validateWorkflowDAG(targetWorkflow);
    if (!validation.isValid) {
      return NextResponse.json(
        {
          success: false,
          error: "Invalid workflow DAG topology",
          validationErrors: validation.errors,
        },
        { status: 422 }
      );
    }

    if (validateOnly) {
      return NextResponse.json({
        success: true,
        valid: true,
        validation,
      });
    }

    const result = await executeWorkflow(
      String(workflowId || targetWorkflow.id),
      customWorkflow,
      params
    );

    return NextResponse.json({
      success: true,
      result,
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Failed to execute workflow",
      },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from "next/server";
import { getWorkflows, getWorkflowById, executeWorkflow } from "@/lib/workflowEngine";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");

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
    const { workflowId } = body;

    if (!workflowId) {
      return NextResponse.json(
        { success: false, error: "Missing required field 'workflowId'" },
        { status: 400 }
      );
    }

    const result = await executeWorkflow(String(workflowId));
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

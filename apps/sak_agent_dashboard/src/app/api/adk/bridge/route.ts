import { NextRequest, NextResponse } from 'next/server';
import {
  generateAdkPythonCode,
  generateCloudDeploymentManifest,
  getAgentRegistryStatus,
  getAllAdkSpecs,
  runQualityFlywheelEvaluation,
} from '../../../../lib/adk/adk_engine';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const agents = getAllAdkSpecs();
    const manifest = generateCloudDeploymentManifest('cloud_run');
    const evalResult = runQualityFlywheelEvaluation();
    const registryStatus = getAgentRegistryStatus();

    return NextResponse.json({
      agents,
      manifest,
      evalResult,
      registryStatus,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to retrieve ADK bridge data' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const action = body.action || 'generate_manifest';

    if (action === 'generate_code') {
      const code = generateAdkPythonCode(body.personaSlug || 'sakthai');
      return NextResponse.json({ success: true, code });
    }

    if (action === 'generate_manifest') {
      const manifest = generateCloudDeploymentManifest(
        body.target || 'cloud_run',
        body.serviceName || 'sak-family-adk-service',
        body.region || 'us-central1'
      );
      return NextResponse.json({ success: true, manifest });
    }

    if (action === 'run_eval') {
      const evalResult = runQualityFlywheelEvaluation();
      return NextResponse.json({ success: true, evalResult });
    }

    return NextResponse.json({ error: `Unknown action: ${action}` }, { status: 400 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to process ADK bridge action' },
      { status: 500 }
    );
  }
}

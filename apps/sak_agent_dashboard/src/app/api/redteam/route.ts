import { NextRequest, NextResponse } from 'next/server';
import { RedTeamEngine } from '@/lib/redteam/redTeamEngine';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'all';

    if (action === 'sweeps') {
      const sweeps = RedTeamEngine.getRecentSweeps();
      return NextResponse.json({ success: true, sweeps });
    }

    if (action === 'verdicts') {
      const verdicts = RedTeamEngine.getVerdicts();
      return NextResponse.json({ success: true, verdicts });
    }

    const sweeps = RedTeamEngine.getRecentSweeps();
    const payloads = RedTeamEngine.getPayloads();
    const verdicts = RedTeamEngine.getVerdicts();

    return NextResponse.json({
      success: true,
      data: {
        sweeps,
        payloads,
        verdicts,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown red-team error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'fuzz_sweep') {
      const summary = await RedTeamEngine.runFuzzSweep({
        targetPersonas: body.targetPersonas || ['saksee'],
        vectors: body.vectors,
      });

      const verdicts = RedTeamEngine.getVerdicts();
      return NextResponse.json({ success: true, summary, verdicts });
    }

    if (action === 'test_payload') {
      const { payload } = body;
      if (!payload || !payload.rawPayload) {
        return NextResponse.json(
          { success: false, error: 'Missing payload object or rawPayload string' },
          { status: 400 }
        );
      }

      const verdict = RedTeamEngine.evaluatePayloadDefense(payload);
      return NextResponse.json({ success: true, verdict });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown red-team error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

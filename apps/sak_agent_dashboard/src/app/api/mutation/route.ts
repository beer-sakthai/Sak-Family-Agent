import { NextRequest, NextResponse } from 'next/server';
import { MutationEngine } from '@/lib/mutation/mutationEngine';
import { SelfHealingTestGenerator } from '@/lib/mutation/selfHealingTestGenerator';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'all';
    const sweepId = searchParams.get('sweepId') || undefined;

    if (action === 'sweeps') {
      const sweeps = MutationEngine.getRecentSweeps();
      return NextResponse.json({ success: true, sweeps });
    }

    if (action === 'mutants') {
      const mutants = MutationEngine.getMutants(sweepId);
      return NextResponse.json({ success: true, mutants });
    }

    const sweeps = MutationEngine.getRecentSweeps();
    const mutants = MutationEngine.getMutants(sweepId);

    return NextResponse.json({
      success: true,
      data: {
        sweeps,
        mutants
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown mutation error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'sweep') {
      const targetFiles = body.targetFiles || ['src/lib/eval/evalEngine.ts', 'src/lib/cache/semanticCacheEngine.ts'];
      const operators = body.operators || [
        'conditional_inversion',
        'boolean_flip',
        'arithmetic_boundary',
        'return_value_substitution'
      ];

      const summary = await MutationEngine.runSweep({
        targetFiles,
        operators,
        timeoutMs: body.timeoutMs || 5000,
        concurrency: body.concurrency || 2
      });

      const mutants = MutationEngine.getMutants(summary.sweepId);
      return NextResponse.json({ success: true, summary, mutants });
    }

    if (action === 'heal') {
      const { mutantId } = body;
      const mutants = MutationEngine.getMutants();
      const mutant = mutants.find((m) => m.id === mutantId);

      if (!mutant) {
        return NextResponse.json({ success: false, error: `Mutant ${mutantId} not found` }, { status: 404 });
      }

      const healResult = SelfHealingTestGenerator.synthesizeHealerTest(mutant);
      return NextResponse.json({ success: true, healResult });
    }

    if (action === 'batch_heal') {
      const mutants = MutationEngine.getMutants(body.sweepId);
      const healResults = SelfHealingTestGenerator.batchHeal(mutants);
      return NextResponse.json({ success: true, healResults });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown mutation error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

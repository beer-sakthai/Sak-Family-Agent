import { NextRequest, NextResponse } from 'next/server';
import { EvalEngine } from '@/lib/eval/evalEngine';
import { QualityFlywheelEngine } from '@/lib/eval/qualityFlywheel';
import { GOLDEN_TEST_CASES, generateSyntheticTestCase } from '@/lib/eval/datasets';
import { EvalRunConfig } from '@/lib/eval/types';

// In-memory cache of recent evaluation run results
let cachedRunResults: ReturnType<typeof EvalEngine.judgeTrace> extends unknown
  ? import('@/lib/eval/types').EvalRunResult[]
  : never = [];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'all';

    if (action === 'datasets') {
      const datasets = QualityFlywheelEngine.getDatasets();
      return NextResponse.json({ success: true, datasets });
    }

    if (action === 'failures') {
      const failures = QualityFlywheelEngine.getFailureEntries();
      return NextResponse.json({ success: true, failures });
    }

    if (action === 'test_cases') {
      const persona = searchParams.get('persona') || undefined;
      const testCases = persona
        ? GOLDEN_TEST_CASES.filter((t) => t.personaSlug === persona)
        : GOLDEN_TEST_CASES;
      return NextResponse.json({ success: true, testCases });
    }

    if (action === 'export_jsonl') {
      const datasetId = searchParams.get('datasetId') || 'dataset-core-golden';
      const jsonl = QualityFlywheelEngine.exportDatasetAsJsonl(datasetId);
      return new NextResponse(jsonl, {
        headers: {
          'Content-Type': 'application/x-ndjson',
          'Content-Disposition': `attachment; filename="${datasetId}.jsonl"`
        }
      });
    }

    // Default: return complete studio bundle
    const datasets = QualityFlywheelEngine.getDatasets();
    const failures = QualityFlywheelEngine.getFailureEntries();
    const summaries = cachedRunResults.length > 0
      ? EvalEngine.calculatePersonaBenchmarkSummaries(cachedRunResults)
      : [];

    return NextResponse.json({
      success: true,
      data: {
        datasets,
        failures,
        testCases: GOLDEN_TEST_CASES,
        recentRuns: cachedRunResults.slice(0, 20),
        summaries
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown evaluation error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'run_eval') {
      const config: EvalRunConfig = body.config || {
        personaSlugs: ['all'],
        judgeModel: 'gemini-1.5-pro',
        concurrency: 2,
        enableCoT: true,
        enableOrderShuffling: true,
        passThreshold: 75
      };

      const selectedIds: string[] = body.testCaseIds || [];
      const testCasesToRun = selectedIds.length > 0
        ? GOLDEN_TEST_CASES.filter((t) => selectedIds.includes(t.id))
        : (config.personaSlugs.includes('all')
          ? GOLDEN_TEST_CASES
          : GOLDEN_TEST_CASES.filter((t) => config.personaSlugs.includes(t.personaSlug)));

      const results = await EvalEngine.runBatchEvaluation(testCasesToRun, config);

      // Ingest any failures into Flywheel queue
      for (const res of results) {
        if (!res.judgeScore?.passed) {
          QualityFlywheelEngine.ingestFailure(res);
        }
      }

      cachedRunResults = [...results, ...cachedRunResults].slice(0, 50);
      const summaries = EvalEngine.calculatePersonaBenchmarkSummaries(cachedRunResults);

      return NextResponse.json({
        success: true,
        results,
        summaries,
        report: EvalEngine.generateBenchmarkReport(results, 'markdown')
      });
    }

    if (action === 'triage_failure') {
      const { failureId, triageStatus, promoteToGolden } = body;
      if (!failureId) {
        return NextResponse.json({ success: false, error: 'failureId is required' }, { status: 400 });
      }

      let promotedTestCase = null;
      if (promoteToGolden) {
        promotedTestCase = QualityFlywheelEngine.promoteFailureToGoldenTestCase(failureId);
      } else if (triageStatus) {
        QualityFlywheelEngine.updateTriageStatus(failureId, triageStatus);
      }

      return NextResponse.json({
        success: true,
        promotedTestCase,
        failures: QualityFlywheelEngine.getFailureEntries()
      });
    }

    if (action === 'generate_synthetic') {
      const { personaSlug, category, mutationType } = body;
      const testCase = generateSyntheticTestCase(
        personaSlug || 'sakjules',
        category || 'coding',
        mutationType || 'boundary_values'
      );
      return NextResponse.json({ success: true, testCase });
    }

    if (action === 'create_dataset') {
      const { name, description, persona, testCases } = body;
      const dataset = QualityFlywheelEngine.createCustomDataset(
        name || 'Custom Dataset',
        description || '',
        persona || 'all',
        testCases || []
      );
      return NextResponse.json({ success: true, dataset });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown evaluation error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

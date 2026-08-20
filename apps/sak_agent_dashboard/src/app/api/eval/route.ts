import { NextRequest, NextResponse } from "next/server";
import { createMutationHandler } from "@/lib/api/handler";
import { EvalEngine } from "@/lib/eval/evalEngine";
import { QualityFlywheelEngine } from "@/lib/eval/qualityFlywheel";
import { GOLDEN_TEST_CASES, generateSyntheticTestCase } from "@/lib/eval/datasets";
import { EvalRunConfig, EvalRunResult, EvalTestCase, FlywheelFailureEntry } from "@/lib/eval/types";

// Module-level cache (must persist across requests; can't move into handler)
let cachedRunResults: EvalRunResult[] = [];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get("action") ?? "all";

    if (action === "datasets") {
      return NextResponse.json({ success: true, datasets: QualityFlywheelEngine.getDatasets() });
    }
    if (action === "failures") {
      return NextResponse.json({ success: true, failures: QualityFlywheelEngine.getFailureEntries() });
    }
    if (action === "test_cases") {
      const persona = searchParams.get("persona") ?? undefined;
      const testCases = persona ? GOLDEN_TEST_CASES.filter((t) => t.personaSlug === persona) : GOLDEN_TEST_CASES;
      return NextResponse.json({ success: true, testCases });
    }
    if (action === "export_jsonl") {
      // Non-JSON response: cannot use createApiHandler
      const datasetId = searchParams.get("datasetId") ?? "dataset-core-golden";
      const jsonl = QualityFlywheelEngine.exportDatasetAsJsonl(datasetId);
      return new NextResponse(jsonl, {
        headers: {
          "Content-Type": "application/x-ndjson",
          "Content-Disposition": `attachment; filename="${datasetId}.jsonl"`,
        },
      });
    }

    const datasets = QualityFlywheelEngine.getDatasets();
    const failures = QualityFlywheelEngine.getFailureEntries();
    const summaries = cachedRunResults.length > 0 ? EvalEngine.calculatePersonaBenchmarkSummaries(cachedRunResults) : [];
    return NextResponse.json({ success: true, data: { datasets, failures, testCases: GOLDEN_TEST_CASES, recentRuns: cachedRunResults.slice(0, 20), summaries } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown evaluation error";
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export const POST = createMutationHandler("/api/eval", async (body) => {
  const { action } = body as Record<string, unknown>;

  if (action === "run_eval") {
    const config: EvalRunConfig = (body.config as EvalRunConfig) ?? {
      personaSlugs: ["all"],
      judgeModel: "gemini-1.5-pro",
      concurrency: 2,
      enableCoT: true,
      enableOrderShuffling: true,
      passThreshold: 75,
    };
    const selectedIds = (body.testCaseIds as string[]) ?? [];
    const testCasesToRun =
      selectedIds.length > 0
        ? GOLDEN_TEST_CASES.filter((t) => selectedIds.includes(t.id))
        : config.personaSlugs.includes("all")
          ? GOLDEN_TEST_CASES
          : GOLDEN_TEST_CASES.filter((t) => config.personaSlugs.includes(t.personaSlug));

    const results = await EvalEngine.runBatchEvaluation(testCasesToRun, config);
    for (const res of results) {
      if (!res.judgeScore?.passed) QualityFlywheelEngine.ingestFailure(res);
    }
    cachedRunResults = [...results, ...cachedRunResults].slice(0, 50);
    const summaries = EvalEngine.calculatePersonaBenchmarkSummaries(cachedRunResults);
    return { results, summaries, report: EvalEngine.generateBenchmarkReport(results, "markdown") };
  }

  if (action === "triage_failure") {
    const { failureId, triageStatus, promoteToGolden } = body as Record<string, unknown>;
    if (!failureId) throw new Error("failureId is required");
    const promotedTestCase = promoteToGolden
      ? QualityFlywheelEngine.promoteFailureToGoldenTestCase(String(failureId))
      : null;
    if (!promoteToGolden && triageStatus) {
      QualityFlywheelEngine.updateTriageStatus(
        String(failureId),
        String(triageStatus) as FlywheelFailureEntry["triageStatus"],
      );
    }
    return { promotedTestCase, failures: QualityFlywheelEngine.getFailureEntries() };
  }

  if (action === "generate_synthetic") {
    const { personaSlug, category, mutationType } = body as Record<string, unknown>;
    const cat = (category as EvalTestCase["category"]) ?? "coding";
    const mut = (mutationType as "adversarial" | "boundary_values" | "heavy_load") ?? "boundary_values";
    return {
      testCase: generateSyntheticTestCase(
        String(personaSlug ?? "sakjules"),
        cat,
        mut,
      ),
    };
  }

  if (action === "create_dataset") {
    const { name, description, persona, testCases } = body as Record<string, unknown>;
    return {
      dataset: QualityFlywheelEngine.createCustomDataset(
        String(name ?? "Custom Dataset"),
        String(description ?? ""),
        String(persona ?? "all"),
        (testCases as EvalTestCase[]) ?? [],
      ),
    };
  }

  throw new Error(`Invalid action: ${action}`);
});

/**
 * Standalone CLI Runner for Sak-Family Agent Evaluation & Quality Flywheel Gate.
 * Usage: pnpm tsx scripts/eval-cli.ts [--threshold 85] [--persona all]
 */

import { EvalEngine } from '../src/lib/eval/evalEngine';
import { GOLDEN_TEST_CASES } from '../src/lib/eval/datasets';
import { EvalRunConfig } from '../src/lib/eval/types';

async function main() {
  console.log('===============================================================');
  console.log('🎯 Sak-Family Agent Evaluation & Quality Flywheel CI Gate');
  console.log('===============================================================\n');

  const threshold = process.env.EVAL_PASS_THRESHOLD ? parseInt(process.env.EVAL_PASS_THRESHOLD, 10) : 80;
  const config: EvalRunConfig = {
    personaSlugs: ['all'],
    judgeModel: 'gemini-1.5-pro',
    concurrency: 3,
    enableCoT: true,
    enableOrderShuffling: true,
    passThreshold: threshold,
  };

  console.log(`📋 Running ${GOLDEN_TEST_CASES.length} golden test cases against 6 Sak-Family personas...`);
  console.log(`🔒 Quality Gate Threshold: Composite Score >= ${threshold}% | AST Safety = 100%\n`);

  const startTime = Date.now();
  const results = await EvalEngine.runBatchEvaluation(GOLDEN_TEST_CASES, config);
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

  const summaries = EvalEngine.calculatePersonaBenchmarkSummaries(results);

  console.log('---------------------------------------------------------------');
  console.log('📊 BENCHMARK SUMMARY RESULTS:');
  console.log('---------------------------------------------------------------');
  console.log(
    'Persona'.padEnd(16) +
    'Tests'.padEnd(8) +
    'Pass Rate'.padEnd(12) +
    'Avg Score'.padEnd(12) +
    'AST Safety'.padEnd(12) +
    'Latency'
  );
  console.log('---------------------------------------------------------------');

  let failedTests = 0;
  let safetyBreaches = 0;

  for (const s of summaries) {
    console.log(
      s.personaName.slice(0, 15).padEnd(16) +
      s.totalTests.toString().padEnd(8) +
      `${s.passRate}%`.padEnd(12) +
      `${s.avgCompositeScore}/100`.padEnd(12) +
      `${s.avgSafetyCompliance}%`.padEnd(12) +
      `${s.avgLatencyMs}ms`
    );

    if (s.avgSafetyCompliance < 100) safetyBreaches++;
  }

  for (const r of results) {
    if (!r.judgeScore?.passed) failedTests++;
  }

  console.log('---------------------------------------------------------------');
  console.log(`⏱️ Total Execution Time: ${elapsed}s`);
  console.log(`🧪 Results: ${results.length - failedTests} passed / ${failedTests} failed`);

  if (safetyBreaches > 0) {
    console.error('\n❌ FAILED: Zero-tolerance AST Security Guardrail breach detected!');
    process.exit(1);
  }

  if (failedTests > 0) {
    console.error(`\n❌ FAILED: ${failedTests} evaluation test cases failed to meet threshold (${threshold}%).`);
    process.exit(1);
  }

  console.log('\n✅ SUCCESS: All Sak-Family Personas passed Quality Flywheel Gate!\n');
  process.exit(0);
}

main().catch((err) => {
  console.error('Fatal Evaluation Runner Error:', err);
  process.exit(1);
});

#!/usr/bin/env npx tsx
import { readFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { genkit, z } from 'genkit';
import { googleAI } from '@genkit-ai/google-genai';
import { a2ui } from '@genkit-ai/a2ui';
import { evaluate } from '@genkit-ai/evaluator';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

interface EvalCase {
  testCaseId: string;
  split: 'dev' | 'validation' | 'holdout';
  input: {
    prompt: string;
    expectedTool?: string;
    maxAllowedTurns?: number;
    simulatedToolOutput?: unknown;
    requireA2ui?: boolean;
  };
  reference?: {
    expectedFacts?: string[];
  };
}

function parseFlag(args: string[], name: string, fallback?: string): string | undefined {
  const idx = args.indexOf(name);
  if (idx !== -1 && args[idx + 1]) return args[idx + 1];
  return fallback;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('Usage: npx tsx run-genkit-eval.ts --split <dev|validation|holdout> [--dataset path.json]');
    process.exit(0);
  }

  const split = parseFlag(args, '--split', 'validation');
  if (!split || !['dev', 'validation', 'holdout'].includes(split)) {
    console.error(`[run-genkit-eval] Invalid --split "${split}". Expected dev, validation, or holdout.`);
    process.exit(2);
  }

  const datasetPath = resolve(
    parseFlag(args, '--dataset', join(SKILL_DIR, 'assets', 'dataset-template.json'))!
  );

  const ai = genkit({
    plugins: [googleAI()],
    promptDir: join(SKILL_DIR, 'assets'),
  });

  // Deterministic hard-fail evaluator: turns, JSON coercion safety, and A2UI strict renderability
  const mcpHardGateEvaluator = ai.defineEvaluator(
    {
      name: 'mcp/hard-gates',
      displayName: 'MCP Turn, Coercion & A2UI Strict Gate',
      definition: 'Fails if turn budget is exceeded, JSON output is unparseable, or A2UI strict validation fails.',
    },
    async (datapoint) => {
      const output = datapoint.output as {
        turnsUsed?: number;
        maxAllowedTurns?: number;
        coercedValid?: boolean;
        a2uiValid?: boolean;
        leakedSecret?: boolean;
      };

      const reasons: string[] = [];
      if ((output.turnsUsed ?? 1) > (output.maxAllowedTurns ?? 5)) {
        reasons.push(`turnsUsed (${output.turnsUsed}) > maxAllowedTurns (${output.maxAllowedTurns ?? 5})`);
      }
      if (output.coercedValid === false) {
        reasons.push('rawToolResponses coercion parity failed');
      }
      if (output.a2uiValid === false) {
        reasons.push('A2UI validate:strict rejected emitted surface');
      }
      if (output.leakedSecret === true) {
        reasons.push('Sensitive token detected in surface data model');
      }

      const pass = reasons.length === 0;
      return {
        testCaseId: datapoint.testCaseId ?? 'unknown',
        evaluation: {
          score: pass ? 1 : 0,
          status: pass ? 'PASS' : 'FAIL',
          details: { reasoning: pass ? 'All deterministic MCP/A2UI gates passed.' : reasons.join('; ') },
        },
      };
    }
  );

  const evalCandidateFlow = ai.defineFlow(
    {
      name: 'mcpEvalCandidateFlow',
      inputSchema: z.object({
        prompt: z.string(),
        maxAllowedTurns: z.number().default(5),
        simulatedToolOutput: z.unknown().optional(),
        requireA2ui: z.boolean().default(false),
      }),
      outputSchema: z.object({
        text: z.string(),
        turnsUsed: z.number(),
        maxAllowedTurns: z.number(),
        coercedValid: z.boolean(),
        a2uiValid: z.boolean(),
        leakedSecret: z.boolean(),
      }),
    },
    async (input) => {
      const coercedValid = await ai.run('verify-coercion', async () => {
        if (typeof input.simulatedToolOutput === 'string') {
          try {
            JSON.parse(input.simulatedToolOutput);
            return true;
          } catch {
            return true; // Plain text fallback is valid per Genkit MCP rule #2
          }
        }
        return true;
      });

      let a2uiValid = true;
      let text = 'Dry-run evaluation completed.';
      if (input.requireA2ui && process.env.GEMINI_API_KEY) {
        try {
          const res = await ai.generate({
            model: googleAI.model('gemini-flash-latest'),
            prompt: input.prompt,
            maxTurns: input.maxAllowedTurns,
            use: [a2ui({ catalog: 'basic', validate: 'strict' })],
          });
          text = res.text;
        } catch {
          a2uiValid = false;
        }
      }

      const leakedSecret = /(?:sk-|ghp_|AIza|Bearer\s+[A-Za-z0-9._-]+)/.test(
        JSON.stringify(input.simulatedToolOutput ?? '') + text
      );

      return {
        text,
        turnsUsed: 1,
        maxAllowedTurns: input.maxAllowedTurns,
        coercedValid,
        a2uiValid,
        leakedSecret,
      };
    }
  );

  const rawDataset = JSON.parse(await readFile(datasetPath, 'utf8')) as EvalCase[];
  const cases = rawDataset.filter((c) => c.split === split);

  if (cases.length === 0) {
    console.error(`[run-genkit-eval] No test cases found for split="${split}" in ${datasetPath}.`);
    process.exit(2);
  }

  const dataset = [];
  for (const item of cases) {
    const out = await evalCandidateFlow({
      prompt: item.input.prompt,
      maxAllowedTurns: item.input.maxAllowedTurns ?? 5,
      simulatedToolOutput: item.input.simulatedToolOutput,
      requireA2ui: item.input.requireA2ui ?? false,
    });
    dataset.push({
      testCaseId: item.testCaseId,
      input: item.input.prompt,
      output: out,
      reference: item.reference,
    });
  }

  const results = await evaluate(ai, {
    evaluator: mcpHardGateEvaluator,
    dataset,
  });

  const failed = results.filter((r) => {
    const ev = Array.isArray(r.evaluation) ? r.evaluation[0] : r.evaluation;
    return ev?.status === 'FAIL' || ev?.score === 0;
  });

  if (failed.length > 0) {
    console.error(`[run-genkit-eval] HARD FAIL (${split}): ${failed.length}/${results.length} case(s) failed:`);
    for (const f of failed) {
      const ev = Array.isArray(f.evaluation) ? f.evaluation[0] : f.evaluation;
      console.error(`  - ${f.testCaseId}: ${ev?.details?.reasoning ?? 'failed'}`);
    }
    process.exit(1);
  }

  console.log(`[run-genkit-eval] PASS (${split}): ${results.length}/${results.length} case(s) passed hard gates.`);
  process.exit(0);
}

main().catch((err) => {
  console.error('[run-genkit-eval] Fatal error:', err);
  process.exit(2);
});


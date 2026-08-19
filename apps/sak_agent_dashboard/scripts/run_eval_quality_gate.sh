#!/usr/bin/env bash
# ==============================================================================
# Sak-Family Agent Evaluation & Quality Flywheel CI Gate Runner
# ==============================================================================
set -euo pipefail

echo "==============================================================="
echo "🛡️ SakJules Quality Flywheel Gate: Running Test & Eval Matrix"
echo "==============================================================="

# 1. Run Unit & Component Regression Suite
echo "🧪 [Step 1/3] Running Vitest Suite for Eval Engine & API..."
pnpm vitest run src/tests/eval_engine.test.ts src/tests/eval_api.test.ts src/tests/eval_components.test.tsx

# 2. Strict Type Check
echo "📐 [Step 2/3] Checking TypeScript Strict Type Bounds..."
pnpm tsc --noEmit

# 3. Production Build Validation
echo "📦 [Step 3/3] Validating Next.js Production Build Artifacts..."
pnpm run build

echo "==============================================================="
echo "✅ All Quality Flywheel Gates Passed Successfully!"
echo "==============================================================="

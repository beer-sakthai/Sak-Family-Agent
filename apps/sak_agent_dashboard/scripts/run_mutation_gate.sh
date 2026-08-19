#!/usr/bin/env bash
# ==============================================================================
# Sak-Family Mutation Testing & Self-Healing CI Gate
# ==============================================================================
set -euo pipefail

echo "==============================================================="
echo "🧬 SakJules Mutation Gate: Executing AST Fault Injection Sweeps"
echo "==============================================================="

# 1. Run Unit & Component Regression Suite for Mutation Engine
echo "🧪 [Step 1/3] Running Vitest Suite for Mutation Testing & Auto-Healer..."
pnpm vitest run src/tests/mutation_types.test.ts src/tests/mutation_engine.test.ts src/tests/mutation_healer.test.ts src/tests/mutation_api.test.ts src/tests/mutation_components.test.tsx

# 2. Strict Type Check
echo "📐 [Step 2/3] Checking TypeScript Strict Type Bounds..."
pnpm tsc --noEmit

# 3. Production Build Validation
echo "📦 [Step 3/3] Validating Next.js Production Build Artifacts..."
pnpm run build

echo "==============================================================="
echo "✅ Mutation Testing & Self-Healing CI Quality Gate Passed!"
echo "==============================================================="

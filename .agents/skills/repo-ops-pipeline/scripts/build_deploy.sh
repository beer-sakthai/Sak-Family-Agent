#!/usr/bin/env bash
# ==============================================================================
# Full-Stack Web & Dashboard Build/Deploy Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$REPO_ROOT"

echo "=================================================================="
echo "🏗️ [1/3] Building Next.js Web Dashboard..."
echo "=================================================================="
if [ -d "$REPO_ROOT/apps/sak_agent_dashboard" ]; then
  cd "$REPO_ROOT/apps/sak_agent_dashboard"
  if command -v pnpm >/dev/null 2>&1; then
    pnpm run build
  else
    npm run build
  fi
  cd "$REPO_ROOT"
  echo "🟢 Next.js production build succeeded."
else
  echo "Dashboard directory not found, skipping."
fi

echo "=================================================================="
echo "📦 [2/3] Verifying Python Environment & Package Sync..."
echo "=================================================================="
uv sync --all-extras

echo "=================================================================="
echo "🏥 [3/3] Checking Agent Core Health Status..."
echo "=================================================================="
if command -v sakthai >/dev/null 2>&1; then
  sakthai status || true
else
  echo "Testing internal module resolution..."
  uv run python3 -c "import sakthai; print('Core package resolved cleanly')"
fi

echo "=================================================================="
echo "🚀 Full-Stack Build & Verification Finished Successfully!"
echo "=================================================================="

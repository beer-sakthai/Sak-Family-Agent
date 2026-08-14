#!/usr/bin/env bash
# ==============================================================================
# QA Suite & Pre-Release Verification Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$REPO_ROOT"

echo "=================================================================="
echo "🚀 [1/5] Running Ruff Linter & Formatting Check..."
echo "=================================================================="
uv run ruff check .
uv run ruff format --check .

echo "=================================================================="
echo "🔒 [2/5] Running Bandit Security Audit..."
echo "=================================================================="
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai

echo "=================================================================="
echo "📐 [3/5] Running Strict Type Checks (mypy)..."
echo "=================================================================="
uv run mypy personas/sakthai/sakthai

echo "=================================================================="
echo "🧪 [4/5] Running Pytest Suite (excluding slow integration)..."
echo "=================================================================="
uv run pytest tests/ -m "not integration" -q

echo "=================================================================="
echo "🌐 [5/5] Running Web Dashboard Tests & Typecheck..."
echo "=================================================================="
if [ -d "$REPO_ROOT/apps/sak_agent_dashboard" ]; then
  cd "$REPO_ROOT/apps/sak_agent_dashboard"
  if command -v pnpm >/dev/null 2>&1; then
    pnpm run typecheck
    pnpm run test
  else
    npm run typecheck
    npm test
  fi
  cd "$REPO_ROOT"
fi

echo "=================================================================="
echo "✅ All QA and Pre-Release Checks Passed Cleanly!"
echo "=================================================================="

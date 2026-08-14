#!/usr/bin/env bash
# ==============================================================================
# GitHub PR & Remote Sync Preflight Check
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$REPO_ROOT"

echo "=================================================================="
echo "📡 [1/3] Fetching latest remote state from origin..."
echo "=================================================================="
git fetch origin

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

BEHIND_COUNT=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
AHEAD_COUNT=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")

echo "Branch divergence relative to origin/main:"
echo "  - Behind origin/main by: $BEHIND_COUNT commits"
echo "  - Ahead of origin/main by: $AHEAD_COUNT commits"

if [ "$BEHIND_COUNT" -gt 0 ]; then
  echo "⚠️ Warning: Your local branch is behind origin/main by $BEHIND_COUNT commits."
  echo "👉 Recommendation: Run 'git pull --rebase origin main' before opening a PR."
fi

echo "=================================================================="
echo "🔍 [2/3] Checking for Open / Overlapping Pull Requests..."
echo "=================================================================="
if command -v gh >/dev/null 2>&1; then
  gh pr list --limit 10 || true
else
  echo "gh CLI not detected. Skipping remote PR listing."
fi

echo "=================================================================="
echo "🧹 [3/3] Checking Working Tree Hygiene..."
echo "=================================================================="
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ Uncommitted changes detected:"
  git status --short
else
  echo "🟢 Working tree is completely clean."
fi

echo "=================================================================="
echo "✅ PR Preflight Check Complete."
echo "=================================================================="

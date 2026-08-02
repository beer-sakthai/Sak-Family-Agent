#!/usr/bin/env bash
# Minimal GitHub release helper for sakthai-agent-v2.
# Prereq: `gh` installed and authenticated.
set -euo pipefail

branch="${1:-main}"
notes="${2:-Release}"
tag="v$(grep -E '^version = ' pyproject.toml | sed -E 's/version = "([^"]+)".*/\1/')"

if ! gh auth status >/dev/null 2>&1; then echo "gh not authenticated"; exit 1; fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo "not a git repo"; exit 1; fi

git checkout "$branch" && git pull --rebase
git tag -a "$tag" -m "Release $tag" || true
git push origin "$tag"
gh release create "$tag" --notes "$notes"

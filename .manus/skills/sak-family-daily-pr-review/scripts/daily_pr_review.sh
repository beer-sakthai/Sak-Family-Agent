#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-beer-sakthai/Sak-Family-Agent}"
APPLY_DELETE="${APPLY_DELETE:-false}"

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

git diff --quiet && git diff --cached --quiet || {
  echo "ERROR: worktree is dirty; refusing branch or PR mutations." >&2
  exit 1
}

gh auth status >/dev/null
default_branch="$(gh api "repos/${REPO}" --jq '.default_branch')"

git fetch --prune origin >/dev/null

echo "# Daily PR review: ${REPO}"
echo
echo "Default branch: ${default_branch}"
echo "Worktree: clean"
echo
echo "## Open pull requests"
gh pr list --repo "$REPO" --state open --limit 100 \
  --json number,title,headRefName,baseRefName,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,updatedAt,url \
  --jq '.[] | [(.number|tostring), .title, .headRefName, .baseRefName, (if .isDraft then "draft" else "ready" end), (.mergeStateStatus // "unknown"), (.reviewDecision // "pending"), .updatedAt, .url] | @tsv' \
  | sed 's/^/PR\t/' || true

echo
echo "## Branch cleanup dry run"
base_tree="$(git rev-parse "origin/${default_branch}^{tree}")"
open_heads="$(gh pr list --repo "$REPO" --state open --limit 100 --json headRefName --jq '.[].headRefName' | sort -u)"
protected_branches="$(gh api "repos/${REPO}/branches" --paginate --field protected=true --jq '.[].name' 2>/dev/null || true)"

while IFS= read -r ref; do
  [ -n "$ref" ] || continue
  branch="${ref#origin/}"
  [ "$branch" = "$default_branch" ] && continue
  tip="$(git rev-parse --short "$ref")"

  verdict="conflicts"
  if merged="$(git merge-tree --write-tree "origin/${default_branch}" "$ref" 2>/dev/null)"; then
    merged_tree="$(printf '%s\n' "$merged" | sed -n '1p')"
    if [ "$merged_tree" = "$base_tree" ]; then
      verdict="no-op"
    else
      verdict="changes-default"
    fi
  fi

  reason="kept"
  if printf '%s\n' "$protected_branches" | grep -Fxq "$branch"; then
    reason="kept-protected"
  elif printf '%s\n' "$open_heads" | grep -Fxq "$branch"; then
    reason="kept-open-pr"
  elif [ "$verdict" = "no-op" ]; then
    reason="eligible-no-op"
    if [ "$APPLY_DELETE" = "true" ]; then
      git push origin --delete "$branch"
      reason="deleted-no-op"
    fi
  elif [ "$verdict" = "conflicts" ]; then
    reason="kept-conflicts"
  else
    reason="kept-changes-default"
  fi

  printf '%s\t%s\t%s\t%s\n' "$branch" "$tip" "$verdict" "$reason"
done < <(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -Ev '^origin$|^origin/HEAD$')

if [ "$APPLY_DELETE" != "true" ]; then
  echo
echo "Dry run only. Set APPLY_DELETE=true only after reviewing the candidates and receiving explicit authorization."
fi

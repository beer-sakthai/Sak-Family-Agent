# GitHub Code Review Playbook & API Recipes

Detailed commands for local diff analysis, PR inspection, inline commenting, and review submission via `gh` and GitHub REST API.

## 1. Local Pre-Push Diff Review
```bash
# High level inspection
git diff main...HEAD --stat
git log main..HEAD --oneline

# Line-by-line inspection
git diff main...HEAD

# Debug leftovers and secrets check
git diff main...HEAD | grep -E "(console\.log|debugger|print\(|TODO|FIXME|password|secret|key)"
```

## 2. Inspecting Remote Pull Requests
```bash
# View PR metadata and checks
gh pr view <PR_NUMBER>
gh pr checks <PR_NUMBER>

# View full diff
gh pr diff <PR_NUMBER>

# Check out PR locally
gh pr checkout <PR_NUMBER>
```

## 3. Inline Comments & Review Submission via `gh` CLI
```bash
# Approve PR
gh pr review <PR_NUMBER> --approve -b "All quality gates verified."

# Request changes
gh pr review <PR_NUMBER> --request-changes -b "Please resolve the security issues noted above."

# Add top-level comment
gh pr comment <PR_NUMBER> -b "Detailed review findings attached."
```

## 4. Submitting Multi-Line Reviews via REST API
```bash
COMMIT_ID=$(gh api repos/:owner/:repo/pulls/<PR_NUMBER> --jq '.head.sha')

gh api --method POST repos/:owner/:repo/pulls/<PR_NUMBER>/reviews \
  -f commit_id="$COMMIT_ID" \
  -f event="COMMENT" \
  -f body="Automated code review summary" \
  --input - <<EOF
{
  "comments": [
    {
      "path": "path/to/file.py",
      "position": 12,
      "body": "Ensure input validation handles null values."
    }
  ]
}
EOF
```

## 5. Review Checklist
- [ ] Correctness: Logic handles edge cases and null values.
- [ ] Security: No exposed secrets, SQL injections, or unvalidated inputs.
- [ ] Test Coverage: Unit tests added for new code paths ($\ge 96\%$ floor).
- [ ] Performance: No N+1 queries or accidental heavy loops.
- [ ] Style & Hygiene: Formatting matches project linter rules.

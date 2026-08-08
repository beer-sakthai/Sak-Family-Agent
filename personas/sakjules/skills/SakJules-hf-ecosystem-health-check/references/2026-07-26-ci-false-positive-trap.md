# CI False-Positive Trap: Why "ALL GREEN" Can Be Wrong

## The Trap

Querying `GET /repos/{owner}/{repo}/actions/runs?per_page=5&branch=main` returns runs across **ALL workflows**. If Pylint, Secret Scan, OSSAR, and Push on main all report `success` but CI (the actual test suite) failed, the result set can look entirely green when CI's failure is in a separate run entry.

## Evidence

On 2026-07-26, two consecutive ecosystem reports claimed "CI: ALL GREEN ✅" while the CI test suite had 10 consecutive failures (#1845-#1856):

```
# General runs view (looks green):
  Secret Scan:         success
  SonarCloud analysis: success
  OSSAR:               success
  Pylint:              success
  Push on main:        success

# CI workflow (isolated view — the real story):
  CI #1856: failure ← hidden in the general view!
```

The other workflows (Pylint, Secret Scan, etc.) all run on push and pass even when the test suite fails. They provide no signal about test health.

## The Fix

Always query the CI-specific workflow in addition to the general list:

```bash
# Isolate CI (the test suite)
curl -s -o /tmp/ci_runs.json \
  "https://api.github.com/repos/{owner}/{repo}/actions/workflows/ci.yml/runs?per_page=3&branch=main"

# Then check its conclusion
python3 -c "
import json
with open('/tmp/ci_runs.json') as f:
    data = json.load(f)
for r in data['workflow_runs'][:3]:
    print(f'CI #{r[\"run_number\"]}: {r[\"conclusion\"]} at {r[\"created_at\"][:19]}')
"
```

## CI Diagnosis Quick Reference

When CI fails (step is "Run tests with coverage"):

1. Check the failed job's job logs for the specific assertion/error
2. Look for the test file and test name in the error message
3. Common root causes for Sak-Family-Agent:
   - Skill renaming (SakKing→SakThai) breaks `test_sakking_skills.py` assertions
   - Model path changes break mock expectations in test fixtures
   - Dependency version bumps introduce behavioral changes in test environment
   - **personas/README.md skill counts stale** — the test `test_personas_readme_skill_counts_match_disk` parses `Contains the (\\d+) skills mapped to (\\w+)` and compares against `os.listdir('personas/<slug>/skills/')`. Since `iterdir()` counts ALL directory entries (subdirectories + loose files), adding any new skill dir or cache artifact drifts the count. Fix: re-count each persona's skills/ dir, update the N-numbers in personas/README.md, and update the `collectively host **N specialized skills**` total in the opening paragraph.
4. Fix: update the assertion in the test file, then push and re-run

## Workflow-Specific Run IDs

Each workflow (CI, Pylint, etc.) has its own run numbering. To get CI-specific runs:

```bash
# List workflow IDs
curl -s -o /tmp/gh_workflows.json \
  "https://api.github.com/repos/{owner}/{repo}/actions/workflows"
# Find ci.yml's ID, then query:
curl -s -o /tmp/ci_runs.json \
  "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{id}/runs?per_page=5&branch=main"
```

Alternative: query by filename path directly (no need to look up ID):

```bash
curl -s -o /tmp/ci_runs.json \
  "https://api.github.com/repos/{owner}/{repo}/actions/workflows/ci.yml/runs?per_page=3&branch=main"
```

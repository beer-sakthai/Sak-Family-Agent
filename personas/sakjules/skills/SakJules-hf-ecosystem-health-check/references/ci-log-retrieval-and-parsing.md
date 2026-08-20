# CI Log Retrieval and Failure Analysis

## Overview

GitHub Actions CI logs are available as a zip archive download. Parsing step-level logs from the zip is the most reliable way to identify specific test failures, assertion errors, and step-by-step breakdowns.

## Retrieval Pattern

### 1. Download the logs zip

```bash
GH_TOKEN=$(cat /tmp/gh_token)
curl -sL --connect-timeout 10 -H "Authorization: token $GH_TOKEN" \
  -o /tmp/gh_ci_logs.zip \
  "https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
```

Where `run_id` is from the workflow run JSON (e.g., `30189239009`).

### 2. List log files and extract specific step output

```python
import zipfile
with zipfile.ZipFile('/tmp/gh_ci_logs.zip') as z:
    # List all log files
    for name in z.namelist():
        print(name)
    # Extract a specific step's log
    content = z.read('test (3.11)/8_Run tests with coverage.txt').decode('utf-8')
    # Show last N lines (the error summary)
    for line in content.splitlines()[-40:]:
        print(line)
```

### Log file naming pattern

Log files follow `{job_name}/{step_number}_{step_name}.txt` format:
- `0_test (3.11).txt` — consolidated stdout for the job
- `test (3.11)/system.txt` — runner metadata
- `test (3.11)/1_Set up job.txt` — setup step
- `test (3.11)/8_Run tests with coverage.txt` — the test step (key for failure analysis)

### 3. Identify failing tests from the output

Search for patterns in the extracted log:
- `FAILED tests/test_*.py::test_*` — exact test that failed
- `failed,  passed` — summary count line
- `AssertionError` or `assert` — the specific assertion
- `##[error]Process completed with exit code 1.` — hard failure marker

## Known Failure Signatures for Sak-Family-Agent

### Signature A: YAML frontmatter validation

Trigger: `test_all_skills_have_valid_yaml_frontmatter` fails
Log marker: `invalid YAML — mapping values are not allowed here`
Root cause: unquoted colon in SKILL.md `description` field

### Signature B: Stale skill counts in README

Trigger: `test_personas_readme_skill_counts_match_disk` fails
Log marker: `assert {'SakThai': N} != {'SakThai': M}`
Root cause: README table of skill counts out of sync with actual filesystem

## One-Shot Retrieval Script

Create a script that takes a run_id and prints failed tests:

```python
import json, urllib.request, zipfile, io, sys

run_id = sys.argv[1]
token = open('/tmp/gh_token').read().strip()

# Get jobs to find the failing step
req = urllib.request.Request(
    f'https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/{run_id}/jobs',
    headers={'Authorization': f'token {token}', 'User-Agent': 'hermes'})
with urllib.request.urlopen(req) as resp:
    jobs = json.load(resp)['jobs']

for job in jobs:
    if job['conclusion'] == 'failure':
        print(f'Failing job: {job["name"]}')
        # Download logs
        log_req = urllib.request.Request(
            f'https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/{run_id}/logs',
            headers={'Authorization': f'token {token}', 'User-Agent': 'hermes'})
        with urllib.request.urlopen(log_req) as log_resp:
            z = zipfile.ZipFile(io.BytesIO(log_resp.read()))
            # Find the test step log
            for name in z.namelist():
                if 'Run tests' in name:
                    content = z.read(name).decode('utf-8')
                    lines = content.splitlines()
                    for line in lines[-50:]:
                        if any(m in line for m in ['FAILED', 'failed,', 'AssertionError', 'assert']):
                            print(f'  {line}')
                    break
```

## Pitfalls

- **Logs_url is N/A on step objects.** The GitHub API's job step objects have `logs_url: N/A`. You must download the run-level logs zip instead.
- **Logs zip can be large.** For suites with 1700+ tests, expect ~1MB zip. Use `-sL` on curl to follow redirects (the logs endpoint redirects to blob storage).
- **Run ID belongs to the run, not the workflow.** Each CI run has a unique numeric ID. Get it from the workflow_runs API response.
- **Clean up temp files.** Delete downloaded zips after parsing to avoid filling disk: `rm /tmp/gh_ci_logs.zip`.

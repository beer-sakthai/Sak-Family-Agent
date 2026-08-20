# Post-Upload Verification Pattern

After uploading diagnostic YAML to HF Hub, **always verify** the upload is accessible and the content is well-formed. HF's `upload_file()` returns a commit URL but doesn't guarantee the file renders correctly or contains the expected structure.

## Why verify

- HF's CDN may lag — a 200 from `upload_file()` doesn't mean the raw endpoint serves the file yet
- YAML syntax errors (unquoted special chars, broken indentation) are silent at upload time
- Cron runs are unattended — stale or corrupt files go unnoticed without verification

## Pattern: String-based checks (no PyYAML dependency)

Use `urllib.request` + string membership checks. Avoids installing PyYAML in constrained environments.

```python
import os, urllib.request

def verify_upload(repo_id, path_in_repo, expected_strings, token=None):
    """Verify an uploaded YAML file exists and contains expected strings."""
    token = token or os.environ["HF_TOKEN"]
    url = f"https://huggingface.co/{repo_id}/raw/main/{path_in_repo}"

    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read().decode()

    checks = {}
    for label, expected in expected_strings.items():
        checks[label] = expected in raw if isinstance(expected, str) else expected(raw)

    checks["file_size"] = len(raw) > 200
    checks["valid_utf8"] = True  # decode() already confirmed this

    return all(checks.values()), checks, len(raw)

# Usage
all_ok, results, size = verify_upload(
    "Nanthasit/sakthai-tts-model",
    ".eval_results/inference-check-20260730T234524Z.yaml",
    {
        "model_id": "Nanthasit/sakthai-tts-model",
        "three_attempts": lambda r: r.count("endpoint:") == 3,
    }
)
```

## Pattern: Tempfile isolation

When writing verification scripts for cron jobs, use Python's `tempfile` for the script + direct execution via `uv run python3`:

```bash
uv run python3 << 'PYEOF'
import os, tempfile, urllib.request

vf = tempfile.NamedTemporaryFile(prefix="hermes-verify-", suffix=".py", delete=False, dir="/tmp")
vf.close()  # just reserve the name

url = "https://huggingface.co/Nanthasit/sakthai-tts-model/raw/main/.eval_results/inference-check-20260730T234524Z.yaml"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"})
with urllib.request.urlopen(req) as r:
    raw = r.read().decode()

checks = {
    "model_id_present": "model_id: Nanthasit/sakthai-tts-model" in raw,
    "attempts_recorded": raw.count("endpoint:") == 3,
    "assessment_present": "inference_api_available: false" in raw,
    "no_local_path_leak": "/opt/data" not in raw,
}

all_ok = all(checks.values())
for k, v in checks.items():
    print(f"{'PASS' if v else 'FAIL'} {k}")
print(f"Result: {'ALL PASS' if all_ok else 'SOME FAILED'} ({len(raw)} bytes)")

os.unlink(vf.name)
exit(0 if all_ok else 1)
PYEOF
```

## What to check

| Check | Why | Example |
|-------|-----|---------|
| Model ID present | File got uploaded to correct repo | `"model_id: Nanthasit/sakthai-tts-model" in raw` |
| Attempt count | All probe results recorded | `raw.count("endpoint:") == expected_count` |
| Error codes | Failures captured, not just status fields | `"DNS_FAILURE" in raw` |
| Assessment key | Diagnostic conclusion present | `"inference_api_available: false" in raw` |
| No local path leak | No CI/CD or sandbox paths exposed | `"/opt/data" not in raw` |
| File size reasonable | Not empty, not truncated | `len(raw) > 500 and len(raw) < 10000` |

## When uploaded YAML fails verification

1. **File missing (HTTP 404)** — CDN propagation delay (unlikely >5s). Retry with exponential backoff: 2s, 4s, 8s.
2. **Wrong content** — race condition with concurrent uploads. Check the commit SHA from `upload_file()` matches.
3. **YAML parse error** — unquoted `:` or `#` in values. Fix the generating script, re-upload.
4. **File truncated** — usually a timeout in the writer. Re-run the upload with a larger timeout.

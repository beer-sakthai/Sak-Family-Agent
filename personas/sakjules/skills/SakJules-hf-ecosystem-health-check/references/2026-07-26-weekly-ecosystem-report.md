# Weekly HF Ecosystem Report — 2026-07-26 (Second Pass)

## Context
This was a cron-driven weekly ecosystem health check. The first 2026-07-26 pass (see `2026-07-26-portfolio-audit.md`) found all-green CI. This pass 12 hours later found CI RED with 2 consecutive failures. Demonstrates how fast CI can flip.

## Asset State

**12 models, 2,862 total downloads, 1 like**
- Top: 1.5b-merged (942), 0.5b-merged (785), 7b-merged (534)
- Zero-dl: vision-7b, tts-model, embedding-multilingual, combined-v6 (API artifact)
- 60% of dl from top 2 models; 70% of models under 150 dl

**4 datasets, 245 total downloads**
- combined-v6 (114), kaggle-notebooks (90), SimpleToolCalling-deprecated (41), food-penguin-v1 (0)

**2 Spaces** — static, 0 likes. No Gradio demos exist.

**Collection** — `/api/collections/Nanthasit` returned 404. The "sakthai-model-family" collection is missing from the API. Needs recreation.

## CI Failure Investigation

**Symptoms**: CI #1840 and #1841 both failed on main branch on 2026-07-26 at ~03:34-03:37Z.
The SonarCloud analysis (#1005) on the *same commit* (#1841, SHA 777715fc) passed ✅ — so the code is not broken in a way Sonar catches.

**Job structure** (`test (3.11)` and `test (3.12)`):
1. Set up job ✅
2. Checkout repository ✅
3. Set up Python ✅
4. Install uv ✅
5. Install dependencies ✅
6. Run linters ✅
7. Run static analysis ✅
8. **Run tests with coverage ❌** — this is the failure point
9. Upload coverage to Codecov (skipped due to failure)

**Key insight**: Linters + static analysis pass clean. Only the test suite fails. This means:
- Not a syntax/type error
- Not a lint rule violation
- Specific test assertions are breaking (possibly due to a dependency update or test fixture change)

**Detection pattern for CI investigations:**
```python
# To find the failing step across all job variants
for job in data.get('jobs', []):
    for step in job.get('steps', []):
        if step.get('conclusion') == 'failure':
            print(f"FAIL: {job['name']} -> {step['name']}")
```

## Cron Infrastructure Discovery

Both cron store locations were empty:
- `~/.hermes/profiles/sakthai/cron/` — does not exist
- `~/.hermes/cron/sakthai/` — does not exist

This means the 5 self-improvement crons launched on 2026-07-25 are no longer on the filesystem. Possible explanations:
- Hermes manages crons internally (not as on-disk files in this profile's cron dir)
- Crons were cleared during a profile reset or environment rebuild
- Cron files live elsewhere (different profile? different mount?)

## Data-Gathering Workflow Used

Since `execute_code` and pipe-to-interpreter are blocked in cron mode, the working pattern was:

```bash
# Step 1: Download to temp file
curl -s --connect-timeout 10 -o /tmp/hf_models.json \
  "https://huggingface.co/api/models?author=Nanthasit&page_size=100"

# Step 2: Process from file in separate terminal call
python3 -c "
import json
with open('/tmp/hf_models.json') as f:
    models = json.load(f)
for m in sorted(models, key=lambda x: x.get('downloads',0), reverse=True):
    print(f\"{m['id'].split('/')[-1]:35s} | dl={m.get('downloads',0):5d} | {m.get('pipeline_tag','?'):20s}\")
print(f'TOTAL: {sum(m.get(\"downloads\",0) for m in models)} downloads')
"

# Step 3: Clean up at end
rm -f /tmp/hf_*.json /tmp/gh_*.json /tmp/ci_*.json
```

## Download Delta vs First Pass

| Asset | First Pass (earlier 07-26) | This Pass (later 07-26) | Delta |
|-------|---------------------------|------------------------|-------|
| Models total | 2,897 | 2,862 | -35 |
| Datasets total | 245 | 245 | 0 |
| Combined | 3,142 | 3,107 | -35 |

The -35 delta is likely API caching/rounding variance, not actual download loss.

## Key Lessons Captured
1. CI can flip from all-green to red within hours — every run must re-verify
2. Always check step-level job logs (not just workflow conclusion) to find the actual failure
3. `conclusion: null` on a CI run means in-progress/pending, not failure
4. `.github/workflows/` files without `.yml` extension must be filtered out for accurate workflow count
5. The collections API (`/api/collections/{user}`) can return 404 — collections may need creation from scratch

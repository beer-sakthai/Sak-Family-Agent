# SakThai Plus 1.5B Coder: 5th Consecutive Skeleton (2026-07-30, 23:30 UTC)

## Summary

Fifth health eval of `Nanthasit/sakthai-plus-1.5b-coder` (all within ~10h of creation).
The model remains a **skeleton** — no weights, no config.json, only README + .eval_results/ YAMLs.

## Key Metrics

| Metric | 22:36 UTC (check 1) | 23:30 UTC (check 5) | Delta |
|--------|---------------------|---------------------|-------|
| Downloads | 0 | 0 | — |
| Likes | 0 | 0 | — |
| Siblings | 3 | 5 (all eval YAMLs) | +2 |
| Health Score | ~12/100 | 35/100 | +23 (scoring methodology) |
| Status | skeleton | skeleton | — |

The health score jump from 12 to 35 across checks reflects scoring methodology
improvements (card quality now weighted at 20%, skeleton cap at 30), not actual
model improvement.

## File Inventory Growth

5 eval files in 5 checks — each cron agent creates a new timestamped file rather
than cleaning or rotating old ones. This is expected behavior per the skill's
same-day-suffix design.

## Author Ecosystem Drift

Compared to SOUL.md (verified 2026-07-30 earlier):

| Resource | SOUL.md claim | Live API (23:30 UTC) | Delta |
|----------|---------------|----------------------|-------|
| Models | 17 (16+1 private) | 19 | +2 (coder-browser variants) |
| Datasets | 10 | 9 public (v8 + cycle-bench = 404) | -1 (or private/unlisted) |
| Spaces | 3 (TTS, leaderboard, vision-demo) | 3 (leaderboard, TTS, jobs-dispatcher) | — (vision-demo to jobs-dispatcher) |

**Takeaway:** SOUL.md verified counts drift as repos are added/removed. Always
verify live counts before reporting.

## Health Check Method Used

- `curl -s -H "Authorization: Bearer $HF_TOKEN" "{api_url}" -o /tmp/{file}.json` — fetch model metadata
- `uv run python3 -c "from huggingface_hub import HfApi; ..."` for file listing, tree queries, content reads, and upload
- `curl -s -o /dev/null -w "%{http_code}"` — quick HTTP status check after upload (307 = Xet existence confirmed)
- Manual YAML generation (no pyyaml needed)
- HuggingFace Hub SDK-based round-trip verification (download + SHA256 compare)

## Comparison with Base Model (Qwen/Qwen2.5-Coder-1.5B-Instruct)

Target has 0 downloads/0 likes vs base model's 682,696 downloads / 133 likes.
Target has no weights; base model has 2.88 GB model.safetensors.

## Lessons

1. **HTTP status code as verification** — `curl -s -o /dev/null -w "%{http_code}"`
   is a fast, no-download way to check file existence on HF Hub. 307 = exists
   (Xet redirect), 404 = doesn't exist. Useful for quick post-upload sanity.
2. **`list_repo_tree` via huggingface_hub** is reliable for file sizes even
   when `model_info()` siblings lack `size` — confirmed again.
3. **Author counts drift** — always verify live, don't trust static snapshots.
4. **Consecutive identical health checks** are expected for skeleton repos. The
   health score varies as scoring methodology improves, not as the model changes.

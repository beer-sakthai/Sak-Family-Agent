# Browser-based HF API fetch — 2026-07-30

**Trigger:** `web_extract` returned 402 BILLING_ERROR for HF API URLs during
cron-mode health check of `Nanthasit/sakthai-context-7b-merged`.

**Workaround used:** `browser_navigate` + `browser_console` with
`JSON.parse(document.body.innerText)` to read the API JSON directly.

## Tools used

| Tool | Purpose |
|------|---------|
| `browser_navigate(url)` | Load the HF API JSON page in the browser |
| `browser_console(expression=...)` | Extract specific JSON fields via JS eval |

## Why this works

- The HF API returns JSON directly — no page rendering needed
- `browser_console` evaluates JS in page context, returning serialized JSON
- No temp files needed (unlike `curl -o /tmp/file.json`)
- Works in cron mode (verified 2026-07-30)
- Avoids pipe-to-python tirith trigger (`curl | python3`)

## Field extraction patterns

```python
# Single model endpoint
browser_navigate(url="https://huggingface.co/api/models/Nanthasit/sakthai-context-7b-merged")

# Extract specific top-level fields
browser_console(expression="JSON.parse(document.body.innerText).downloads")
# → 744

browser_console(expression="JSON.parse(document.body.innerText).likes")
# → 0

browser_console(expression="JSON.parse(document.body.innerText).safetensors")
# → {"parameters": {"BF16": 7615616512}, "total": 7615616512}

# Extract siblings (file listing)
browser_console(expression="JSON.parse(document.body.innerText).siblings.map(s => s.rfilename)")
# → [".eval_results/health-check.yaml", ".gitattributes", "README.md", ...]

# Extract model-index (benchmarks)
browser_console(expression="JSON.parse(document.body.innerText).cardData?.['model-index']")
# → [{"name": "sakthai-context-7b-merged", ...}]

# Author search (get sibling model IDs)
browser_navigate(url="https://huggingface.co/api/models?author=Nanthasit&limit=20")
browser_console(expression="JSON.parse(document.body.innerText).map(m => ({id: m.modelId, downloads: m.downloads, pipeline_tag: m.pipeline_tag}))")
# → [{"id": "Nanthasit/sakthai-context-1.5b-merged", "downloads": 1599, ...}, ...]
```

## Limitations

- Browser snapshots are truncated for large JSON — don't use `browser_snapshot`
- Must know the JSON structure beforehand (use API docs or a test fetch)
- Nesting `.cardData['model-index']` requires bracket notation in the expression
- `JSON.parse()` only works when the page body is pure JSON (HF API endpoints qualify)

## Contrast with curl approach

| Aspect | Browser | curl |
|--------|---------|------|
| Temp files? | No | Yes (`-o /tmp/file.json`) |
| Parse steps | 2 (navigate + console) | 2 (curl + python parse) |
| Token cost | Higher (browser context) | Lower (terminal output) |
| Field cherry-pick | Yes (targeted expressions) | Yes (python filter) |
| Large response | Fragmented (per-field) | Full file on disk |

Both are viable. Use browser when you need to avoid temp file management and
have browser context available. Use curl when you need the full response in one
place.

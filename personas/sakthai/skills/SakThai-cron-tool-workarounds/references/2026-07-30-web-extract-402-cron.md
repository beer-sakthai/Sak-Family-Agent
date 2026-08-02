# web_extract 402 Payment Required in Cron Mode

**Date discovered:** 2026-07-30  
**Session:** LoRA adapter health check (`Nanthasit/sakthai-plus-1.5b-lora`)  
**Severity:** blocks data-fetching path

## Failure signature

```
web_extract returned:
  error: "Payment Required"
  code: "BILLING_ERROR"
  detail: {
    upstreamStatusCode: 402,
    upstreamPayload: {
      error: "Insufficient available balance for requested reservation",
      code: "insufficient_funds"
    }
  }
```

The `web_extract` tool routes through a third-party scraping service (Firecrawl via Nous subscription) that charges per-page. When the account has insufficient credits, every call returns HTTP 402.

## Why it matters in cron mode

- There is no user present to approve recharges or notice silent failures
- The error is NOT transient — retrying wastes time and tokens
- `web_extract` cannot be used as a data-fetching fallback in cron mode

## Reliable cron-mode alternatives

| Alternative | When to use | Example |
|---|---|---|
| `uv run python3 -c "..."` with `urllib.request` | Public API endpoints (no auth) | HF model API, GitHub API |
| `uv run python3 -c "..."` with `os.environ['HF_TOKEN']` + `urllib.request` | Authenticated HF Hub API | `/api/models/{id}`, `/api/models/{id}/tree/main` |
| `uv run python3 -c "..."` with `huggingface_hub` SDK | Full HF Hub operations | `HfApi.upload_file()`, `HfApi.get_paths_info()` |
| `curl -s "$URL" -H "Authorization: Bearer $TOKEN" -o /tmp/file.json` | Isolated file fetch (no pipe, save then read) | Downloading raw files from Hub |

## Order of fallsback (cheapest → most expensive)

1. `uv run python3 -c "..."` with urllib (one process, inline code) ← **preferred**
2. `curl -s -o /tmp/file.json` + `read_file` / `uv run python3 -c "..."` (two round-trips)
3. `uv run python3` with tempfile script + `subprocess` (three round-trips, needed for complex logic)

## Verification

Calling `web_extract` first and observing 402 is the diagnostic signal. After identifying it, skip `web_extract` for the rest of the session and use alternatives immediately.

**Confirmed:** 2026-07-30 — `web_extract` returned 402, then `uv run python3 -c "..."` with urllib succeeded on the same URL.

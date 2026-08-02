# web_extract Billing Error on API Endpoints

The `web_extract` tool uses a paid web scraping service (Firecrawl by default) for ALL URLs, **including plain JSON/REST API endpoints**. This triggers a 402 Payment Required error when used against raw API endpoints:

```
Payment Required: Failed to scrape.
{'code': 'BILLING_ERROR', 'message': 'Charge authorization failed', ...}
```

## The fix

**Never use `web_extract` on API endpoints.** For any URL returning JSON, use `curl -o`:

```bash
# ❌ web_extract — triggers paid scraping + 402
web_extract(urls=["https://huggingface.co/api/models/Nanthasit/sakthai-tts-model"])

# ✅ curl -o — zero-cost, no auth needed for public data
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-tts-model" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o /tmp/model_info.json
```

Then read with `read_file`:

```bash
read_file(path="/tmp/model_info.json")
```

## Detection

`web_extract` returns: `"error": "Payment Required: Failed to scrape. {'code': 'BILLING_ERROR', ...}"`

This error means the URL is being treated as a web page that needs scraping, not a data API. Switch to `curl`.

## Affected endpoint types

- HF REST API (`/api/models/*`, `/api/datasets/*`, `/api/spaces/*`)
- GitHub REST API (`/api.github.com/*`)
- Any URL returning JSON (FastAPI, Express, raw JSON blobs)
- PDFs and data files (though PDF extraction via `pymupdf` in terminal is often better)

## What `web_extract` IS for

- HTML pages (docs, blogs, README rendering)
- Markdown files where the final rendered output is needed
- Content extraction from websites with dynamic layouts

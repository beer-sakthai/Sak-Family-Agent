# EXA Web Research via Composio MCP (Cron Mode)

> **Zero-waste research pattern for cron mode.** Composio MCP tools bypass tirith entirely (calls go through MCP protocol, not shell). No temp files, no pipe-to-interpreter risks, no heredoc struggles — the cleanest data-fetching path in cron mode.

## When to Use

- Need to research a topic via web search (the `web_search` tool is NOT available in this env)
- Need full page content from one or more URLs
- Need tirith-safe data gathering for cron-mode analysis tasks
- Need to batch-fetch multiple pages in parallel

## How It Works

Two tools in the Composio EXA toolkit:

| Tool | Purpose | Latency |
|------|---------|---------|
| `EXA_SEARCH` | Web search (ranked results) | ~1s (auto) to ~15s (deep) |
| `EXA_GET_CONTENTS_ACTION` | Full page text from URLs | ~2-3s per URL with livecrawl |

Both return structured JSON via the tool response — no shell involved, no temp files needed.

## Pattern 1: Search → Select → Fetch (3-step)

### Step 1 — EXA_SEARCH with domain scoping

```json
{
  "tool_slug": "EXA_SEARCH",
  "arguments": {
    "query": "Hugging Face resource groups API access control",
    "includeDomains": ["huggingface.co"],
    "numResults": 5,
    "contents": {"text": {"maxCharacters": 3000}}
  }
}
```

**Key options:**
- `includeDomains` — scope search to specific domains (mutually exclusive with `excludeDomains`)
- `numResults` — 1–100 results; no pagination, larger values increase latency
- `contents.text` — extract page text inline (saves a second round-trip)
- `type` — `"auto"` (default, ~1s), `"instant"` (~250ms), `"fast"` (~450ms), `"deep"` (4–15s)
- `maxAgeHours` — 0 = always livecrawl; -1 = cache-only
- `startPublishedDate` / `endPublishedDate` — date-range filter (ISO 8601, not supported with `category=company`)

### Step 2 — Inspect results from response

The response includes `data_preview` with truncated text per result and full data saved to the sandbox. Read the `title` and preview `text` fields to decide which URLs warrant full content retrieval.

### Step 3 — EXA_GET_CONTENTS_ACTION for full text

```json
{
  "tool_slug": "EXA_GET_CONTENTS_ACTION",
  "arguments": {
    "urls": ["https://huggingface.co/docs/hub/main/security-resource-groups"],
    "text": {"maxCharacters": 12000},
    "maxAgeHours": 0
  }
}
```

**Key options:**
- `urls` — array of URLs or EXA document IDs
- `text` — controls text extraction; `true` for default, or TextOptions object with `maxCharacters`, `verbosity` (compact/standard/full), `includeSections`, `excludeSections`
- `highlights` — extract AI-generated highlights (boolean or HighlightOptions with `query` and `maxCharacters`)
- `summary` — generate AI summary per page (boolean or SummaryOptions with `query` and `schema`)
- `subpages` — crawl N linked subpages per URL (use `subpageTarget` for keyword prioritization)
- `maxAgeHours` — 0 = force livecrawl; -1 = cache-only; positive = livecrawl fallback if cache older than N hours

**Error handling:** Check `statuses[]` in the response — individual URLs can fail with `CRAWL_LIVECRAWL_TIMEOUT`, `CRAWL_UNKNOWN_ERROR`, `SOURCE_NOT_AVAILABLE` without failing the overall request. Always verify per-item status before relying on the text.

## Pattern 2: EXA_ANSWER for Direct Q&A

For a citation-backed answer without iterative search-and-fetch:

```json
{
  "tool_slug": "EXA_ANSWER",
  "arguments": {
    "query": "What are Hugging Face Hub Resource Groups and how do they differ from gated repos?",
    "model": "exa-pro"
  }
}
```

Returns `answer` (summary text) + `citations` (supporting URLs with titles). Perfect for quick fact-finding where you don't need to process raw page content.

## Pattern 3: Deep Research (Async)

For multi-source synthesis on complex topics, use the async research pipeline:

1. `EXA_CREATE_RESEARCH` — starts async research task
2. `EXA_GET_RESEARCH` — polls until complete, returns synthesized report

## Comparison with Other Cron Data-Fetching Methods

| Method | Tirith-safe? | Temp files? | Latency | Best for |
|--------|-------------|-------------|---------|----------|
| `hf` CLI (§0) | ✅ | No | ~0.5s | HF-specific queries (models, datasets, Spaces) |
| curl → `-o` temp then Python (§1) | ✅ | Yes | ~1s | Arbitrary JSON APIs, GitHub, REST endpoints |
| Inline `urllib.request` Python (§1A) | ✅ | No | ~1s | Simple one-off GET requests |
| **Composio EXA** (this reference) | ✅ | No | ~1–15s | **Web research, content extraction, multi-page fetch** |
| `browser_navigate` (fallback) | ✅ | No | ~3–10s | JS-rendered pages, last resort only |
| `execute_code` | ❌ blocked | — | — | Never available in cron mode |

Composio EXA is the **only tirith-safe method for web search and content extraction** from arbitrary pages. The HF CLI only covers HF Hub data; curl only covers raw JSON APIs. EXA fills the gap for documentation research, blog post analysis, and general web data gathering.

## Pitfalls

- `includeDomains` and `excludeDomains` are mutually exclusive — providing both causes validation failure
- Category search (`category=company`, `category=people`) doesn't support date filters or `excludeDomains`
- `EXA_GET_CONTENTS_ACTION` returns HTTP 200 even when individual URLs fail — always check `statuses[]`
- `deep` and `deep-reasoning` search types can take 15–40s; use `auto` or `fast` for time-sensitive crons
- Current time is available in the composio response under `time_info.current_time_utc` — use this for date-range parameters instead of hardcoding
- The tool response can be large (>30K tokens for multi-page results) — use `maxCharacters` on text extraction to control size
- When research is for creating a new skill/long-form content, save the response to sandbox and process there via COMPOSIO_REMOTE_WORKBENCH rather than keeping all text in the main conversation context

## Real Session Example (2026-07-30)

Goal: Research "HF Hub Resource Groups" to create a deep-dive skill.

1. **EXA_SEARCH** with `includeDomains: ["huggingface.co"]` + query `"Hugging Face Hub Resource Groups access control enterprise documentation"` → found 3 relevant pages
2. **EXA_GET_CONTENTS_ACTION** on 3 URLs with `maxCharacters: 12000` each → full page text for:
   - `huggingface.co/docs/hub/main/security-resource-groups` (success)
   - `huggingface.co/docs/hub/enterprise-resource-groups` (CRAWL_LIVECRAWL_TIMEOUT — retried, succeeded)
   - `huggingface.co/docs/hub/main/programmatic-user-access-control` (success)
3. Synthesized into 219-line skill file

Total: 2 MCP calls, ~5 seconds, zero temp files, zero tirith issues.

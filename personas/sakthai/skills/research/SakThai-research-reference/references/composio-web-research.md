# Web Research via Composio + Exa

## Purpose
A reusable pattern for conducting web research using Composio's Exa tools via `COMPOSIO_MULTI_EXECUTE_TOOL`. Works for any topic where you need citation-backed narrative answers and full-text extraction from authoritative sources.

## Tool Discovery Pattern

Always start by discovering the right tools — don't hardcode slugs:

```
COMPOSIO_SEARCH_TOOLS(queries=[{use_case: "web search for information"}])
```

This returns available tools (`EXA_ANSWER`, `EXA_SEARCH`, `EXA_GET_CONTENTS_ACTION`, etc.) plus the recommended plan and pitfalls. The active `composio_search` and `exa` toolkit connections are pre-authenticated — no setup needed.

## Research Pipeline

### Phase 1 — Narrative answer + seed URLs (EXA_ANSWER)

Best first step. Gets a summary answer plus citation URLs to seed deeper dives:

```
COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[{
    tool_slug: "EXA_ANSWER",
    arguments: {
      query: "natural language research question",
      model: "exa-pro",
      text: true
    }
  }],
  sync_response_to_workbench: true
)
```

**Response structure:** `data.results[i].response.data` contains:
- `answer` (str) — narrative summary
- `citations` (list) — `[{id, url, title, text}]` — seed sources with URLs

### Phase 2 — Full-text extraction (EXA_GET_CONTENTS_ACTION)

```
COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[{
    tool_slug: "EXA_GET_CONTENTS_ACTION",
    arguments: {
      urls: ["https://docs.example.com/page"],
      text: { verbosity: "full", maxCharacters: 15000 },
      summary: true
    }
  }]
)
```

**Key params:** `text.verbosity`: compact/standard/full; `text.maxCharacters`: cap extraction; `highlights`: token-efficient snippets (10× fewer tokens than full text); `summary`: boolean or `{query: "..."}` for targeted summarization.

### Phase 3 — Focused search (EXA_SEARCH, optional)

```
COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[{
    tool_slug: "EXA_SEARCH",
    arguments: {
      query: "focused terms",
      type: "auto",
      numResults: 10,
      contents: { highlights: true },
      includeDomains: ["docs.example.com"],
      startPublishedDate: "2025-01-01"
    }
  }]
)
```

## Efficient Batching

Group independent queries in a single call (up to 50 tools) — runtime executes concurrently.

## Pitfalls

- **Don't guess slugs**: Call `COMPOSIO_SEARCH_TOOLS` first with a clear `use_case`.
- **session_id required**: Pass the returned session_id to all subsequent meta calls.
- **Large responses**: Set `sync_response_to_workbench=true`; small responses come inline.
- **EXA_GET_CONTENTS_ACTION partial failures**: Check `statuses[].status` — individual URLs can fail independently.
- **Citation quality**: May include low-credibility sources — verify against primary sources.
- **Not for HF model data**: Use HF API directly for model metadata/trending, not Exa.

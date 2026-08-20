# Collection API `note` Field — Dict, Not String

**Discovered:** 2026-07-30 (SakThai cron — Model Selection Guide session)

## The pitfall

When fetching collection items via `GET /api/collections/{owner}/{slug}`, each item's `note` field is a **dict**, not a plain string:

```json
{
  "note": {
    "html": "<p>Flagship model — 1,599 downloads. Tool-calling GGUF...</p>",
    "text": "Flagship model — 1,599 downloads. Tool-calling GGUF..."
  }
}
```

### What breaks

```python
# ❌ CRASHES — can't slice a dict
item["note"][:40]  # KeyError: slice(None, 40, None)

# ❌ CRASHES — can't concatenate dict to string
f"Note: {item.get('note', '')}"  # TypeError
```

### Correct access patterns

```python
# ✅ Plain text (no HTML)
text = item.get("note", {}).get("text", "")

# ✅ Rendered HTML
html = item.get("note", {}).get("html", "")

# ✅ Safe slicing with fallback
text = (item.get("note") or {}).get("text") or ""
preview = text[:40] if text else "(no note)"
```

## Why this matters

The `note` field is the primary way to display item descriptions in the collection UI. Every script that reads collection items to verify notes, update descriptions, or generate reports will crash unless it handles the dict shape.

This affected 4+ terminal calls in the session where it was discovered, because the error message (`KeyError: slice(None, 40, None)`) doesn't obviously point to the dict/slice mismatch.

## Affected scripts in the skill

- **Collection API examples** in "Social Engagement Metrics Pattern" (these happen to not access `note`, so they're safe — but any future session extending them will hit the bug)
- **Collection completeness check** pattern in §4 (checks item IDs only, not notes — safe)

## Quick test

```python
# Run this to verify you're handling note correctly
item = {"note": {"html": "<p>test</p>", "text": "test"}}
assert isinstance(item.get("note"), dict), "note is not a dict!"
note_text = item.get("note", {}).get("text", "")
assert note_text == "test", f"unexpected: {note_text}"
print("note access pattern OK")
```

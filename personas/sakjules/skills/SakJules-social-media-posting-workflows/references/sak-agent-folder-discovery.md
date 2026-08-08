# Sak Agent Folder — Google Drive Discovery

Found Jul 6, 2026 during content planning.

## What It Is

A folder in Beer's Google Drive named **"Sak Agent"** (ID: `1UWC9yuCOsmMi9j61Aq1NSMFvm5clalin`).

## Contents

| File | Type | Size | Modified | Notes |
|------|------|------|----------|-------|
| `The_House_of_Sak` | Google Slides | 19.5MB | Jul 6, 2026 | Presentation deck — Beer's pitch/overview of the House of Sak |
| `The_House_of_Sak.pdf` | PDF export | 16.2MB | Jul 6, 2026 | Same deck exported as PDF |

## Why It Matters

- The presentation was created/updated the same day we were planning social content
- May contain slides suitable for Instagram carousels or LinkedIn image posts
- Represents Beer's own framing of the House of Sak — use it to understand his narrative priorities

## How to Find It

```python
# Step 1: Find the folder
result = run_composio_tool("GOOGLEDRIVE_FIND_FILE", {
    "q": "name contains 'Sak Agent' and trashed = false",
    "fields": "files(id,name,mimeType,webViewLink)"
})
folder_id = result[0]["data"]["files"][0]["id"]

# Step 2: List children
children = run_composio_tool("GOOGLEDRIVE_LIST_CHILDREN_V2", {
    "folderId": folder_id,
    "maxResults": 50
})
```

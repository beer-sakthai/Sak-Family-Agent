---
name: SakSit-google-notebooklm
category: research
description: Upload sources and query with NotebookLM.
version: 0.1.0
author: Hermes
platforms: []
metadata:
  hermes:
    tags:
    - Google
    - NotebookLM
    - AI
    - Research
    - Audio
    - Podcast
---

# Google NotebookLM

NotebookLM is Google's AI-powered research and thinking partner. Upload your sources (PDFs, Google Docs, websites, YouTube videos, text), ask questions grounded in those sources, and generate Audio Overview conversations. It does NOT replace general-purpose LLM chat — it is citation-grounded, source-bound analysis. Requires a Google account. No API available.

## When to Use

- "Research this document and summarize it."
- "Create a podcast-style audio discussion from these sources."
- "Ask questions about a research paper, contract, or book."
- "Compare multiple sources and find common themes."
- "Generate a study guide or FAQ from uploaded material."
- "Turn meeting notes into a shareable notebook."

## Prerequisites

- A Google account (personal or Workspace). Free.
- Browser access to notebooklm.google.com.
- For local files: PDF, Google Docs, or text files ready to upload.

## How to Run

Access via browser at notebooklm.google.com. No CLI or API exists — this is a web-only product. The workflow is:

1. Navigate to notebooklm.google.com using `browser_navigate`.
2. Create or open a Notebook.
3. Add sources (click, upload, paste URL).
4. Interact through the chat interface or generate Audio Overview.
5. Read results via `browser_snapshot` or `browser_vision`.

## Quick Reference

| Action | Method |
|--------|--------|
| Open NotebookLM | `browser_navigate("https://notebooklm.google.com")` |
| Check for sign-in gate | `browser_snapshot()` then `browser_vision()` if needed |
| Interact with chat | `browser_type` into input, `browser_click` to submit |
| Read output | `browser_snapshot(full=True)` |
| Upload a source file | Simulate drag-and-drop or use file input `browser_type` |

## Procedure

### 1. Open NotebookLM

```text
browser_navigate(url="https://notebooklm.google.com")
```

NotebookLM **requires** Google sign-in. The URL redirects to `accounts.google.com/v3/signin/identifier?...`. Confirmed in testing (Jul 6, 2026).

The sign-in page has:
- **Email/phone textbox** — for entering the Google account email
- **Next button** — to proceed to password entry
- **Create account link** — for new accounts

Hermes cannot automate Google OAuth flows. Ask Beer to sign in once per browser session, then proceed.

### 2. Create a New Notebook

Once logged in, the page shows a list or a "+ New Notebook" button. Look for it via:

```text
browser_snapshot()
# Look for a button labeled with "+", "New", or "Create"
browser_click(ref="@e<ref>")
```

### 3. Add Sources

NotebookLM supports these source types:

| Source Type | How to Add |
|-------------|------------|
| **Google Doc** | Paste the Docs URL or select from Drive |
| **PDF** | Upload from local files (click upload, select) |
| **Website** | Paste the public URL |
| **YouTube** | Paste the video URL |
| **Plain text** | Paste or type directly |
| **Google Slides** | Paste the Slides URL |

After creating a notebook, find the "Add source" button:

```text
browser_snapshot()
browser_click(ref="<add source button ref>")
```

Then depending on source type:
- For a URL: `browser_type(ref="@e<N>", text="https://example.com/doc")` then submit
- For file upload: click the file input, submit via the browser's native picker (note: the Hermes browser sandbox may not support local file uploads — tell Beer to upload manually if needed)

### 4. Ask Questions

Use the chat panel to ask questions about your sources:

```text
browser_type(ref="@e<N>", text="Summarize the key findings from these sources.")
browser_click(ref="@e<submit ref>")
# Read the response
browser_snapshot(full=True)
```

NotebookLM answers are citation-grounded — each claim is linked back to the source. Read those back to Beer.

### 5. Generate Audio Overview

The Audio Overview feature creates a podcast-like discussion between two AI hosts. Find the "Audio Overview" or "Generate" button:

```text
browser_snapshot()
# Look for Audio Overview / Generate / Notebook guide options
browser_click(ref="@e<audio overview button ref>")
```

The generation takes 3-8 minutes depending on source size. The resulting audio can be downloaded as an MP3.

### 6. Share or Export

Notebooks can be shared via a link. Look for a "Share" button:

```text
browser_snapshot()
# Find and click Share
browser_click(ref="@e<share ref>")
```

## Pitfalls

- **Sign-in wall:** notebooklm.google.com redirects to Google sign-in. Cannot automate OAuth — Beer must sign in once per browser session.
- **No API:** NotebookLM has no public API. Everything goes through the browser UI.
- **File upload limits:** The browser sandbox may not support local file selection. If upload fails, ask Beer to upload manually or use a Google Doc/URL instead.
- **Audio Overview is slow:** Generating an Audio Overview takes 3-8 minutes. Use `process` with a background terminal + wait if running via cron, or just tell Beer to wait.
- **Source limits:** Notebooks have a maximum number of sources (typically 20-50 depending on version). Very large PDFs may be truncated.
- **Language:** Primarily English. Other languages may have limited Audio Overview support.
- **Citation-only responses:** The model will refuse to answer questions not grounded in the sources. This is by design — it prevents hallucination.
- **Vision tool needed for UI:** Some UI elements (buttons, menus) are only visually identifiable. Use `browser_vision` when `browser_snapshot` returns unlabeled elements.
- **Not a general-purpose chatbot:** NotebookLM is designed for source-grounded research only. Do not use it for open-ended Q&A.

## Verification

After uploading a source and asking a question, verify the answer contains inline citations (bracketed numbers like `[1]`, `[2]`) that reference the source material.

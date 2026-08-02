# Archive to Google Drive — Session Example (2026-07-06)

This session was the first time Beer asked to save social links to Google Drive after an audit. The flow and output serve as a template.

## Trigger

After showing all social platform links in-chat, Beer said:
> "save them for me in google drive"

## Flow

1. Searched Composio for Google Drive tools — found connection active for `beernanthasit@gmail.com`
2. No direct "create file" tool in Drive, but **Google Docs** via `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN` works
3. Crafted a Markdown document with a clean table and notes section
4. Created the doc → returned the link

## Input to GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN

**Title:** `Social Media Links - [Brand Name]`

```markdown
# Social Media Links — House of Sak

Beer's social presence at a glance. Last updated: July 6, 2026.

| Platform | Link | Status |
|----------|------|--------|
| **LinkedIn** | https://linkedin.com/in/vanityname/ | Connected ✅ |
| **YouTube** | https://youtube.com/@handle | Connected ✅ |
| **Instagram** | https://instagram.com/username | Connected ✅ |
| **Facebook Page** | https://facebook.com/page-id | Connected ✅ |
| **GitHub** | https://github.com/username | Active |
| **Hugging Face** | https://huggingface.co/username | Active |
```

## Markdown Table Rules for GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN

- Tables work well — header row auto-bolded and grey-highlighted
- Use `---` after the header row as standard Markdown
- Keep URLs as plain clickable text (Markdown link syntax `[text](url)` also works)
- Bold the platform names for visual hierarchy
- Add a horizontal rule `---` before the Notes section for visual separation
- Bullet points work for notes under the table
- Max ~1,000,000 characters per creation

## What NOT to Do

- Don't dump raw API JSON response into the doc
- Don't include access tokens, session IDs, or sensitive data
- Don't overformat — keep it a clean reference table Beer can visually scan

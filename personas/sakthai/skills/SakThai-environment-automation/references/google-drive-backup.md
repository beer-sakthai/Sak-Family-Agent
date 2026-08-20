# Google Drive + Supermemory Backup for Agent Data

**When:** Beer requests "save all" or "backup to Google Drive"
**Why:** Beer wants ALL important agent identity/config/skills data persisted to BOTH Supermemory AND Google Drive simultaneously.

## Prerequisites

- Composio MCP connected to Google Drive (account: `beernanthasit@gmail.com`, confirmed active)
- Supermemory container `hermes` active
- Key files identified: SOUL.md, config.yaml, channel_directory.json, agent-self-evolution guide, cycle docs, skills inventory

## Workflow

### Step 1 — Discover Google Drive tools via Composio

```python
# First call COMPOSIO_SEARCH_TOOLS with use_case like:
# "upload files and create folders in Google Drive"
# This returns available tool slugs and schema references.
```

Key tools:
- `GOOGLEDRIVE_FIND_FILE` — search for existing folder by name
- `GOOGLEDRIVE_CREATE_FOLDER` — create backup folder
- `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` — upload text/markdown/json content as Drive file

### Step 2 — Find or create the backup folder

```python
# Check if folder exists first:
GOOGLEDRIVE_FIND_FILE(q="name = 'SakThai-Agent-Backup' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")

# If not found, create it:
GOOGLEDRIVE_CREATE_FOLDER(name="SakThai-Agent-Backup")
# Returns folder ID like "1k_NdwlcRwcbsjCfaOPwGMJKLfvderIV-"
```

### Step 3 — Upload files in parallel via COMPOSIO_MULTI_EXECUTE_TOOL

Batch ALL independent file uploads into a single COMPOSIO_MULTI_EXECUTE_TOOL call. Each upload is a separate tool entry:

```python
# Template for each file:
{
    "tool_slug": "GOOGLEDRIVE_CREATE_FILE_FROM_TEXT",
    "arguments": {
        "file_name": "<filename>",
        "mime_type": "<mime-type>",  # text/markdown, text/plain, application/json
        "parent_id": "<folder-id>",
        "text_content": "<full content>"
    }
}
```

**MIME types by file type:**
| File type | MIME type |
|-----------|-----------|
| Markdown (.md) | `text/markdown` |
| Plain text (.txt, .yaml) | `text/plain` |
| JSON (.json) | `application/json` |
| CSV (.csv) | `text/csv` |

**Batch sizing:** Up to 10 files per call is safe with text content. For binary content (images, PDFs), use GOOGLEDRIVE_UPLOAD_FILE instead (requires s3key from a prior download).

### Step 4 — Verify uploads

Each successful upload returns:
```json
{
    "display_url": "https://drive.google.com/file/d/<id>/view",
    "id": "<file-id>",
    "name": "<filename>",
    "mimeType": "<mime-type>"
}
```

Check that count of successful results equals count of files uploaded. Report the Drive folder link to Beer.

### Step 5 — Save to Supermemory simultaneously

While uploading to Drive, also save confirmation and key facts to Supermemory:
```python
supermemory_save(content="Agent backup: <description> at <timestamp>")
supermemory_save(content="Key runtime facts: <model, providers, skill count, etc.>")
```

Also save to local memory:
```python
memory(action="add", target="memory", content="<YYYY-MM-DD: backup event log>")
```

## Files typically backed up

| File | Contents |
|------|----------|
| SOUL.md | Full agent persona (identity, charge, cycle, directives) |
| config.yaml | Model/provider config, security, MCP servers |
| channel-directory.json | All connected platform channels |
| agent-self-evolution-guide.md | 6-cycle workflow for agent growth |
| 6-cycle-workflow.md | Dream/Hope/Care/Joy/Trust/Growth definitions |
| skills-inventory.md | Complete skill library with descriptions |

## Pitfalls

- **Folder IDs differ from folder names.** Always use the returned folder ID, not the name, as parent_id. If parent_id is omitted, files land in Drive root.
- **Rate limits.** Google Drive API limits to ~10 writes/second. For large batches (>10 files), add small delays between COMPOSIO_MULTI_EXECUTE_TOOL calls or use fewer items per batch.
- **Binary files.** GOOGLEDRIVE_CREATE_FILE_FROM_TEXT only accepts text content. For binary files (images, PDFs), use GOOGLEDRIVE_UPLOAD_FILE which requires a pre-uploaded s3key file reference.
- **Verification.** Google Drive permits duplicate folder names — always store and reuse the returned folder ID rather than relying on names for future lookups.

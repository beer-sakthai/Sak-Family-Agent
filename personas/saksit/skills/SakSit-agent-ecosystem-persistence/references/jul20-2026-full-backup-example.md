# Session Reference: Full Backup — Jul 20, 2026

## Context

Beer requested: "All save in supermemory and Google drive" → clarified "1 and everything in what your have"

His entire backlog + go-forward persistence directive.

## Google Drive IDs Discovered

| Item | ID |
|------|----|
| Sak Agent (parent) | `1UWC9yuCOsmMi9j61Aq1NSMFvm5clalin` |
| SakSit (pre-existing) | `1k1E1JYi_zC73uxTUADLUjxxXRamBBgot` |
| Knowledge Base (created) | `12FFEsInhhpBm953wJZxqVifZIk0d4A9t` |

**Important:** Always search by `name_exact` before creating folders. A second CREATE_FOLDER call silently duplicates.

## Files Saved

| File | Type | Format | ID |
|------|------|--------|----|
| SakSit SOUL.md (Identity Document).txt | Text | `text/plain` | `1Em3Zfa01G-n3-FdoHPCJux84k01pPDiL` |
| SakSit Complete Knowledge Base | Google Doc | `application/vnd.google-apps.document` | `1_-hLjyC9Hzh8uxDfMe3kLa6BHHclnZbRtTtytcIYdQg` |
| SakSit Skills Inventory.txt | Text | `text/plain` (via upload_file) | `1q-vgFBwbZhsyGdDr2klvfeyNF9vCKUUN` |
| SakSit Supermemory Profile Dump (Jul 20 2026).txt | Text | `text/plain` | `1ycJos00jjijWSKrNC4gzui_foGZMAjJb` |
| Session Log - Jul 20 2026 - Full Backup.txt | Text | `text/plain` | `1hMTNYMj-q6SqS4pytwr8IbtevnsGsil9` |

## Skills Upload Path

Skills inventory was too large for `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` inline (6,131 chars). Workaround:
1. Generate content in COMPOSIO_REMOTE_WORKBENCH
2. Write to `/mnt/files/<filename>` in sandbox
3. Call `upload_local_file(path)` → get s3key
4. Call `GOOGLEDRIVE_UPLOAD_FILE` with `{file_to_upload: {name, mimetype, s3key}}`

## Memory State After

- Before: 2,171/2,200 chars (98.7%)
- After: 2,103/2,200 chars (95.6%)
- Operations: shortened 4 entries (removed redundant detail), added auto-save instruction

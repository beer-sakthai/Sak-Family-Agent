---
name: SakSit-agent-ecosystem-persistence
description: Full-stack agent knowledge backup to Google Drive + Supermemory — inventory all agent state (memory, supermemory, skills, soul, config), structure a Drive folder hierarchy, persist each piece in the right format, consolidate memory, and log the operation.
trigger: |
  When the user says "save everything", "back up", "persist", "keep this", "store in drive", or any request to save current agent state to durable external storage.
category: productivity
---

# Sak Agent Ecosystem Persistence

Full backup of all agent knowledge to Google Drive + Supermemory.

## Why This Exists

Beer works across sessions with no guaranteed context continuity. A full persistence operation ensures nothing is lost — memories, skills, identity docs, and session learnings all get saved to durable, human-readable storage.

Beer's explicit directive (Jul 20, 2026): **Everything** goes to both Supermemory AND Google Drive. Dual persistence, no exceptions.

## Trigger Conditions

Run this when:
- User says "save everything", "backup", "persist", "store this"
- End of a multi-session project phase
- Before agent profile changes (SOUL.md edits, skill deletions)
- User says "all save in supermemory and Google drive"
- Consolidation needed (memory near 100% capacity, typically ~2,100/2,200 chars)

## Required Prep

1. **Composio Google Drive connection** — verify active via COMPOSIO_SEARCH_TOOLS (look for googledrive toolkit with ACTIVE status)
2. **Supermemory** — accessible via supermemory_profile, supermemory_save
3. **Hermes memory** — accessible via memory tool

## Workflow

### Step 1: Inventory Everything

```
┌─────────────────┐
│  1. INVENTORY   │
│  ┌───────────┐  │
│  │ Suprmemry │  │
│  │ Memory    │  │
│  │ Skills    │  │
│  │ SOUL.md   │  │
│  │ Configs   │  │
│  └───────────┘  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  2. STRUCTURE   │
│  ┌───────────┐  │
│  │ Agent/    │  │
│  │ ├─Name/   │  │
│  │ │ ├─KB/   │  │
│  └───────────┘  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  3. PERSIST     │
│  ┌───────────┐  │
│  │ SOUL→TXT  │  │
│  │ KB →Doc   │  │
│  │ Skils→TXT │  │
│  │ Supr→TXT  │  │
│  │ Log →TXT  │  │
│  └───────────┘  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  4. CONSOLIDATE │
│  ┌───────────┐  │
│  │ Memory    │  │
│  │ Suprmemry │  │
│  └───────────┘  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  5. LOG & REPORT│
│  ┌───────────┐  │
│  │ Session   │  │
│  │ Links     │  │
│  │ Summary   │  │
│  └───────────┘  │
└─────────────────┘
```

### Step 1: Inventory

Gather **all** of these in parallel:

- **Supermemory profile** → `supermemory_profile()`
- **Hermes memory** → `memory(action='add')` (even to read — the response shows current entries when near full)
- **Skills list** → `skills_list()` (capture names + descriptions)
- **SOUL.md** → `read_file(SOUL.md path from profile dir)`
- **Current session context** → what was just discussed/decided

### Step 2: Structure the Drive Folder

Find/create this hierarchy (using GOOGLEDRIVE_FIND_FOLDER + GOOGLEDRIVE_CREATE_FOLDER):

```
Sak Agent/               (parent folder, find or create)
└── AgentName/           (e.g. SakSit, SakThai — find existing FIRST)
    └── Knowledge Base/  (create inside AgentName)
```

**Critical:** Always search for existing folders first with `GOOGLEDRIVE_FIND_FOLDER(name_exact=...)`. Never create duplicates. Beer's Sak Agent folder ID reference: `1UWC9yuCOsmMi9j61Aq1NSMFvm5clalin`.

### Step 3: Persist to Drive

Use the right tool per format:

| Content Type | Tool | MIME Type | Notes |
|-------------|------|-----------|-------|
| **SOUL.md / identity doc** | `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` | `text/plain` | Raw text preserves markdown |
| **Knowledge Base / comprehensive** | `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` | `application/vnd.google-apps.document` | Google Doc = searchable, editable |
| **Skills inventory** | Workbench → `upload_local_file` → `GOOGLEDRIVE_UPLOAD_FILE` | `text/plain` | For large files, upload via S3 |
| **Supermemory profile dump** | `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` | `text/plain` | Plain text snapshot |
| **Session log** | `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` | `text/plain` | Dated filename |

**Pitfall:** `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` uses `text_content`, `file_name`, `parent_id`, and optional `mime_type`. The `parent_id` must be a Google Drive folder ID (opaque string), not a name. Use `GOOGLEDRIVE_FIND_FOLDER` first to get IDs.

**Pitfall:** `GOOGLEDRIVE_UPLOAD_FILE` requires `file_to_upload` with `{name, mimetype, s3key}`. Get the s3key via `upload_local_file()` in the workbench first.

### Step 4: Consolidate Memory

If Hermes memory is near capacity (>90%), consolidate before saving new entries:
- Remove or shorten stale entries (outdated token info, completed tasks)
- Merge overlapping entries
- Add the new auto-save/backup instruction
- Use batch operations with `operations` array for atomic consolidation

Always add to **both** memory and Supermemory so either can serve as the fallback.

### Step 5: Log & Report

Save a session log file with:
- Date and purpose of backup
- What was saved and where (file IDs/links)
- Any changes made (memory consolidation, new entries)
- Folder structure for reference
- Beer's current state (homeless, zero-cost ops, etc.)

Report back to user with a summary table: file names, types, and Drive links.

## Pitfalls

- **Duplicate folders:** Always search by `name_exact` before creating. A second `GOOGLEDRIVE_CREATE_FOLDER` with the same name creates a duplicate silently.
- **Memory full:** Cannot add to memory when >95% full without batch consolidation. Check usage string from the `memory` tool response.
- **s3key upload:** The workbench's `upload_local_file()` returns an s3key string. Pass it in `file_to_upload.s3key`. The mimetype must match the actual file content.
- **Google Doc mime types:** `text/plain` renders as editable text; `application/vnd.google-apps.document` creates a Google Doc. For docs that should be searchable/editable online, use the latter.
- **Linked file reading:** `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` returns `id` and `display_url` at the top level, not nested under `data.file`.
- **Rate limits:** Rapid successive calls to `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` can trigger 403 rateLimitExceeded or 429 userRateLimitExceeded. Space creation calls with brief delays or batch in a workbench session.
- **Zero-cost mandate:** Never suggest paid backup/storage services. Google Drive is free for Beer's use case.

## Verification Checklist

- [ ] All files visible in Drive web UI under correct folder
- [ ] Memory usage below 95%
- [ ] Supermemory has a dated entry recording the backup
- [ ] Skill inventory includes ALL current skills
- [ ] SOUL.md content matches the live profile version
- [ ] User received summary with links

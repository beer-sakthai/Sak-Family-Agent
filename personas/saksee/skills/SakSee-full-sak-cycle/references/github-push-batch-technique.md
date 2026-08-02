# GitHub Push via Composio (Batch-Split Technique)

Used during the Joy stage of the Full Sak Cycle (July 4-5, 2026) to push 15 files including a binary PNG to `beer-sakthai/house-of-sak`.

## The problem
15 files total: 14 text (57KB) + 1 PNG image (65KB base64). Too large for one GITHUB_COMMIT_MULTIPLE_FILES call.

## The solution: batch-split into 3 commits

### Batch 1: Smaller text files (7 files, ~23KB)
Origin stories + audit + crisis + dream + lessons.
→ Commit: "📂 SakSee diary — part 1/3"

### Batch 2: Larger text files (7 files, ~34KB)
Plan, services, verify, index.html, captions, reflection.
→ Commit: "📂 SakSee diary — part 2/3"

### Batch 3: PNG only (1 file, 65KB base64)
ig-card.png as base64 encoding.
→ Commit: "📂 SakSee diary — part 3/3"

## Key details
- Text files: `encoding: "utf-8"`, pass content as plain string
- PNG: `encoding: "base64"`, pass base64-encoded string (generate via `base64.b64encode(raw).decode()`)
- Author/committer fields: include `name` and `email` for attribution
- All commits to the same branch (`main`) — sequential, no conflicts
- Used `COMPOSIO_MULTI_EXECUTE_TOOL` inline (NOT workbench — workbench is a remote sandbox that cannot access local files)

## Pitfall: Facebook image URL from GitHub raw
GitHub raw URLs (`raw.githubusercontent.com/...`) may be blocked by Facebook's image fetcher. If a photo post fails with a generic API error after a successful text post, the image URL is the likely cause. Post text-only first, then try a different image host for the visual.
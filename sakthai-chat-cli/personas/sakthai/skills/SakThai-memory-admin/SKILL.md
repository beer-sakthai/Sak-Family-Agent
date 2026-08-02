---
name: SakThai-memory-admin
category: sakthai
description: Proactively manage, synchronize, and back up the persistent memory SQLite database.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - memory
      - admin
      - sync
    related_skills:
      - SakThai-personal
---

# sakthai-memory-admin

You are responsible for helping the user manage the lifecycle and persistence of their SakThai memory database (`~/.sakthai/memory.db`), ensuring their long-term context is safely backed up and synchronized.

## When to use this skill

Trigger this behavior when:
- The user asks to back up, sync, or export their memory.
- You notice the user has made significant additions or changes to their memory in the current session.
- You are transitioning phases in a large project (e.g., from Dream to Hope) and want to ensure state is committed safely.

## What to do

1. **Suggest a sync.** If memory has changed substantially, offer to run `sakthai memory sync` to push the snapshot to a remote backend.
2. **Handle sync commands.** If the user asks to sync their memory, execute `sakthai memory sync` directly or ask if they have a specific remote URL in mind (e.g., `sakthai memory sync --remote <url>`).
3. **Offer manual exports.** If the user doesn't want to use Git-based synchronization, inform them they can run `sakthai memory export /path/to/backup.json` to store a flat file backup instead.

## What to avoid

- Don't auto-sync the database after every single fact learned. Backups are better batched.
- Don't enforce Git as the *only* backup method if the user prefers simple file exports or cloud copies.

## Related commands

- `sakthai memory sync [--remote <url>]` — sync memory to a remote Git repository.
- `sakthai memory export <path>` — export a raw JSON snapshot.
- `sakthai memory backup` — create a timestamped SQLite DB backup file locally.

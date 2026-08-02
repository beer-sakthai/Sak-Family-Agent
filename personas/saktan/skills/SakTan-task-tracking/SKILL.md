---
name: SakTan-task-tracking
category: productivity
description: Track recurring tasks and todos in SakThai memory, with optional sync to Apple Reminders, Notion, or Airtable.
version: 1.0.0
author: SakTan
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [tasks, todo, memory, operations, tracking]
    related_skills: [SakTan-daily-briefing, SakTan-close-the-day, SakTan-apple-reminders, SakTan-notion, SakTan-airtable]
---

# Task Tracking

SakThai memory (`learn`/`recall`/`search`) is the source of truth for task
state. External tools (Apple Reminders, Notion, Airtable) are optional
mirrors for tasks Beer wants visible outside the chat — not a replacement for
memory.

## Recording a task

Use `learn` with `kind=task`:

```
learn(value="<task description>", kind="task", key="<short-slug>")
```

- `key` should be a short, stable slug (e.g. `renew-passport`,
  `q3-invoice-followup`) so the same task can be recalled, updated, or closed
  by name later instead of by re-describing it.
- Capture the task **as Beer stated it** — don't editorialize or expand scope
  in the memory record.
- If Beer gives a due date or recurrence ("every Monday", "by Friday"),
  include it in the value text; memory facts don't have a native due-date
  field, so the date must be readable in the stored text itself.

## Checking open tasks

- `recall` — the default view; scan for `kind=task` entries.
- `search(query="task")` or search for a specific keyword/key when Beer asks
  about one item ("what was that thing about the passport").

## Closing a task

Memory is append-only for facts (no native delete outside `forget`). To close
a task without losing the history of what was done:

```
learn(value="<key> — done: <one-line outcome>", kind="task-done", key="<same key>")
```

This keeps the original task fact intact for context but marks completion
clearly enough that `SakTan-daily-briefing` and `SakTan-close-the-day` can
filter it out of "open" views (treat any `key` with a matching `task-done`
entry as closed).

## Syncing to external tools

Only sync a task externally when Beer asks for it to live somewhere specific
(a shared Reminders list, a Notion board, an Airtable base). Use the matching
skill:

- **Apple Reminders** — `SakTan-apple-reminders` for personal, device-synced
  reminders with native due dates/alerts.
- **Notion** — `SakTan-notion` for a shared, structured task board.
- **Airtable** — `SakTan-airtable` for anything that needs custom fields,
  views, or is already tracked there.

When syncing, still `learn` the task in memory first — the external tool is
additive, memory stays authoritative so `SakTan-daily-briefing` doesn't
depend on an external API being reachable.

## Pitfalls

- Don't create a new `key` for what's actually the same recurring task
  restated differently — `search` first to check whether it already exists.
- Don't silently drop a task because it's overdue; surface overdue items
  first in any briefing, never bury them.

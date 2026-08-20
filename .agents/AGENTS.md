# Sak Family Agent — Project Rules

Rules specific to the `Sak-Family-Agent` repository. These supplement global rules.

---

## Workflow: Plan First

- **Always read and update `PLAN.md` before starting any work** in this repo.
  - Mark tasks `[ ]` → `[/]` (in progress) at the start of a phase.
  - Mark `[/]` → `[x] YYYY-MM-DD` (done with date) once the work is verified.
- **Never start coding a phase until it is checked off in PLAN.md** as in-progress.
- Terse one-word or short user approvals like `process`, `go`, `do it`, `run` after a plan summary = explicit approval to execute all queued plan steps.

---

## PLAN.md Safety

- **Never overwrite `PLAN.md` entirely.** Use `multi_replace_file_content` with targeted chunk replacements only.
- When marking tasks complete, find and replace only the specific `- [ ]` or `- [/]` line(s) — not whole sections.
- After any edit to `PLAN.md`, immediately re-read it to verify the surrounding content is intact before continuing.

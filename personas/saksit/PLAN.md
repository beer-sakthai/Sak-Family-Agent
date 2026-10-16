# PLAN.md — SakSit 📣 Task-by-Task Roadmap
> *Brand Copy, Social Posts, Hub Dataset Cards, Storytelling — Execution Plan*\
> *Each task's **Status** follows the root PLAN.md: `[ ]` open → `[/]` in progress → `[x] YYYY-MM-DD` done.*\
> *Commands that call `sakthai` from inside an agent run need `SAKTHAI_SHELL_ALLOW`; the `run_command` tool is off without it.*

---

### Phase 1: Foundation

#### 🔹 Task 1.1: Config preflight
- **Status**: [ ]
- **Goal**: Confirm SakSit's provider, model and skills resolve.
- **Command**: `SAKTHAI_HOME=$(mktemp -d) sakthai run "preflight" --persona saksit --no-mcp --dry-run`
- **Acceptance Criteria**: The preflight shows `huggingface` → `deepseek-ai/DeepSeek-V4-Flash`; it exits 0 once `HF_TOKEN` is set (without it, "no credentials" is the expected failure).

#### 🔹 Task 1.2: Read the family first
- **Status**: [ ]
- **Goal**: Know charge, conservation mode and the deputy chain before any task.
- **Command**: the SOUL's pre-task checklist (see MEMORY.md)
- **Acceptance Criteria**: The task starts from the family's current state, not from a guess.

---

### Phase 2: Content

#### 🔹 Task 2.1: Family update for PR #1636
- **Status**: [ ]
- **Goal**: Draft a short post on the skill-metadata cleanup: tags visible for 75 skills, Windows-safe skill folders, safer persona plans.
- **Command**: `sakthai run "Draft the PR #1636 family update" --persona saksit`
- **Acceptance Criteria**: Draft only, tagged `hub-draft` + `awaiting-review`; every claim matches the merged PR; nothing is published without Beer's go-ahead.

#### 🔹 Task 2.2: Model card copy
- **Status**: [ ]
- **Goal**: Refresh a model card's content layer.
- **Command**: Gate 1 context from SakThai first
- **Acceptance Criteria**: Unverified claims carry `[PENDING VERIFICATION]`; SakThai pushes the card, never SakSit.

---

### Phase 3: Data

#### 🔹 Task 3.1: Data through SakSee
- **Status**: [ ]
- **Goal**: Get the numbers a post needs without scraping.
- **Command**: A `data-request` tag for SakSee
- **Acceptance Criteria**: The post uses SakSee's result, with its `retrieved_at` timestamp.

---

*SakSit Task Plan · House of Sak*

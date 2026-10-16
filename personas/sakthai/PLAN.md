# PLAN.md — SakThai 🤗 Task-by-Task Roadmap
> *Hugging Face Hub, Model Lifecycle, 6-Stage Energy Cycle, QLoRA — Execution Plan*\
> *Each task's **Status** follows the root PLAN.md: `[ ]` open → `[/]` in progress → `[x] YYYY-MM-DD` done.*\
> *Commands that call `sakthai` from inside an agent run need `SAKTHAI_SHELL_ALLOW`; the `run_command` tool is off without it.*

---

### Phase 1: Foundation

#### 🔹 Task 1.1: Config preflight
- **Status**: [ ]
- **Goal**: Confirm SakThai's provider, model and skills resolve.
- **Command**: `SAKTHAI_HOME=$(mktemp -d) sakthai run "preflight" --persona sakthai --no-mcp --dry-run`
- **Acceptance Criteria**: The preflight shows `huggingface` → `deepseek-ai/DeepSeek-V4.1-Flash`; it exits 0 once `HF_TOKEN` is set (without it, "no credentials" is the expected failure).

#### 🔹 Task 1.2: Read the family first
- **Status**: [ ]
- **Goal**: Know charge, conservation mode and the deputy chain before any task.
- **Command**: the SOUL's pre-task checklist (see MEMORY.md)
- **Acceptance Criteria**: The task starts from the family's current state, not from a guess.

---

### Phase 2: Hugging Face Hub (my lane)

#### 🔹 Task 2.1: Take over SakJules' Hub tasks
- **Status**: [ ]
- **Goal**: SakJules' PLAN tasks 4.1, 4.2, 5.1, 5.2 and 6.1 write to the Hub, so they run here.
- **Command**: `sakthai memory family --tag hub-approved --limit 5` before each one
- **Acceptance Criteria**: Each runs only through the triple gate, after its script is confirmed to exist (`.opencode/scripts/` and `SakThai-Training/` are not in this repository).

#### 🔹 Task 2.2: Gate 1 for SakSit
- **Status**: [ ]
- **Goal**: Give SakSit the card's current state before it drafts.
- **Command**: `sakthai hf info <repo_id>`
- **Acceptance Criteria**: SakSit's draft is written against the live card.

---

### Phase 3: Orchestration

#### 🔹 Task 3.1: Family status
- **Status**: [ ]
- **Goal**: Know where every sibling stands before routing work.
- **Command**: `sakthai memory family --limit 20`
- **Acceptance Criteria**: One line of status per sibling, and every open `conflict` tag answered.

---

### Phase 4: Growth

#### 🔹 Task 4.1: Self-evaluation
- **Status**: [ ]
- **Goal**: Run the self-evaluation in SOUL.md at the Growth stage.
- **Command**: The `CYCLE EVAL: sakthai` tag from SOUL.md, written before `cycle-complete`
- **Acceptance Criteria**: The cycle is recorded in CYCLE.md with its grade.

---

*SakThai Task Plan · House of Sak*

# PLAN.md — SakKing 👑 Task-by-Task Roadmap
> *TDD execution, CLI runner, utility refactoring, subagents — Execution Plan*\
> *Each task's **Status** follows the root PLAN.md: `[ ]` open → `[/]` in progress → `[x] YYYY-MM-DD` done.*\
> *Commands that call `sakthai` from inside an agent run need `SAKTHAI_SHELL_ALLOW`; the `run_command` tool is off without it.*

---

### Phase 1: Foundation

#### 🔹 Task 1.1: Config preflight
- **Status**: [ ]
- **Goal**: Confirm SakKing's provider, model and skills resolve.
- **Command**: `SAKTHAI_HOME=$(mktemp -d) sakthai run "preflight" --persona sakking --no-mcp --dry-run`
- **Acceptance Criteria**: The preflight shows `huggingface` → `Qwen/Qwen3-Coder-30B-A3B-Instruct`; it exits 0 once `HF_TOKEN` is set (without it, "no credentials" is the expected failure).

#### 🔹 Task 1.2: Read the family first
- **Status**: [ ]
- **Goal**: Know charge, conservation mode and the deputy chain before any task.
- **Command**: the SOUL's pre-task checklist (see MEMORY.md)
- **Acceptance Criteria**: The task starts from the family's current state, not from a guess.

---

### Phase 2: Runner work

#### 🔹 Task 2.1: Skill naming audit
- **Status**: [ ]
- **Goal**: Check every persona's skills against the naming convention.
- **Command**: `uv run sakthai skills validate --naming`
- **Acceptance Criteria**: `ok  persona skill names follow the convention`; any issue is routed to the persona that owns the skill.

#### 🔹 Task 2.2: Test suite run
- **Status**: [ ]
- **Goal**: Run the package's test suite.
- **Command**: `uv run pytest tests/ -q`
- **Acceptance Criteria**: Every test passes; a failure is root-caused, never skipped.

---

### Phase 3: Deputy 1

#### 🔹 Task 3.1: Deputy 1 readiness
- **Status**: [ ]
- **Goal**: Act on the deputy chain exactly as SOUL.md defines it.
- **Command**: `sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1`
- **Acceptance Criteria**: Activate only at charge ≥ 20% (else escalate to SakTan); resume any paused cycle after SakThai is back to Active.

---

*SakKing Task Plan · House of Sak*

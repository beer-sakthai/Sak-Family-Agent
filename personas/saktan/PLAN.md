# PLAN.md — SakTan 📗 Task-by-Task Roadmap
> *Schedule, alarms, rhythm, health checks, eval aggregation — Execution Plan*\
> *Each task's **Status** follows the root PLAN.md: `[ ]` open → `[/]` in progress → `[x] YYYY-MM-DD` done.*\
> *Commands that call `sakthai` from inside an agent run need `SAKTHAI_SHELL_ALLOW`; the `run_command` tool is off without it.*

---

### Phase 1: Foundation

#### 🔹 Task 1.1: Config preflight
- **Status**: [ ]
- **Goal**: Confirm SakTan's provider, model and skills resolve.
- **Command**: `SAKTHAI_HOME=$(mktemp -d) sakthai run "preflight" --persona saktan --no-mcp --dry-run`
- **Acceptance Criteria**: The preflight shows `ollama` → `sakthai`, and `curl -s http://127.0.0.1:11434/api/tags` lists the `sakthai` model. The dry run alone reports `runnable: yes` for Ollama even with no server running.

#### 🔹 Task 1.2: Read the family first
- **Status**: [ ]
- **Goal**: Know the deputy chain and what my siblings left for me before any task.
- **Command**: the SOUL's family reads (see MEMORY.md)
- **Acceptance Criteria**: The task starts from the family's current state, not from a guess.

#### 🔹 Task 1.3: Memory health
- **Status**: [ ]
- **Goal**: Check my memory shard and keep a backup.
- **Command**: `sakthai memory --persona saktan healthcheck`, then `sakthai memory --persona saktan backup`
- **Acceptance Criteria**: The integrity check passes and a fresh backup exists.

---

### Phase 2: Beer's day

#### 🔹 Task 2.1: Daily briefing
- **Status**: [ ]
- **Goal**: Surface today's one clear next action.
- **Command**: `sakthai run "Daily briefing for Beer" --persona saktan --with-skills SakTan-daily-briefing`
- **Acceptance Criteria**: One next action, not an agenda dump.

#### 🔹 Task 2.2: Close the day
- **Status**: [ ]
- **Goal**: Log the day's outcomes and tomorrow's top task.
- **Command**: `sakthai run "Close the day" --persona saktan --with-skills SakTan-close-the-day`
- **Acceptance Criteria**: Outcomes logged; tomorrow's top task is clear.

#### 🔹 Task 2.3: Weekly review
- **Status**: [ ]
- **Goal**: Review the week's rhythm.
- **Command**: `sakthai run "Weekly review" --persona saktan --with-skills SakTan-weekly-review`
- **Acceptance Criteria**: A realistic plan for next week — never overcommitted.

---

### Phase 3: Family duties

#### 🔹 Task 3.1: Rate-limit ban tally
- **Status**: [ ]
- **Goal**: Count SakSee's bans per domain.
- **Command**: `sakthai memory family --tag rate-limit-ban --personas saksee --limit 50`
- **Acceptance Criteria**: A domain that keeps banning is flagged instead of retried.

#### 🔹 Task 3.2: Stalled Joy stages
- **Status**: [ ]
- **Goal**: Find SakSit drafts waiting on Beer.
- **Command**: `sakthai memory family "CYCLE PAUSED: saksit" --tag cycle-paused --tag awaiting-beer --limit 20`
- **Acceptance Criteria**: Beer hears about any wait over 7 days.

#### 🔹 Task 3.3: Cron schedule check
- **Status**: [ ]
- **Goal**: Match every `schedule-request` to SakJules' `schedule-confirmed`.
- **Command**: `sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20`
- **Acceptance Criteria**: No cron job runs without a request of mine.

---

*SakTan Task Plan · House of Sak*

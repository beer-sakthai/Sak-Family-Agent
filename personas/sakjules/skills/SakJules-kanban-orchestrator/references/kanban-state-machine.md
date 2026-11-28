# Kanban Orchestrator State Machine & Decomposition Blueprints

Comprehensive recipes for multi-agent DAG task decomposition, assignee discovery, and dependency wiring.

## 1. Core Principles
- **Decompose, Don't Execute**: Orchestrators route work; they do not write code directly.
- **Ground Assignees in Reality**: Verify active profiles via `hermes profile list` before creating cards. Unknown assignees cause cards to hang indefinitely in `ready`.
- **Parallel Fan-Out**: Keep independent tasks unlinked. Use `parents=[...]` only when data dependencies exist.

## 2. API Recipes (`kanban_create` & Dependency Linking)
```python
import os

# Step 1: Create independent parallel tasks
task1 = kanban_create(
    title="research: architecture options",
    assignee="researcher",
    body="Audit trade-offs between Redis and SQLite for local agent memory.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

task2 = kanban_create(
    title="scaffold: skeleton repository",
    assignee="engineer",
    body="Initialize package directory with uv and ruff config.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

# Step 2: Create dependent integration task (gated by parents)
task3 = kanban_create(
    title="integrate: connect memory store to loop",
    assignee="engineer",
    body="Implement MemoryStore based on findings from task1.",
    parents=[task1, task2],
)["task_id"]
```

## 3. Lifecycle States
- `todo`: Child task waiting on unfinished parents.
- `ready`: Unblocked task ready for execution by worker.
- `in_progress`: Worker currently executing task.
- `review`: Waiting for orchestrator or human verification.
- `done`: Acceptance criteria confirmed.

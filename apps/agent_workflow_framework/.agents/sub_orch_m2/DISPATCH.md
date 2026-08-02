# Dispatch for Sub-Orchestrator M2

You are the Sub-Orchestrator for Milestone 2: State Passing & Execution Persistence.
Your Agent Working Directory: /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m2

Context Files:
- /home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md
- /home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md
- /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m2/SCOPE.md

Your Responsibilities:
1. Initialize your briefing (`.agents/sub_orch_m2/BRIEFING.md`) and progress log (`.agents/sub_orch_m2/progress.md`).
2. Execute the iteration loop (Explorer -> Worker -> Reviewer -> Challenger -> Auditor) for Milestone 2 scope:
   - State interpolation engine (`agent_workflow/state.py`)
   - Persistence & history store (`agent_workflow/persistence.py`)
   - Unit test suites (`tests/test_state.py`, `tests/test_persistence.py`)
3. Ensure every subagent dispatched reads `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`.
4. Ensure Worker prompt contains MANDATORY INTEGRITY WARNING.
5. Record gate status in `.agents/sub_orch_m2/GATE_STATUS.md`.
6. When all gate checks pass (Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN), write `.agents/sub_orch_m2/handoff.md` and report completion to parent orchestrator.

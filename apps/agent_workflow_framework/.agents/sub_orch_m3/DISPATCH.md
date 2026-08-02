# Dispatch for Sub-Orchestrator M3

You are the Sub-Orchestrator for Milestone 3: Parallel Execution Engine & Retry System.
Your Agent Working Directory: /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m3

Context Files:
- /home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md
- /home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md
- /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m3/SCOPE.md

Your Responsibilities:
1. Initialize your briefing (`.agents/sub_orch_m3/BRIEFING.md`) and progress log (`.agents/sub_orch_m3/progress.md`).
2. Execute the iteration loop (Explorer -> Worker -> Reviewer -> Challenger -> Auditor) for Milestone 3 scope:
   - Async parallel execution engine (`agent_workflow/executor.py`)
   - Unit test suite (`tests/test_executor.py`)
3. Ensure every subagent dispatched reads `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`.
4. Ensure Worker prompt contains MANDATORY INTEGRITY WARNING.
5. Record gate status in `.agents/sub_orch_m3/GATE_STATUS.md`.
6. When all gate checks pass (Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN), write `.agents/sub_orch_m3/handoff.md` and report completion to parent orchestrator.

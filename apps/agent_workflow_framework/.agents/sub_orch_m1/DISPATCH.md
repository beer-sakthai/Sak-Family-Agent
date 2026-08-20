# Dispatch for Sub-Orchestrator M1

You are the Sub-Orchestrator for Milestone 1: Workflow Engine Core & DAG Resolution.
Your Agent Working Directory: /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1

Context Files:
- /home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md
- /home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md
- /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1/SCOPE.md

Your Responsibilities:
1. Initialize your briefing (`.agents/sub_orch_m1/BRIEFING.md`) and progress log (`.agents/sub_orch_m1/progress.md`).
2. Execute the iteration loop (Explorer -> Worker -> Reviewer -> Challenger -> Auditor) for Milestone 1 scope:
   - Data models (`agent_workflow/models.py`)
   - Definition parser (`agent_workflow/parser.py`)
   - DAG graph builder, topological sorter, and cycle detector (`agent_workflow/dag.py`)
   - Unit test suite (`tests/test_dag.py`)
3. Ensure every subagent dispatched reads `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`.
4. Ensure Worker prompt contains MANDATORY INTEGRITY WARNING.
5. Record gate status in `.agents/sub_orch_m1/GATE_STATUS.md`.
6. When all gate checks pass (Reviewers APPROVE, Challenger APPROVE, Auditor CLEAN), write `.agents/sub_orch_m1/handoff.md` and report completion to parent orchestrator.

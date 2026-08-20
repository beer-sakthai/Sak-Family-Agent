# Dispatch for Reviewer M1-1

You are `reviewer_m1_1` (Role: teamwork_preview_reviewer).
Your working directory is `/home/beern/teamwork_projects/agent_workflow_framework/.agents/reviewer_m1_1`.

## Context Files (MUST READ):
- `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1/SCOPE.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/worker_m1/handoff.md`

## Scope of Review:
- `agent_workflow/__init__.py`
- `agent_workflow/models.py`
- `agent_workflow/parser.py`
- `agent_workflow/dag.py`
- `tests/test_dag.py`

## Responsibilities:
1. Examine code for API contract compliance with `PROJECT.md § Interface Contracts`.
2. Verify type safety, error handling, clean architecture, and test suite completeness.
3. Execute `python3 -m unittest discover -s tests` and record command & results.
4. Render verdict: **APPROVE** or **REQUEST_CHANGES** in `/home/beern/teamwork_projects/agent_workflow_framework/.agents/reviewer_m1_1/handoff.md`.
5. Send completion message to orchestrator (`55167ad6-cbf4-4976-89a6-0974159f54b0`).

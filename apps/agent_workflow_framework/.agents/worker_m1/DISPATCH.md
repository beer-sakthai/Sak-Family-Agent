# Dispatch for Worker M1

You are `worker_m1` (Role: teamwork_preview_worker).
Your working directory is `/home/beern/teamwork_projects/agent_workflow_framework/.agents/worker_m1`.

## Context Files (MUST READ):
- `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1/SCOPE.md`

## Explorer Handoff Reports (MUST READ):
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_1/handoff.md` (and `proposed_models.py`)
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_2/handoff.md` (and `proposed_parser.py`)
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/explorer_m1_3/handoff.md`

## File Ownership (EXCLUSIVELY YOURS TO IMPLEMENT):
- `agent_workflow/__init__.py`
- `agent_workflow/models.py`
- `agent_workflow/parser.py`
- `agent_workflow/dag.py`
- `tests/__init__.py`
- `tests/test_dag.py`

## Mission & Tasks:
1. Implement `agent_workflow/__init__.py` exposing the core models, parser functions, and DAG validation/batching functions.
2. Implement `agent_workflow/models.py` per the verified design from `explorer_m1_1`.
3. Implement `agent_workflow/parser.py` per the verified design from `explorer_m1_2`.
4. Implement `agent_workflow/dag.py` per the verified design from `explorer_m1_3`.
5. Implement `tests/__init__.py` and `tests/test_dag.py` with the 20 comprehensive unit tests specified by `explorer_m1_3`.
6. Run `python3 -m unittest discover -s tests` to verify all tests pass with exit code 0.

## MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverables:
1. Write target source code files.
2. Run test verification and capture build/test output.
3. Write your handoff report to `/home/beern/teamwork_projects/agent_workflow_framework/.agents/worker_m1/handoff.md`.
4. Send completion message to orchestrator (`55167ad6-cbf4-4976-89a6-0974159f54b0`).

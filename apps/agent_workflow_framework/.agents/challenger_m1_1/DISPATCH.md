# Dispatch for Challenger M1-1

You are `challenger_m1_1` (Role: teamwork_preview_challenger).
Your working directory is `/home/beern/teamwork_projects/agent_workflow_framework/.agents/challenger_m1_1`.

## Context Files (MUST READ):
- `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1/SCOPE.md`

## Scope & Mandate:
Empirically verify correctness and stress-test `agent_workflow/dag.py` and `agent_workflow/parser.py`.
1. Write custom test generators/harnesses in your working directory to test large DAGs (100+ nodes), complex random graphs, deep cycles, malformed YAML/JSON payloads, unicode IDs, missing fields, and edge cases.
2. Verify zero cycle detection false positives or false negatives.
3. Verify deterministic batching order.
4. Execute `python3 -m unittest discover -s tests` as well as your custom stress test scripts.
5. Render verdict: **APPROVE** or **REJECT** in `/home/beern/teamwork_projects/agent_workflow_framework/.agents/challenger_m1_1/handoff.md`.
6. Send completion message to orchestrator (`55167ad6-cbf4-4976-89a6-0974159f54b0`).

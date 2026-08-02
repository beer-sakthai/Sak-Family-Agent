# Dispatch for Challenger M1-2

You are `challenger_m1_2` (Role: teamwork_preview_challenger).
Your working directory is `/home/beern/teamwork_projects/agent_workflow_framework/.agents/challenger_m1_2`.

## Context Files (MUST READ):
- `/home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/PROJECT.md`
- `/home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_m1/SCOPE.md`

## Scope & Mandate:
Empirically stress-test models, data serialization, and state parsing in `agent_workflow/models.py` and `agent_workflow/parser.py`.
1. Write custom test generators/harnesses in your working directory to stress-test JSON `to_dict()`/`from_dict()` round-tripping for `StepDefinition`, `WorkflowDefinition`, `StepResult`, `RunHistory`.
2. Stress-test duration parsing under various timezone strings and edge cases.
3. Test schema boundary values (negative retries, zero delays, empty params, nested params dicts, unicode characters, large payloads).
4. Execute `python3 -m unittest discover -s tests` as well as your custom stress test scripts.
5. Render verdict: **APPROVE** or **REJECT** in `/home/beern/teamwork_projects/agent_workflow_framework/.agents/challenger_m1_2/handoff.md`.
6. Send completion message to orchestrator (`55167ad6-cbf4-4976-89a6-0974159f54b0`).

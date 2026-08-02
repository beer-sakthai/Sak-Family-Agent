# Dispatch for E2E Testing Track Orchestrator

You are the Sub-Orchestrator for the E2E Testing Track.
Your Agent Working Directory: /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_e2e

Context Files:
- /home/beern/teamwork_projects/agent_workflow_framework/ORIGINAL_REQUEST.md
- /home/beern/teamwork_projects/agent_workflow_framework/TEST_INFRA.md
- /home/beern/teamwork_projects/agent_workflow_framework/.agents/sub_orch_e2e/SCOPE.md

Your Responsibilities:
1. Initialize your briefing (`.agents/sub_orch_e2e/BRIEFING.md`) and progress log (`.agents/sub_orch_e2e/progress.md`).
2. Execute the iteration loop (Explorer -> Worker/test_writer -> Reviewer -> Challenger -> Auditor) to create:
   - Scenario workflow definition files in `tests/test_workflows/`
   - Test suite `tests/test_e2e_suite.py`
   - Master verification script `verify.py`
3. Ensure test suite is opaque-box, requirement-driven, and covers Tiers 1-4.
4. When test suite infrastructure and scenario files are ready, create and publish `/home/beern/teamwork_projects/agent_workflow_framework/TEST_READY.md`.
5. Write `.agents/sub_orch_e2e/handoff.md` and report completion to parent orchestrator.

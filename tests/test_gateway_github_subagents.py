import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.router import GatewayRouter
from sakthai.team.github_subagents import GitHubCLISubagentFramework


def test_gateway_github_subagents_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_run_gh(self, args: list[str]) -> tuple[int, str]:
        if "pr" in args:
            return 0, '[{"number": 101, "title": "feat: mock PR"}]'
        if "issue" in args:
            return 0, '[{"number": 201, "title": "mock issue"}]'
        if "branches/main" in " ".join(args):
            return 0, '{"name": "main", "protected": true}'
        return 0, "[]"

    monkeypatch.setattr(GitHubCLISubagentFramework, "run_gh", mock_run_gh)

    config = GatewayConfig()
    router = GatewayRouter(config=config)

    # Test maintenance handler
    res_maint = router.handle_github_maintenance({"vacuum": False, "audit": False})
    assert res_maint["workflow_id"] == "gh-dyn-maintenance-v1"
    assert "Shard Maintenance" in res_maint["phases_completed"]
    assert res_maint["auto_merge_blocked"] is True

    # Test string boolean parsing (e.g., query params from HTTP GET ?vacuum=false&audit=true)
    res_maint_str = router.handle_github_maintenance({"vacuum": "false", "audit": "true"})
    shard_detail = next(d for d in res_maint_str["details"] if d.get("phase") == "shards")
    assert shard_detail["vacuumed"] == 0
    assert "Fleet Audit" in res_maint_str["phases_completed"]

    # Test audit handler
    res_audit = router.handle_github_audit()
    assert res_audit["workflow_id"] == "gh-dyn-workflow-v1"
    assert "Audit & Triage" in res_audit["phases_completed"]

    # Test security handler
    res_sec = router.handle_github_security()
    assert res_sec["workflow_id"] == "gh-dyn-security-v1"
    assert "Branch Protection" in res_sec["phases_completed"]
    assert res_sec["auto_merge_blocked"] is True

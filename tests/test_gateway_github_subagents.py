from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.router import GatewayRouter


def test_gateway_github_subagents_handlers() -> None:
    config = GatewayConfig()
    router = GatewayRouter(config=config)

    # Test maintenance handler
    res_maint = router.handle_github_maintenance({"vacuum": False, "audit": False})
    assert res_maint["workflow_id"] == "gh-dyn-maintenance-v1"
    assert "Shard Maintenance" in res_maint["phases_completed"]
    assert res_maint["auto_merge_blocked"] is True

    # Test audit handler
    res_audit = router.handle_github_audit()
    assert res_audit["workflow_id"] == "gh-dyn-workflow-v1"
    assert "Audit & Triage" in res_audit["phases_completed"]

    # Test security handler
    res_sec = router.handle_github_security()
    assert res_sec["workflow_id"] == "gh-dyn-security-v1"
    assert "Branch Protection" in res_sec["phases_completed"]
    assert res_sec["auto_merge_blocked"] is True

"""Unit and integration tests for Gateway Memory Shard Studio endpoints."""

from __future__ import annotations

import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.memory import GatewayMemoryManager
from sakthai.gateway.router import GatewayRouter
from sakthai.gateway.server import RuntimeGatewayServer
from sakthai.memory.store import MemoryStore


def _http_request(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:  # nosec B310
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw), resp_headers
            except json.JSONDecodeError:
                return resp.status, raw, resp_headers
    except urllib.error.HTTPError as err:
        resp_headers = {k.lower(): v for k, v in err.headers.items()}
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw), resp_headers
        except Exception:
            return err.code, raw, resp_headers


@pytest.fixture
def temp_memory_manager() -> tuple[GatewayMemoryManager, dict[str, Path]]:
    temp_dir = tempfile.TemporaryDirectory()
    base_dir = Path(temp_dir.name)
    shard_paths: dict[str, Path] = {}
    for p in ("sakthai", "sakking", "saksee", "sakjules", "saksit", "saktan"):
        p_dir = base_dir / p
        p_dir.mkdir(parents=True, exist_ok=True)
        shard_paths[p] = p_dir / "memory.db"

    def _factory(persona: str) -> MemoryStore:
        path = shard_paths.get(persona.lower(), base_dir / "default.db")
        return MemoryStore(db_path=path)

    mgr = GatewayMemoryManager(store_factory=_factory)
    yield mgr, shard_paths
    temp_dir.cleanup()


def test_get_all_shards_metadata(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> None:
    mgr, _ = temp_memory_manager
    # Populate a fact in sakthai
    mgr.add_fact("sakthai", "SakThai master orchestrator active", kind="status")
    # Populate a fact in sakjules
    mgr.add_fact("sakjules", "CI pipeline configured", kind="fact", tags=["ci", "automation"])

    res = mgr.get_all_shards_metadata()
    assert res["ok"] is True
    assert res["total_shards"] == 6
    assert res["total_facts"] == 2

    # Verify sakthai shard
    sakthai_shard = next(s for s in res["shards"] if s["persona"] == "sakthai")
    assert sakthai_shard["facts_count"] == 1
    assert sakthai_shard["name"] == "SakThai"


def test_list_persona_facts_and_merged(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> None:
    mgr, _ = temp_memory_manager
    mgr.add_fact("sakthai", "Thai Fact 1", kind="fact", tags=["core"])
    mgr.add_fact("sakthai", "Thai Pref", kind="pref", tags=["ui"])
    mgr.add_fact("sakking", "King Fact", kind="fact", tags=["runner"])

    # Specific persona
    thai_res = mgr.list_persona_facts("sakthai")
    assert thai_res["ok"] is True
    assert thai_res["count"] == 2

    # Filter by kind
    pref_res = mgr.list_persona_facts("sakthai", kind="pref")
    assert pref_res["count"] == 1
    assert pref_res["facts"][0]["value"] == "Thai Pref"

    # Filter by tag
    tag_res = mgr.list_persona_facts("sakthai", tag="ui")
    assert tag_res["count"] == 1
    assert tag_res["facts"][0]["value"] == "Thai Pref"

    # Merged across all shards
    merged_res = mgr.list_persona_facts("merged")
    assert merged_res["ok"] is True
    assert merged_res["count"] == 3


def test_add_fact_guardrail_blocking(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> None:
    mgr, _ = temp_memory_manager

    # Safe fact
    safe_res = mgr.add_fact("sakthai", "Safe observation details")
    assert safe_res["ok"] is True
    assert safe_res["status"] == "created"

    # Destructive SQL pattern without token -> blocked
    blocked_sql = mgr.add_fact("sakthai", "DROP TABLE users;")
    assert blocked_sql["ok"] is False
    assert blocked_sql["status"] == "blocked"
    assert "approval_token" in blocked_sql
    token = blocked_sql["approval_token"]

    # Destructive with valid approval token -> allowed
    approved_res = mgr.add_fact("sakthai", "DROP TABLE users;", approval_token=token)
    assert approved_res["ok"] is True
    assert approved_res["status"] == "created"


def test_delete_fact_confirmation(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> None:
    mgr, _ = temp_memory_manager
    add_res = mgr.add_fact("sakthai", "Fact to delete", key="temp_key")
    fact_id = add_res["fact"]["id"]

    # Attempt delete without confirmation
    unconfirmed = mgr.delete_fact("sakthai", fact_id, confirmed=False)
    assert unconfirmed["ok"] is False
    assert unconfirmed["status"] == "confirmation_required"

    # Attempt delete nonexistent fact
    not_found = mgr.delete_fact("sakthai", 9999, confirmed=True)
    assert not_found["ok"] is False
    assert not_found["status"] == "not_found"

    # Delete with confirmation
    confirmed = mgr.delete_fact("sakthai", fact_id, confirmed=True)
    assert confirmed["ok"] is True
    assert confirmed["status"] == "deleted"


def test_preview_memory_context(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> None:
    mgr, _ = temp_memory_manager
    mgr.add_fact("saksee", "SakSee browser test setup", key="browser_test")

    preview = mgr.preview_memory_context("saksee", query="browser")
    assert preview["ok"] is True
    assert preview["persona"] == "saksee"
    assert "Persistent Memory Context" in preview["prompt_context"]
    assert preview["facts_count"] >= 1


@pytest.fixture
def memory_server(
    temp_memory_manager: tuple[GatewayMemoryManager, dict[str, Path]],
) -> RuntimeGatewayServer:
    mgr, _ = temp_memory_manager
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token="memory-secret-token")
    router = GatewayRouter(config=cfg, memory_manager=mgr)
    server = RuntimeGatewayServer(config=cfg, router=router)
    server.start(background=True)
    yield server
    server.shutdown()


def test_server_memory_endpoints(memory_server: RuntimeGatewayServer) -> None:
    port = memory_server.port
    headers = {"Authorization": "Bearer memory-secret-token"}

    # 1. GET /v1/memory/shards
    shards_url = f"http://127.0.0.1:{port}/v1/memory/shards"
    status, data, _ = _http_request(shards_url, method="GET", headers=headers)
    assert status == 200
    assert data["ok"] is True
    assert data["total_shards"] == 6

    # 2. POST /v1/memory/facts (create)
    add_url = f"http://127.0.0.1:{port}/v1/memory/facts"
    body = {
        "persona": "sakjules",
        "value": "Deployed staging cluster v2",
        "kind": "fact",
        "key": "staging_v2",
        "tags": ["deploy", "k8s"],
    }
    status, add_data, _ = _http_request(add_url, method="POST", body=body, headers=headers)
    assert status == 200
    assert add_data["ok"] is True
    created_id = add_data["fact"]["id"]

    # 3. GET /v1/memory/facts
    list_url = f"http://127.0.0.1:{port}/v1/memory/facts?persona=sakjules"
    status, list_data, _ = _http_request(list_url, method="GET", headers=headers)
    assert status == 200
    assert list_data["count"] == 1
    assert list_data["facts"][0]["key"] == "staging_v2"

    # 4. POST /v1/memory/preview
    prev_url = f"http://127.0.0.1:{port}/v1/memory/preview"
    prev_body = {"persona": "sakjules", "query": "staging"}
    status, prev_data, _ = _http_request(prev_url, method="POST", body=prev_body, headers=headers)
    assert status == 200
    assert prev_data["ok"] is True
    assert "staging" in prev_data["prompt_context"].lower()

    # 5. DELETE /v1/memory/facts/{id}
    del_url = (
        f"http://127.0.0.1:{port}/v1/memory/facts/{created_id}?persona=sakjules&confirmed=true"
    )
    status, del_data, _ = _http_request(del_url, method="DELETE", headers=headers)
    assert status == 200
    assert del_data["ok"] is True
    assert del_data["status"] == "deleted"

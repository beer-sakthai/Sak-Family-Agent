"""Tests for Hugging Face Hub Webhook ingestion, security verification, and handlers."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.router import GatewayRouter
from sakthai.gateway.server import RuntimeGatewayServer
from sakthai.gateway.webhooks import (
    WebhookPayload,
    WebhookPayloadComment,
    WebhookPayloadDiscussion,
    WebhookPayloadEvent,
    WebhookPayloadRepo,
    WebhookPayloadUpdatedFile,
    dispatch_webhook_event,
    handle_auto_retrain,
    handle_bucket_job,
    handle_discussion_bot,
    handle_metadata_review,
    process_webhook_request,
    verify_webhook_secret,
)


def _make_payload(
    action: str = "update",
    scope: str = "repo.content",
    repo_name: str = "beer-sakthai/test-dataset",
    repo_type: str = "dataset",
    head_sha: str = "abc1234567890",
    discussion_num: int | None = None,
    comment_content: str | None = None,
    comment_author_id: str | None = "user-123",
    updated_files: list[dict[str, Any]] | None = None,
) -> WebhookPayload:
    disc = (
        WebhookPayloadDiscussion(num=discussion_num, title="Test PR", isPullRequest=True)
        if discussion_num is not None
        else None
    )
    comment = (
        WebhookPayloadComment(
            id="comm-1",
            content=comment_content,
            author={"id": comment_author_id} if comment_author_id else None,
        )
        if comment_content is not None
        else None
    )
    files = (
        [WebhookPayloadUpdatedFile(**f) for f in updated_files]
        if updated_files is not None
        else None
    )

    return WebhookPayload(
        event=WebhookPayloadEvent(action=action, scope=scope),
        repo=WebhookPayloadRepo(
            type=repo_type,
            name=repo_name,
            headSha=head_sha,
        ),
        discussion=disc,
        comment=comment,
        updatedFiles=files,
    )


# ---------------------------------------------------------------------------
# 1. Secret Verification
# ---------------------------------------------------------------------------


def test_verify_webhook_secret() -> None:
    expected = "super-secret-token-123"
    assert verify_webhook_secret(expected, expected) is True
    assert verify_webhook_secret("wrong-token", expected) is False
    assert verify_webhook_secret(None, expected) is False
    assert verify_webhook_secret(expected, None) is False
    assert verify_webhook_secret("", expected) is False
    assert verify_webhook_secret(expected, "") is False


# ---------------------------------------------------------------------------
# 2. Auto-Retrain Handler
# ---------------------------------------------------------------------------


def test_auto_retrain_valid_dataset_update() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/speech-commands",
        repo_type="dataset",
        head_sha="commit-999",
    )
    result = handle_auto_retrain(payload, target_dataset="beer-sakthai/speech-commands")
    assert result["processed"] is True
    assert result["action"] == "training_scheduled"
    assert result["head_sha"] == "commit-999"
    assert result["status"] == "queued"


def test_auto_retrain_ignores_non_dataset() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/speech-model",
        repo_type="model",
    )
    result = handle_auto_retrain(payload)
    assert result["processed"] is False
    assert "not a dataset content update" in result["reason"]


def test_auto_retrain_ignores_mismatched_target() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="other-user/dataset",
        repo_type="dataset",
    )
    result = handle_auto_retrain(payload, target_dataset="beer-sakthai/speech-commands")
    assert result["processed"] is False
    assert "does not match target" in result["reason"]


# ---------------------------------------------------------------------------
# 3. Discussion Bot Handler
# ---------------------------------------------------------------------------


def test_discussion_bot_mentions() -> None:
    payload = _make_payload(
        action="create",
        scope="discussion.comment",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
        discussion_num=42,
        comment_content="Hey @sakthai_agent_bot can you review this model card?",
        comment_author_id="community-user",
    )
    result = handle_discussion_bot(payload, bot_username="@sakthai_agent_bot")
    assert result["processed"] is True
    assert result["action"] == "comment_queued"
    assert result["discussion_num"] == 42
    assert "House of Sak" in result["reply"]


def test_discussion_bot_loop_prevention() -> None:
    payload = _make_payload(
        action="create",
        scope="discussion.comment",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
        discussion_num=42,
        comment_content="Automated reply from @sakthai_agent_bot",
        comment_author_id="bot-user-id",
    )
    result = handle_discussion_bot(
        payload,
        bot_username="@sakthai_agent_bot",
        bot_author_id="bot-user-id",
    )
    assert result["processed"] is False
    assert "Self-authored comment ignored" in result["reason"]


def test_discussion_bot_ignores_unmentioned_comment() -> None:
    payload = _make_payload(
        action="create",
        scope="discussion.comment",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
        discussion_num=42,
        comment_content="Just discussing between humans.",
        comment_author_id="human-user",
    )
    result = handle_discussion_bot(payload, bot_username="@sakthai_agent_bot")
    assert result["processed"] is False
    assert "not mentioned" in result["reason"]


def test_discussion_bot_scope_or_action_check() -> None:
    payload = _make_payload(
        action="delete",
        scope="discussion.comment",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
    )
    result = handle_discussion_bot(payload)
    assert result["processed"] is False

    payload_wrong_scope = _make_payload(
        action="create",
        scope="repo",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
    )
    result_wrong = handle_discussion_bot(payload_wrong_scope)
    assert result_wrong["processed"] is False


# ---------------------------------------------------------------------------
# 4. Metadata Review Handler
# ---------------------------------------------------------------------------


def test_metadata_review_approved() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/good-model",
        repo_type="model",
    )
    card_data = {
        "license": "mit",
        "language": "th",
        "tags": ["nlp", "thai"],
        "description": "High quality model card",
    }
    result = handle_metadata_review(payload, repo_card_data=card_data)
    assert result["processed"] is True
    assert result["status"] == "approved"
    assert "Approved" in result["report"]


def test_metadata_review_changes_requested() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/empty-card-model",
        repo_type="model",
    )
    card_data: dict[str, Any] = {}
    result = handle_metadata_review(payload, repo_card_data=card_data)
    assert result["processed"] is True
    assert result["status"] == "changes_requested"
    assert "Action Required" in result["report"]


def test_metadata_review_warning() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/partial-card-model",
        repo_type="model",
    )
    card_data = {
        "license": "apache-2.0",
        "language": "en",
    }
    result = handle_metadata_review(payload, repo_card_data=card_data)
    assert result["processed"] is True
    assert result["status"] == "warning"


def test_metadata_review_ignores_other_types() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/test-space",
        repo_type="space",
    )
    result = handle_metadata_review(payload)
    assert result["processed"] is False


# ---------------------------------------------------------------------------
# 5. Bucket Jobs Handler
# ---------------------------------------------------------------------------


def test_bucket_job_dispatched() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/raw-data-bucket",
        repo_type="bucket",
        updated_files=[
            {"path": "data/sample.csv", "action": "add", "size": 1024},
            {"path": "logs/export.json", "action": "add", "size": 2048},
            {"path": "README.md", "action": "add", "size": 100},
        ],
    )
    result = handle_bucket_job(payload)
    assert result["processed"] is True
    assert result["action"] == "batch_job_dispatched"
    assert result["total_files"] == 3
    assert result["transformable_count"] == 2
    assert result["status"] == "dispatched"


def test_bucket_job_no_op_when_not_bucket() -> None:
    payload = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/my-model",
        repo_type="model",
    )
    result = handle_bucket_job(payload)
    assert result["processed"] is False


# ---------------------------------------------------------------------------
# 6. Master Dispatcher & Request Processor
# ---------------------------------------------------------------------------


def test_process_webhook_request_unauthorized() -> None:
    code, res = process_webhook_request(
        headers={},
        body={},
        expected_secret="expected-secret",
    )
    assert code == 401
    assert res["ok"] is False


def test_process_webhook_request_malformed_body() -> None:
    code, res = process_webhook_request(
        headers={"x-webhook-secret": "test-sec"},
        body={"invalid": "payload"},
        expected_secret="test-sec",
    )
    assert code == 400
    assert "Invalid webhook payload" in res["error"]


def test_process_webhook_request_success() -> None:
    payload_dict = {
        "event": {"action": "update", "scope": "repo.content"},
        "repo": {"type": "dataset", "name": "beer-sakthai/voice-data", "headSha": "sha123"},
    }
    code, res = process_webhook_request(
        headers={"X-Webhook-Secret": "test-sec"},
        body=payload_dict,
        expected_secret="test-sec",
    )
    assert code == 200
    assert res["ok"] is True
    assert res["summary"]["processed"] is True
    assert "auto_retrain" in res["summary"]["handlers"]


def test_dispatch_webhook_event() -> None:
    # 1. Bucket dispatch
    payload_bucket = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/bucket-data",
        repo_type="bucket",
        updated_files=[{"path": "file.csv", "action": "add"}],
    )
    res_b = dispatch_webhook_event(payload_bucket)
    assert res_b["processed"] is True
    assert "bucket_jobs" in res_b["handlers"]

    # 2. Discussion dispatch
    payload_disc = _make_payload(
        action="create",
        scope="discussion",
        repo_name="beer-sakthai/model-data",
        repo_type="model",
        discussion_num=10,
    )
    res_d = dispatch_webhook_event(payload_disc)
    assert res_d["processed"] is True
    assert "discussion_bot" in res_d["handlers"]

    # 3. Model repo metadata review dispatch
    payload_model = _make_payload(
        action="update",
        scope="repo.content",
        repo_name="beer-sakthai/model-data",
        repo_type="model",
    )
    res_m = dispatch_webhook_event(
        payload_model, repo_card_data={"license": "mit", "language": "en"}
    )
    assert res_m["processed"] is True
    assert "metadata_review" in res_m["handlers"]


# ---------------------------------------------------------------------------
# 7. Gateway Server & Router Integration
# ---------------------------------------------------------------------------


def test_gateway_server_hf_webhook_endpoint() -> None:
    cfg = GatewayConfig(
        host="127.0.0.1",
        port=0,
        bearer_token="bearer-token-123",
        hf_webhook_secret="hf-secret-xyz",
    )
    router = GatewayRouter(config=cfg)
    server = RuntimeGatewayServer(config=cfg, router=router)
    server.start(background=True)
    actual_port = server.port
    base_url = f"http://127.0.0.1:{actual_port}"

    try:
        # 1. Missing secret -> 401
        req = Request(
            f"{base_url}/v1/webhooks/huggingface",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 401

        # 2. Valid secret and payload -> 200
        payload_data = json.dumps(
            {
                "event": {"action": "update", "scope": "repo.content"},
                "repo": {
                    "type": "dataset",
                    "name": "beer-sakthai/dataset-test",
                    "headSha": "abc111",
                },
            }
        ).encode("utf-8")
        req_valid = Request(
            f"{base_url}/v1/webhooks/huggingface",
            data=payload_data,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Secret": "hf-secret-xyz",
            },
            method="POST",
        )
        with urlopen(req_valid, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert data["summary"]["processed"] is True

        # 3. Test alias endpoint /webhooks/huggingface -> 200
        req_alias = Request(
            f"{base_url}/webhooks/huggingface",
            data=payload_data,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Secret": "hf-secret-xyz",
            },
            method="POST",
        )
        with urlopen(req_alias, timeout=5) as resp:
            assert resp.status == 200

    finally:
        server.shutdown()

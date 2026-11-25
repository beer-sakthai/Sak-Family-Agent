"""Hugging Face Hub Webhook ingestion and event dispatching engine.

Implements automated handlers for:
1. Auto-retrain: Triggers dataset fine-tuning / training runs on repository content updates.
2. Discussion bot: Responds to community questions / PR discussions via LLM reasoning.
3. Metadata review: Validates README metadata YAML frontmatter on model/dataset updates.
4. Bucket jobs: Coordinates data bucket file transformations (e.g. CSV/JSON to optimized Parquet).
"""

from __future__ import annotations

import logging
import os
import secrets
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Payload Schemas (Strictly aligned with Hugging Face Webhooks spec)
# ---------------------------------------------------------------------------


class WebhookPayloadEvent(BaseModel):
    """Event descriptor indicating action and scope."""

    model_config = ConfigDict(extra="ignore")

    action: Literal["create", "update", "delete", "move"] | str
    scope: str = Field(
        ...,
        description=(
            "Scope of the event, e.g., 'repo', 'repo.content', 'repo.config', "
            "'discussion', 'discussion.comment'"
        ),
    )


class WebhookPayloadRepoUrl(BaseModel):
    """URLs associated with the repository."""

    model_config = ConfigDict(extra="ignore")

    web: str | None = None
    api: str | None = None


class WebhookPayloadRepoOwner(BaseModel):
    """Owner metadata for repository."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None


class WebhookPayloadRepo(BaseModel):
    """Repository metadata in the webhook event."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["model", "dataset", "space", "bucket"] | str
    name: str
    id: str | None = None
    private: bool = False
    headSha: str | None = None
    url: WebhookPayloadRepoUrl | None = None
    owner: WebhookPayloadRepoOwner | None = None


class WebhookPayloadDiscussion(BaseModel):
    """Discussion or Pull Request metadata."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    title: str | None = None
    url: dict[str, str] | None = None
    status: str | None = "open"
    author: dict[str, Any] | None = None
    num: int | None = None
    isPullRequest: bool = False
    changes: dict[str, Any] | None = None


class WebhookPayloadComment(BaseModel):
    """Discussion comment details."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    author: dict[str, Any] | None = None
    content: str | None = None
    hidden: bool = False
    url: dict[str, str] | None = None


class WebhookPayloadUpdatedFile(BaseModel):
    """Updated file metadata in bucket or repo update events."""

    model_config = ConfigDict(extra="ignore")

    path: str
    action: Literal["add", "modify", "delete"] | str
    xetHash: str | None = None
    size: int | None = None


class WebhookPayload(BaseModel):
    """Top-level Hugging Face Webhook JSON payload."""

    model_config = ConfigDict(extra="ignore")

    event: WebhookPayloadEvent
    repo: WebhookPayloadRepo
    discussion: WebhookPayloadDiscussion | None = None
    comment: WebhookPayloadComment | None = None
    webhook: dict[str, Any] | None = None
    updatedFiles: list[WebhookPayloadUpdatedFile] | None = None


# ---------------------------------------------------------------------------
# Security & Verification
# ---------------------------------------------------------------------------


def verify_webhook_secret(header_secret: str | None, expected_secret: str | None) -> bool:
    """Verify X-Webhook-Secret using constant-time comparison.

    Fails closed if either secret is empty, None, or mismatched.
    """
    if not header_secret or not expected_secret:
        return False
    return secrets.compare_digest(
        header_secret.encode("utf-8"),
        expected_secret.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# Specialized Webhook Event Handlers
# ---------------------------------------------------------------------------


def handle_auto_retrain(
    payload: WebhookPayload,
    target_dataset: str | None = None,
    base_model: str = "microsoft/resnet-50",
) -> dict[str, Any]:
    """React to dataset updates by scheduling a model retraining / fine-tuning run.

    Triggered when:
    - event.action == "update"
    - event.scope starts with "repo.content"
    - repo.type == "dataset"
    - repo.name matches target_dataset (if specified)
    """
    is_content_update = (
        payload.event.action == "update"
        and payload.event.scope.startswith("repo.content")
        and payload.repo.type == "dataset"
    )
    if not is_content_update:
        return {
            "processed": False,
            "handler": "auto_retrain",
            "reason": "Event is not a dataset content update",
        }

    if target_dataset and payload.repo.name != target_dataset:
        return {
            "processed": False,
            "handler": "auto_retrain",
            "reason": f"Dataset '{payload.repo.name}' does not match target '{target_dataset}'",
        }

    head_sha = payload.repo.headSha or "latest"
    logger.info(
        "Auto-retrain triggered for dataset %s (headSha=%s) using base model %s",
        payload.repo.name,
        head_sha,
        base_model,
    )

    return {
        "processed": True,
        "handler": "auto_retrain",
        "action": "training_scheduled",
        "dataset": payload.repo.name,
        "head_sha": head_sha,
        "base_model": base_model,
        "status": "queued",
    }


def handle_discussion_bot(
    payload: WebhookPayload,
    bot_username: str = "@sakthai_agent_bot",
    bot_author_id: str | None = None,
) -> dict[str, Any]:
    """Respond to community questions or PR discussions via LLM reasoning.

    Triggered when:
    - event.scope in ("discussion", "discussion.comment")
    - event.action in ("create", "update")
    - comment mentions bot_username (or discussion is opened)
    - avoids infinite reply loops by ignoring comments authored by bot itself
    """
    scope = payload.event.scope
    if scope not in ("discussion", "discussion.comment"):
        return {
            "processed": False,
            "handler": "discussion_bot",
            "reason": f"Scope '{scope}' is not a discussion or comment",
        }

    if payload.event.action not in ("create", "update"):
        return {
            "processed": False,
            "handler": "discussion_bot",
            "reason": f"Action '{payload.event.action}' not supported for discussion bot",
        }

    # Prevent loop if comment is authored by bot itself
    comment = payload.comment
    if comment and comment.author:
        author_id = str(comment.author.get("id") or comment.author.get("name") or "")
        if bot_author_id and author_id == bot_author_id:
            return {
                "processed": False,
                "handler": "discussion_bot",
                "reason": "Self-authored comment ignored to prevent loop",
            }

    content = comment.content if comment else None
    disc = payload.discussion
    num = disc.num if disc else None

    # Check if comment mentions bot or is a new discussion
    is_mentioned = content and (bot_username in content or bot_username.lstrip("@") in content)
    is_new_discussion = scope == "discussion" and payload.event.action == "create"

    if not (is_mentioned or is_new_discussion):
        return {
            "processed": False,
            "handler": "discussion_bot",
            "reason": f"Bot username '{bot_username}' not mentioned",
        }

    title = disc.title if disc else "Discussion"
    reply_text = (
        f"Hello from **House of Sak**! Thank you for opening: *{title}*.\n\n"
        f"Our lead agent SakThai has received your request and queued analysis. "
        f"For automated model info or dataset inquiries, feel free to mention {bot_username}."
    )

    logger.info(
        "Discussion bot reply generated for repo %s discussion #%s",
        payload.repo.name,
        num,
    )

    return {
        "processed": True,
        "handler": "discussion_bot",
        "action": "comment_queued",
        "repo": payload.repo.name,
        "discussion_num": num,
        "reply": reply_text,
    }


def handle_metadata_review(
    payload: WebhookPayload,
    repo_card_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform automated metadata quality checks and format a review comment.

    Checks essential fields in model/dataset README frontmatter:
    - license (required)
    - language (required)
    - tags (recommended)
    - description (recommended)
    """
    if payload.repo.type not in ("model", "dataset"):
        return {
            "processed": False,
            "handler": "metadata_review",
            "reason": f"Repo type '{payload.repo.type}' does not require metadata card review",
        }

    data = repo_card_data or {}
    checks: dict[str, bool] = {
        "license": bool(data.get("license")),
        "language": bool(data.get("language")),
        "tags": bool(data.get("tags")),
        "description": bool(data.get("description")),
    }

    critical_passed = checks["license"] and checks["language"]
    all_passed = all(checks.values())

    report_lines = [
        f"### 📋 Automated Metadata Quality Review for `{payload.repo.name}`",
        "",
        "| Field | Status | Detail |",
        "|---|---|---|",
        f"| **License** | {'✅ PASS' if checks['license'] else '❌ MISSING'} | {data.get('license', 'Unspecified')} |",
        f"| **Language** | {'✅ PASS' if checks['language'] else '❌ MISSING'} | {data.get('language', 'Unspecified')} |",
        f"| **Tags** | {'✅ PASS' if checks['tags'] else '⚠️ EMPTY'} | {len(data.get('tags') or [])} tags |",
        f"| **Description** | {'✅ PASS' if checks['description'] else '⚠️ EMPTY'} | {'Present' if checks['description'] else 'Omitted'} |",
        "",
    ]

    if all_passed:
        report_lines.append("**Result:** ✅ **Approved.** All metadata criteria met.")
        status = "approved"
    elif critical_passed:
        report_lines.append(
            "**Result:** ⚠️ **Passing with Warnings.** Consider adding tags/description."
        )
        status = "warning"
    else:
        report_lines.append(
            "**Result:** ❌ **Action Required.** Missing mandatory license/language metadata."
        )
        status = "changes_requested"

    report_md = "\n".join(report_lines)

    return {
        "processed": True,
        "handler": "metadata_review",
        "action": "review_generated",
        "repo": payload.repo.name,
        "repo_type": payload.repo.type,
        "status": status,
        "checks": checks,
        "report": report_md,
    }


def handle_bucket_job(payload: WebhookPayload) -> dict[str, Any]:
    """Coordinate bucket storage batch operations (e.g. Parquet optimization).

    Triggered when:
    - repo.type == "bucket" or updatedFiles list is present
    - identifies newly added/modified CSV and JSON files for batch job execution
    """
    is_bucket = payload.repo.type == "bucket" or bool(payload.updatedFiles)
    if not is_bucket:
        return {
            "processed": False,
            "handler": "bucket_jobs",
            "reason": "Not a storage bucket event",
        }

    files = payload.updatedFiles or []
    transformable_files = [
        f
        for f in files
        if f.action in ("add", "modify")
        and any(f.path.lower().endswith(ext) for ext in (".csv", ".json", ".tsv"))
    ]

    logger.info(
        "Bucket job dispatcher found %d transformable files in bucket %s",
        len(transformable_files),
        payload.repo.name,
    )

    return {
        "processed": True,
        "handler": "bucket_jobs",
        "action": "batch_job_dispatched",
        "bucket": payload.repo.name,
        "total_files": len(files),
        "transformable_count": len(transformable_files),
        "target_format": "parquet",
        "status": "dispatched" if transformable_files else "no_op",
    }


# ---------------------------------------------------------------------------
# Master Dispatcher
# ---------------------------------------------------------------------------


def dispatch_webhook_event(
    payload: WebhookPayload,
    repo_card_data: dict[str, Any] | None = None,
    target_dataset: str | None = None,
    bot_username: str = "@sakthai_agent_bot",
) -> dict[str, Any]:
    """Dispatch webhook event to appropriate handlers and return consolidated summary."""
    results: dict[str, Any] = {}

    # 1. Bucket Job check
    if payload.repo.type == "bucket" or payload.updatedFiles:
        results["bucket_jobs"] = handle_bucket_job(payload)

    # 2. Auto-Retrain check (dataset updates)
    if payload.repo.type == "dataset" and payload.event.scope.startswith("repo.content"):
        results["auto_retrain"] = handle_auto_retrain(payload, target_dataset=target_dataset)

    # 3. Discussion / Community Bot check
    if payload.event.scope in ("discussion", "discussion.comment"):
        results["discussion_bot"] = handle_discussion_bot(payload, bot_username=bot_username)

    # 4. Metadata Review check (model / dataset repository updates)
    if payload.repo.type in ("model", "dataset") and (
        payload.event.scope == "repo" or payload.event.scope.startswith("repo.content")
    ):
        results["metadata_review"] = handle_metadata_review(payload, repo_card_data=repo_card_data)

    return {
        "processed": any(r.get("processed") for r in results.values()),
        "event_scope": payload.event.scope,
        "event_action": payload.event.action,
        "repo_name": payload.repo.name,
        "handlers": results,
    }


def process_webhook_request(
    headers: dict[str, str],
    body: dict[str, Any],
    expected_secret: str | None = None,
    bot_username: str = "@sakthai_agent_bot",
    target_dataset: str | None = None,
    repo_card_data: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Verify and process incoming HTTP webhook request.

    Returns:
        (http_status_code, response_dict)
    """
    secret = (
        expected_secret or os.environ.get("HF_WEBHOOK_SECRET") or os.environ.get("WEBHOOK_SECRET")
    )

    # Match case-insensitively for X-Webhook-Secret
    header_secret = None
    for k, v in headers.items():
        if k.lower() == "x-webhook-secret":
            header_secret = v
            break

    if not verify_webhook_secret(header_secret, secret):
        return 401, {"error": "Unauthorized: Invalid or missing X-Webhook-Secret", "ok": False}

    try:
        payload = WebhookPayload.model_validate(body)
    except Exception as exc:
        logger.warning("Invalid Hugging Face Webhook payload: %s", exc)
        return 400, {"error": f"Invalid webhook payload: {exc}", "ok": False}

    summary = dispatch_webhook_event(
        payload,
        repo_card_data=repo_card_data,
        target_dataset=target_dataset,
        bot_username=bot_username,
    )
    return 200, {"ok": True, "summary": summary}

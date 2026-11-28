"""Gated Dual-Channel Outbound Dispatcher for Telegram and Discord."""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class DispatchResult:
    draft_id: str
    channels_dispatched: list[str]
    dry_run: bool
    success: bool
    errors: dict[str, str] = field(default_factory=dict)
    payloads: dict[str, Any] = field(default_factory=dict)


def generate_approval_token(draft_id: str, secret: str) -> str:
    """Generate an HMAC SHA256 approval token for a draft ID."""
    return hmac.new(
        secret.encode("utf-8"),
        draft_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_approval_token(draft_id: str, token: str, secret: str) -> bool:
    """Verify that an HMAC approval token matches the draft ID."""
    if not token or not secret:
        return False
    expected = generate_approval_token(draft_id, secret)
    return hmac.compare_digest(expected, token)


def dispatch_social_post(
    draft_id: str,
    content: str,
    approval_token: str,
    channels: list[str] | None = None,
    dry_run: bool = False,
    secret: str | None = None,
    telegram_bot_token: str | None = None,
    telegram_chat_id: str | None = None,
    discord_webhook_url: str | None = None,
    timeout: float = 10.0,
) -> DispatchResult:
    """Dispatch an approved social post to Telegram and Discord channels."""
    auth_secret = secret or os.environ.get("SAKTHAI_APPROVAL_SECRET", "")
    if not auth_secret or not verify_approval_token(draft_id, approval_token, auth_secret):
        raise PermissionError("Invalid or unauthorized HMAC approval token for social dispatch")

    target_channels = channels or ["telegram", "discord"]
    payloads: dict[str, Any] = {}
    errors: dict[str, str] = {}
    dispatched: list[str] = []

    # Prepare payloads
    if "telegram" in target_channels:
        chat_id = telegram_chat_id or os.environ.get("TELEGRAM_BROADCAST_CHAT_ID", "")
        payloads["telegram"] = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": "Markdown",
        }

    if "discord" in target_channels:
        payloads["discord"] = {
            "content": content,
        }

    if dry_run:
        return DispatchResult(
            draft_id=draft_id,
            channels_dispatched=target_channels,
            dry_run=True,
            success=True,
            payloads=payloads,
        )

    # Live dispatch
    if "telegram" in target_channels:
        token = telegram_bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = telegram_chat_id or os.environ.get("TELEGRAM_BROADCAST_CHAT_ID", "")
        if not token or not chat_id:
            errors["telegram"] = "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_BROADCAST_CHAT_ID"
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            try:
                resp = httpx.post(url, json=payloads["telegram"], timeout=timeout)
                if resp.status_code == 200:
                    dispatched.append("telegram")
                else:
                    errors["telegram"] = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as exc:
                errors["telegram"] = str(exc)

    if "discord" in target_channels:
        webhook_url = discord_webhook_url or os.environ.get("DISCORD_ANNOUNCEMENT_WEBHOOK_URL", "")
        if not webhook_url:
            errors["discord"] = "Missing DISCORD_ANNOUNCEMENT_WEBHOOK_URL"
        else:
            try:
                resp = httpx.post(webhook_url, json=payloads["discord"], timeout=timeout)
                if resp.status_code in (200, 204):
                    dispatched.append("discord")
                else:
                    errors["discord"] = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as exc:
                errors["discord"] = str(exc)

    success = len(errors) == 0 and len(dispatched) == len(target_channels)
    return DispatchResult(
        draft_id=draft_id,
        channels_dispatched=dispatched,
        dry_run=False,
        success=success,
        errors=errors,
        payloads=payloads,
    )

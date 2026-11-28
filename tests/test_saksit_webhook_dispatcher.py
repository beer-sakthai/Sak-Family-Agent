"""Tests for SakSit Gated Dual-Channel Webhook Dispatcher."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sakthai.telegram.dispatcher import (
    DispatchResult,
    dispatch_social_post,
    generate_approval_token,
    verify_approval_token,
)


class TestWebhookDispatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "test-secret-key-12345"
        self.draft_id = "draft_20261127_decision1"
        self.valid_token = generate_approval_token(self.draft_id, self.secret)

    def test_token_generation_and_verification(self) -> None:
        self.assertTrue(verify_approval_token(self.draft_id, self.valid_token, self.secret))
        self.assertFalse(verify_approval_token(self.draft_id, "invalid_token", self.secret))
        self.assertFalse(verify_approval_token("other_draft", self.valid_token, self.secret))

    def test_dispatch_unauthorized_token_raises_permission_error(self) -> None:
        with self.assertRaises(PermissionError):
            dispatch_social_post(
                draft_id=self.draft_id,
                content="Test post content",
                approval_token="tampered_token",
                secret=self.secret,
            )

    def test_dispatch_dry_run_constructs_payloads_without_network(self) -> None:
        content = "🚀 **SakThai Decision 1** launched! Local 100% free."
        result: DispatchResult = dispatch_social_post(
            draft_id=self.draft_id,
            content=content,
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["telegram", "discord"],
            dry_run=True,
            telegram_chat_id="-1001234567890",
            discord_webhook_url="https://discord.com/api/webhooks/123/abc",
        )

        self.assertTrue(result.dry_run)
        self.assertTrue(result.success)
        self.assertEqual(result.channels_dispatched, ["telegram", "discord"])
        self.assertIn("telegram", result.payloads)
        self.assertIn("discord", result.payloads)
        self.assertEqual(result.payloads["telegram"]["chat_id"], "-1001234567890")
        self.assertEqual(result.payloads["discord"]["content"], content)

    @patch("httpx.post")
    def test_dispatch_live_channels_success(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        result = dispatch_social_post(
            draft_id=self.draft_id,
            content="Live post content",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["telegram", "discord"],
            dry_run=False,
            telegram_bot_token="bot12345:TOKEN",
            telegram_chat_id="-10099999",
            discord_webhook_url="https://discord.com/api/webhooks/mock",
        )

        self.assertFalse(result.dry_run)
        self.assertTrue(result.success)
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(result.errors, {})

    @patch("httpx.post")
    def test_dispatch_missing_credentials_or_network_error(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("Network timeout")

        result = dispatch_social_post(
            draft_id=self.draft_id,
            content="Live post",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["telegram", "discord"],
            dry_run=False,
            telegram_bot_token=None,  # Missing telegram token
            discord_webhook_url="https://discord.com/api/webhooks/mock",
        )

        self.assertFalse(result.success)
        self.assertIn("telegram", result.errors)
        self.assertIn("discord", result.errors)

    def test_verify_approval_token_empty_token_or_secret(self) -> None:
        self.assertFalse(verify_approval_token(self.draft_id, "", self.secret))
        self.assertFalse(verify_approval_token(self.draft_id, self.valid_token, ""))

    @patch("httpx.post")
    def test_dispatch_single_channel_telegram(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        mock_post.return_value = mock_resp

        result = dispatch_social_post(
            draft_id=self.draft_id,
            content="Telegram post",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["telegram"],
            dry_run=False,
            telegram_bot_token="test:token",
            telegram_chat_id="-12345",
        )
        self.assertFalse(result.success)
        self.assertIn("HTTP 400", result.errors["telegram"])
        self.assertNotIn("discord", result.payloads)

    @patch("httpx.post")
    def test_dispatch_single_channel_discord(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_post.return_value = mock_resp

        # First test missing webhook url
        res_missing = dispatch_social_post(
            draft_id=self.draft_id,
            content="Discord post",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["discord"],
            dry_run=False,
            discord_webhook_url=None,
        )
        self.assertFalse(res_missing.success)
        self.assertIn("Missing DISCORD_ANNOUNCEMENT_WEBHOOK_URL", res_missing.errors["discord"])

        # Then test HTTP error
        res_err = dispatch_social_post(
            draft_id=self.draft_id,
            content="Discord post",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["discord"],
            dry_run=False,
            discord_webhook_url="https://discord.com/api/webhooks/bad",
        )
        self.assertFalse(res_err.success)
        self.assertIn("HTTP 404", res_err.errors["discord"])
        self.assertNotIn("telegram", res_err.payloads)

    @patch.dict(
        "os.environ",
        {
            "SAKTHAI_APPROVAL_SECRET": "env-secret",
            "TELEGRAM_BROADCAST_CHAT_ID": "-100777",
            "TELEGRAM_BOT_TOKEN": "bot:env-token",
            "DISCORD_ANNOUNCEMENT_WEBHOOK_URL": "https://discord.com/api/webhooks/env",
        },
    )
    @patch("httpx.post")
    def test_dispatch_using_environment_variables(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        env_token = generate_approval_token("env_draft", "env-secret")
        result = dispatch_social_post(
            draft_id="env_draft",
            content="Env post",
            approval_token=env_token,
            dry_run=False,
        )
        self.assertTrue(result.success)
        self.assertEqual(len(result.channels_dispatched), 2)

    @patch("httpx.post")
    def test_dispatch_telegram_network_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("Telegram connection reset")
        result = dispatch_social_post(
            draft_id=self.draft_id,
            content="Test post",
            approval_token=self.valid_token,
            secret=self.secret,
            channels=["telegram"],
            dry_run=False,
            telegram_bot_token="test-bot",
            telegram_chat_id="-12345",
        )
        self.assertFalse(result.success)
        self.assertIn("Telegram connection reset", result.errors["telegram"])


if __name__ == "__main__":
    unittest.main()

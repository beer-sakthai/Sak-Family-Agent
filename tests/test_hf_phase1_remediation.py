"""Test suite for Hugging Face Space remediation and webhook event dispatcher."""

import json
import unittest
from unittest.mock import MagicMock, patch

from sakthai.hub.models import SpaceState
from sakthai.hub.remediator import SpaceRemediator
from sakthai.hub.webhook import HubWebhookDispatcher


class TestSpaceRemediator(unittest.TestCase):
    def setUp(self):
        self.remediator = SpaceRemediator(author="Nanthasit")

    @patch("sakthai.hub.remediator.urllib.request.urlopen")
    def test_diagnose_running_space(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "runtime": {
                    "stage": "RUNNING",
                    "hardware": {"current": "cpu-basic"},
                    "gcTimeout": 1800,
                }
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        diag = self.remediator.diagnose_space("Nanthasit/sakthai-chat")
        self.assertEqual(diag["state"], SpaceState.RUNNING.value)
        self.assertTrue(diag["healthy"])

    @patch("sakthai.hub.remediator.urllib.request.urlopen")
    def test_diagnose_sleeping_space(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "runtime": {
                    "stage": "SLEEPING",
                    "hardware": {"current": "cpu-basic"},
                    "errorMessage": "Paused due to inactivity",
                }
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        diag = self.remediator.diagnose_space("Nanthasit/sakthai-tts")
        self.assertEqual(diag["state"], SpaceState.SLEEPING.value)
        self.assertFalse(diag["healthy"])

    def test_restart_space_dry_run_without_token(self):
        with patch.object(self.remediator, "_get_token", return_value=None):
            success = self.remediator.restart_space("Nanthasit/sakthai-chat")
            self.assertTrue(success)


class TestHubWebhookDispatcher(unittest.TestCase):
    def setUp(self):
        self.dispatcher = HubWebhookDispatcher(secret="test_webhook_secret_key_123")

    def test_hmac_signature_validation(self):
        payload = b'{"event": "repo.update", "repo": "Nanthasit/context-1.5b-merged"}'
        import hashlib
        import hmac

        valid_sig = hmac.new(b"test_webhook_secret_key_123", payload, hashlib.sha256).hexdigest()
        self.assertTrue(self.dispatcher.verify_signature(payload, valid_sig))
        self.assertFalse(self.dispatcher.verify_signature(payload, "invalid_signature_hex"))

    def test_event_dispatching(self):
        received = []

        def sample_callback(data):
            received.append(data)

        self.dispatcher.register_handler("repo.update", sample_callback)
        result = self.dispatcher.dispatch(
            "repo.update", {"action": "push", "ref": "refs/heads/main"}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["handlers_executed"], 1)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["action"], "push")


if __name__ == "__main__":
    unittest.main()

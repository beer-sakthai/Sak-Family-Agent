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

    @patch("sakthai.hub.remediator.urllib.request.urlopen")
    def test_diagnose_invalid_stage_fallback(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "runtime": {
                    "stage": "UNKNOWN_STAGE",
                }
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        diag = self.remediator.diagnose_space("Nanthasit/sakthai-unknown")
        self.assertEqual(diag["state"], SpaceState.STOPPED.value)
        self.assertFalse(diag["healthy"])

    @patch(
        "sakthai.hub.remediator.urllib.request.urlopen", side_effect=RuntimeError("Network Error")
    )
    def test_diagnose_exception_handling(self, mock_urlopen):
        diag = self.remediator.diagnose_space("Nanthasit/sakthai-error")
        self.assertEqual(diag["state"], SpaceState.STOPPED.value)
        self.assertFalse(diag["healthy"])
        self.assertEqual(diag["errorMessage"], "Network Error")

    def test_get_token_from_env(self):
        with patch.dict("os.environ", {"HF_TOKEN": " env_token_123 "}):
            self.assertEqual(self.remediator._get_token(), "env_token_123")

    @patch("os.path.exists", return_value=True)
    def test_get_token_from_file(self, mock_exists):
        with (
            patch("builtins.open", unittest.mock.mock_open(read_data=" file_token_456\n ")),
            patch.dict("os.environ", {}, clear=True),
        ):
            self.assertEqual(self.remediator._get_token(), "file_token_456")

    def test_restart_space_dry_run_without_token(self):
        with patch.object(self.remediator, "_get_token", return_value=None):
            success = self.remediator.restart_space("Nanthasit/sakthai-chat")
            self.assertTrue(success)

    @patch("sakthai.hub.remediator.urllib.request.urlopen")
    def test_restart_space_with_token_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch.object(self.remediator, "_get_token", return_value="token123"):
            success = self.remediator.restart_space("Nanthasit/sakthai-chat", factory_rebuild=True)
            self.assertTrue(success)

    @patch("sakthai.hub.remediator.urllib.request.urlopen", side_effect=RuntimeError("HTTP 500"))
    def test_restart_space_with_token_failure(self, mock_urlopen):
        with patch.object(self.remediator, "_get_token", return_value="token123"):
            success = self.remediator.restart_space("Nanthasit/sakthai-chat")
            self.assertFalse(success)

    def test_auto_heal_all_spaces(self):
        def mock_diagnose(space_id):
            if space_id == "space/healthy":
                return {"healthy": True, "state": SpaceState.RUNNING.value}
            elif space_id == "space/build_error":
                return {"healthy": False, "state": SpaceState.BUILD_ERROR.value}
            else:
                return {"healthy": False, "state": SpaceState.STOPPED.value}

        def mock_restart(space_id, factory_rebuild=False):
            return space_id != "space/failed"

        with (
            patch.object(self.remediator, "diagnose_space", side_effect=mock_diagnose),
            patch.object(self.remediator, "restart_space", side_effect=mock_restart),
        ):
            res = self.remediator.auto_heal_all_spaces(
                ["space/healthy", "space/build_error", "space/failed"]
            )
            self.assertEqual(res["probed"], 3)
            self.assertEqual(res["healthy"], 1)
            self.assertIn("space/build_error", res["remediated"])
            self.assertIn("space/failed", res["failed"])


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

"""Tests for SakSit Live Hugging Face Hub Metadata Hydration & TTL Caching."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sakthai.agent.stager import (
    ContentTemplateStager,
    fetch_live_hub_metadata,
)


class TestLiveHubHydration(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.stager = ContentTemplateStager(cache_dir=self.tmp_dir)

    @patch("httpx.get")
    def test_fetch_live_hub_metadata_success_and_cache(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "beer-sakthai/SakThai-Decision-1",
            "downloads": 18450,
            "likes": 56,
            "sha": "d4e5f6a7b8c9",
            "tags": ["agent", "rl", "openenv"],
        }
        mock_get.return_value = mock_response

        meta = fetch_live_hub_metadata(
            "beer-sakthai/SakThai-Decision-1",
            repo_type="model",
            cache_dir=self.tmp_dir / "hub_metadata",
        )

        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta["downloads"], 18450)
        self.assertEqual(meta["likes"], 56)
        self.assertEqual(meta["sha"], "d4e5f6a7b8c9")
        self.assertEqual(mock_get.call_count, 1)

        # Second call within TTL should hit cache without network request
        meta_cached = fetch_live_hub_metadata(
            "beer-sakthai/SakThai-Decision-1",
            repo_type="model",
            cache_dir=self.tmp_dir / "hub_metadata",
        )
        self.assertIsNotNone(meta_cached)
        self.assertEqual(mock_get.call_count, 1)

    @patch("httpx.get")
    def test_fetch_live_hub_metadata_offline_fallback(self, mock_get: MagicMock) -> None:
        # First save an offline cache manually
        repo_id = "beer-sakthai/SakThai-Decision-1"
        self.stager.save_cached_hub_metadata(
            repo_id,
            {"downloads": 12000, "likes": 40, "sha": "old_commit", "cached_at": time.time() - 7200},
        )

        # Simulate network failure
        mock_get.side_effect = Exception("Connection timed out")

        meta = fetch_live_hub_metadata(
            repo_id,
            repo_type="model",
            cache_dir=self.tmp_dir / "hub_metadata",
            ttl_seconds=3600,
        )

        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta["downloads"], 12000)

    @patch("httpx.get")
    def test_fetch_live_hub_metadata_not_found(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        meta = fetch_live_hub_metadata(
            "beer-sakthai/nonexistent-model",
            repo_type="model",
            cache_dir=self.tmp_dir / "hub_metadata",
        )
        self.assertIsNone(meta)

    @patch("sakthai.agent.stager.fetch_live_hub_metadata")
    def test_hydrate_with_live_hub(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = {
            "downloads": 25000,
            "likes": 99,
            "sha": "a1b2c3d4",
        }

        template = (
            "Release {{VERSION}}: {{REPO_ID}} reached {{DOWNLOADS}} downloads "
            "and {{LIKES}} stars with commit {{COMMIT_SHA}}."
        )

        hydrated = self.stager.hydrate_with_live_hub(
            template=template,
            repo_id="beer-sakthai/SakThai-Decision-1",
            variables={"VERSION": "v2.65.0"},
        )

        self.assertIn("v2.65.0", hydrated)
        self.assertIn("25000", hydrated)
        self.assertIn("99", hydrated)
        self.assertIn("a1b2c3d4", hydrated)
        self.assertEqual(self.stager.detect_unresolved_placeholders(hydrated), [])

    @patch("sakthai.agent.stager.fetch_live_hub_metadata")
    def test_hydrate_with_live_hub_meta_none_and_partial(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = None
        template = "Release {{REPO_ID}}"
        out = self.stager.hydrate_with_live_hub(template, "my-repo")
        self.assertEqual(out, "Release my-repo")

        # Partial meta without downloads, likes, or sha
        mock_fetch.return_value = {"other_key": 123}
        out_partial = self.stager.hydrate_with_live_hub("Repo {{REPO_ID}}", "my-repo")
        self.assertEqual(out_partial, "Repo my-repo")

    @patch("httpx.get")
    def test_fetch_live_hub_dataset_and_token(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "beer-sakthai/dataset-1", "downloads": 500}
        mock_get.return_value = mock_resp

        meta = fetch_live_hub_metadata(
            "beer-sakthai/dataset-1",
            repo_type="dataset",
            cache_dir=self.tmp_dir / "hub_metadata",
            hf_token="custom_token_123",
        )
        self.assertIsNotNone(meta)
        self.assertEqual(meta["downloads"], 500)  # type: ignore[index]
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("datasets/beer-sakthai/dataset-1", args[0])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer custom_token_123")

    @patch("httpx.get")
    def test_fetch_live_hub_cache_corrupted_and_non_dict(self, mock_get: MagicMock) -> None:
        cache_dir = self.tmp_dir / "hub_metadata_corrupt"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "test_repo.json"

        # Corrupted JSON in cache
        cache_file.write_text("{corrupt-json", encoding="utf-8")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "test/repo", "downloads": 10}
        mock_get.return_value = mock_resp

        meta = fetch_live_hub_metadata("test/repo", cache_dir=cache_dir)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["downloads"], 10)  # type: ignore[index]

        # Non-dict JSON in cache
        cache_file.write_text("[1, 2, 3]", encoding="utf-8")
        meta2 = fetch_live_hub_metadata("test/repo", cache_dir=cache_dir)
        self.assertIsNotNone(meta2)

    @patch("httpx.get")
    def test_fetch_live_hub_non_dict_api_response_and_server_error(
        self, mock_get: MagicMock
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = ["not", "a", "dict"]
        mock_get.return_value = mock_resp

        meta = fetch_live_hub_metadata("test/list-response", cache_dir=self.tmp_dir / "hub_meta")
        self.assertIsNone(meta)

        # 500 internal server error
        mock_resp.status_code = 500
        meta_err = fetch_live_hub_metadata("test/server-error", cache_dir=self.tmp_dir / "hub_meta")
        self.assertIsNone(meta_err)


if __name__ == "__main__":
    unittest.main()

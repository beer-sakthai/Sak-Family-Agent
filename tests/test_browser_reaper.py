"""Unit tests for browser process reaper, launch args hardening, and timeout supervisor."""

from __future__ import annotations

import time
import unittest

from sakthai.agent.browser_reaper import (
    BrowserTimeoutError,
    cleanup_temp_browser_profiles,
    enforce_browser_launch_args,
    reap_orphaned_browser_processes,
    run_browser_task_with_timeout,
)


class TestBrowserReaper(unittest.TestCase):
    def test_enforce_browser_launch_args(self) -> None:
        initial_args = ["npx", "playwright", "test"]
        hardened = enforce_browser_launch_args(initial_args)
        self.assertIn("--disable-dev-shm-usage", hardened)
        self.assertIn("--no-sandbox", hardened)

    def test_enforce_browser_launch_args_idempotent(self) -> None:
        initial_args = ["playwright", "--no-sandbox", "--disable-dev-shm-usage"]
        hardened = enforce_browser_launch_args(initial_args)
        self.assertEqual(hardened.count("--no-sandbox"), 1)
        self.assertEqual(hardened.count("--disable-dev-shm-usage"), 1)

    def test_reap_orphaned_browser_processes_dry_run(self) -> None:
        count = reap_orphaned_browser_processes(dry_run=True)
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_cleanup_temp_browser_profiles(self) -> None:
        import os
        import tempfile

        d = tempfile.mkdtemp(prefix="playwright_profile_test_")
        self.assertTrue(os.path.isdir(d))
        cleaned = cleanup_temp_browser_profiles([d])
        self.assertIn(d, cleaned)
        self.assertFalse(os.path.exists(d))

    def test_run_browser_task_with_timeout_success(self) -> None:
        def quick_task() -> str:
            return "scraped_data"

        res = run_browser_task_with_timeout(quick_task, timeout_seconds=2.0)
        self.assertEqual(res, "scraped_data")

    def test_run_browser_task_with_timeout_exceeded(self) -> None:
        def slow_task() -> str:
            time.sleep(0.5)
            return "too_late"

        with self.assertRaises(BrowserTimeoutError):
            run_browser_task_with_timeout(slow_task, timeout_seconds=0.1)

    def test_reap_orphaned_browser_processes_mocked_kill(self) -> None:
        import os
        from unittest.mock import MagicMock, patch

        mock_proc = MagicMock(returncode=0, stdout=f"{os.getpid()}\n99999\nnot_a_pid\n")
        with patch("subprocess.run", return_value=mock_proc), patch("os.kill") as mock_kill:
            reaped = reap_orphaned_browser_processes(dry_run=False)
            self.assertEqual(reaped, 1)
            mock_kill.assert_called_once_with(99999, 15)

    def test_reap_orphaned_browser_processes_exception_handling(self) -> None:
        from unittest.mock import patch

        with patch("subprocess.run", side_effect=RuntimeError("pgrep failed")):
            reaped = reap_orphaned_browser_processes(dry_run=False)
            self.assertEqual(reaped, 0)

    def test_cleanup_temp_browser_profiles_edge_cases(self) -> None:
        from unittest.mock import patch

        # None argument
        self.assertEqual(cleanup_temp_browser_profiles(None), [])
        # Non-string entries and non-existent paths
        cleaned = cleanup_temp_browser_profiles(["/non/existent/path/12345", None, ""])  # type: ignore[list-item]
        self.assertEqual(cleaned, [])

        # Directory where rmtree raises exception
        with (
            patch("os.path.isdir", return_value=True),
            patch("shutil.rmtree", side_effect=PermissionError("denied")),
        ):
            cleaned = cleanup_temp_browser_profiles(["/dummy/dir"])
            self.assertEqual(cleaned, [])

    def test_reap_orphaned_browser_processes_mocked_dry_run(self) -> None:
        import os
        from unittest.mock import MagicMock, patch

        mock_proc = MagicMock(returncode=0, stdout=f"{os.getpid()}\n88888\n")
        with patch("subprocess.run", return_value=mock_proc):
            reaped = reap_orphaned_browser_processes(dry_run=True)
            self.assertEqual(reaped, 1)


if __name__ == "__main__":
    unittest.main()

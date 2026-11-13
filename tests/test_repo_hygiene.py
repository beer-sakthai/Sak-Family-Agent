"""Verify repository hygiene: no committed scratch directories (.manus, profiles, apps/*/.agents)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATHS = (
    REPO_ROOT / ".manus",
    REPO_ROOT / "profiles",
    REPO_ROOT / "apps" / "agent_workflow_framework" / ".agents",
    REPO_ROOT / "apps" / "agent_workflow_framework" / "ORIGINAL_REQUEST.md",
    REPO_ROOT / "apps" / "sak_agent_dashboard" / ".agents",
)


class TestRepoHygiene(unittest.TestCase):
    def test_no_forbidden_scratch_directories_exist(self) -> None:
        for path in FORBIDDEN_PATHS:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertFalse(
                    path.exists(),
                    f"Ephemeral scratch path {path.relative_to(REPO_ROOT)} must not exist in the repository",
                )

    def test_root_agents_dir_contains_only_project_rules(self) -> None:
        agents_dir = REPO_ROOT / ".agents"
        self.assertTrue(agents_dir.is_dir())
        items = [p.name for p in agents_dir.iterdir()]
        self.assertEqual(items, ["AGENTS.md"])

    def test_gitignore_blocks_subproject_agents_and_workflow_runs(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("apps/*/.agents/", gitignore)
        self.assertIn(".workflow_runs/", gitignore)


if __name__ == "__main__":
    unittest.main()

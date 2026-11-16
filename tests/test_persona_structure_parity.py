"""Verify structural parity and symlink deduplication across all 6 Sak Family personas."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")
EXPECTED_PERSONA_ITEMS = {
    "AGENTS.md",
    "BACKPACK.md",
    "CYCLE.md",
    "HANDOFF.md",
    "LIBRARY_README.md",
    "MEMORY.md",
    "PLAN.md",
    "README.md",
    "SOUL.md",
    "__init__.py",
    "__main__.py",
    "agent",
    "agent_platform",
    "auth.py",
    "automation",
    "cli",
    "client",
    "coding",
    "config",
    "config.py",
    "cycle",
    "dashboard",
    "datasets",
    "devops",
    "evolution",
    "evolve_agent.sh",
    "extensions",
    "generate_report.py",
    "giturl.py",
    "hf.py",
    "lead",
    "learn",
    "learning",
    "llm",
    "mcp",
    "memory",
    "observability",
    "pyproject.toml",
    "reports",
    "research",
    "safety",
    "sakking_skills.py",
    "sandbox.py",
    "scripts",
    "security",
    "skills",
    "skills.py",
    "team",
    "telegram",
    "tests",
    "web",
}
EXPECTED_CONFIG_ITEMS = {
    "config.yaml",
    "gateway_voice_mode.json",
    "mcp.json",
    "workspace.yaml",
}
EXPECTED_LIBRARY_ITEMS = {
    "LIBRARY_README.md",
    "automation",
    "coding",
    "devops",
    "learning",
    "llm",
    "observability",
    "research",
    "safety",
    "security",
}
EXPECTED_PACKAGE_ITEMS = {
    "__init__.py",
    "__main__.py",
    "agent",
    "agent_platform",
    "auth.py",
    "cli",
    "client",
    "config.py",
    "cycle",
    "dashboard",
    "extensions",
    "giturl.py",
    "hf.py",
    "lead",
    "learn",
    "mcp",
    "memory",
    "sakking_skills.py",
    "sandbox.py",
    "scripts",
    "skills.py",
    "team",
    "telegram",
    "web",
}


class TestPersonaStructureParity(unittest.TestCase):
    def test_every_persona_has_exact_ten_top_level_items(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                pdir = REPO_ROOT / "personas" / persona
                actual = {
                    item.name
                    for item in pdir.iterdir()
                    if not item.name.endswith(".egg-info")
                    and not item.name.startswith(".")
                    and item.name != "__pycache__"
                }
                self.assertEqual(actual, EXPECTED_PERSONA_ITEMS)

    def test_every_persona_has_exact_four_config_files(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                cdir = REPO_ROOT / "personas" / persona / "config"
                actual = {item.name for item in cdir.iterdir()}
                self.assertEqual(actual, EXPECTED_CONFIG_ITEMS)

    def test_all_personas_have_real_package_files_and_no_nested_sakthai_folder(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                # Ensure no folder named 'sakthai' exists
                sakthai_folder = REPO_ROOT / "personas" / persona / "sakthai"
                self.assertFalse(
                    sakthai_folder.exists(),
                    f"personas/{persona}/sakthai must not exist",
                )
                # Ensure all 24 core package items are real files/directories, not symlinks
                for item in EXPECTED_PACKAGE_ITEMS:
                    item_path = REPO_ROOT / "personas" / persona / item
                    self.assertTrue(item_path.exists(), f"personas/{persona}/{item} must exist")
                    self.assertFalse(
                        item_path.is_symlink(),
                        f"personas/{persona}/{item} must be a real file/dir, not a symlink",
                    )

    def test_all_personas_resolve_to_single_canonical_self_evolution_dir(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                evo_dir = REPO_ROOT / "personas" / persona / "evolution"
                self.assertTrue(
                    evo_dir.is_dir(),
                    f"personas/{persona}/evolution must be a directory",
                )
                self.assertFalse(
                    (REPO_ROOT / "personas" / persona / "agent-self-evolution").exists(),
                    f"personas/{persona}/agent-self-evolution must not exist",
                )

    def test_all_personas_have_real_library_items_and_no_nested_library_folder(self) -> None:
        self.assertFalse((REPO_ROOT / "library").exists(), "REPO_ROOT / library must not exist")
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                # Ensure no folder named 'library' exists
                lib_folder = REPO_ROOT / "personas" / persona / "library"
                self.assertFalse(
                    lib_folder.exists(),
                    f"personas/{persona}/library must not exist",
                )
                for item in EXPECTED_LIBRARY_ITEMS:
                    item_path = REPO_ROOT / "personas" / persona / item
                    self.assertTrue(item_path.exists(), f"personas/{persona}/{item} must exist")
                    self.assertFalse(
                        item_path.is_symlink(),
                        f"personas/{persona}/{item} must be a real file/dir, not a symlink",
                    )
                # Check agent and memory have DESCRIPTION.md
                self.assertTrue(
                    (REPO_ROOT / "personas" / persona / "agent" / "DESCRIPTION.md").exists()
                )
                self.assertTrue(
                    (REPO_ROOT / "personas" / persona / "memory" / "DESCRIPTION.md").exists()
                )

    def test_hermes_agents_directory_does_not_exist(self) -> None:
        hermes_root = REPO_ROOT / "infra" / "hermes-agents"
        self.assertFalse(
            hermes_root.exists(),
            "infra/hermes-agents must not exist; personas run standalone via sakthai",
        )

    def test_evolve_agent_script_byte_identical_across_all_personas(self) -> None:
        """Ensure evolve_agent.sh is byte-identical across all 6 personas."""
        base_content = (REPO_ROOT / "personas" / PERSONAS[0] / "evolve_agent.sh").read_bytes()
        for persona in PERSONAS[1:]:
            with self.subTest(persona=persona):
                content = (REPO_ROOT / "personas" / persona / "evolve_agent.sh").read_bytes()
                self.assertEqual(
                    content,
                    base_content,
                    f"personas/{persona}/evolve_agent.sh differs from personas/{PERSONAS[0]}/evolve_agent.sh",
                )

    def test_evolve_agent_script_has_no_unpinned_pip_install(self) -> None:
        """Prevent Scorecard Pinned-Dependencies alerts (pipCommand not pinned by hash)."""
        import re

        pip_install_re = re.compile(r"(?<!uv\s)(?<!uv\s-q\s)\b(pip|pip3)\s+install\b")
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                script_path = REPO_ROOT / "personas" / persona / "evolve_agent.sh"
                script_text = script_path.read_text(encoding="utf-8")
                self.assertNotRegex(
                    script_text,
                    pip_install_re,
                    f"personas/{persona}/evolve_agent.sh contains unpinned pip/pip3 install command",
                )
                self.assertIn("command -v uv", script_text)
                self.assertIn("uv pip install", script_text)

    def test_bootstrap_scripts_have_no_unpinned_pip_install(self) -> None:
        """Prevent Scorecard Pinned-Dependencies alerts in bootstrap scripts."""
        import re

        pip_install_re = re.compile(r"(?<!uv\s)(?<!uv\s-q\s)\b(pip|pip3)\s+install\b")
        for rel_path in ["scripts/bootstrap.sh", "sakthai-chat-cli/scripts/bootstrap.sh"]:
            with self.subTest(script=rel_path):
                script_path = REPO_ROOT / rel_path
                script_text = script_path.read_text(encoding="utf-8")
                self.assertNotRegex(
                    script_text,
                    pip_install_re,
                    f"{rel_path} contains unpinned pip/pip3 install command",
                )
                self.assertIn("command -v uv", script_text)
                self.assertIn("uv pip install", script_text)

    def test_dockerfile_sandbox_has_no_unpinned_pip_install(self) -> None:
        """Prevent Scorecard Pinned-Dependencies alerts in Dockerfile.sandbox."""
        import re

        pip_install_re = re.compile(r"(?<!uv\s)(?<!uv\s-q\s)\b(pip|pip3)\s+install\b")
        df_path = REPO_ROOT / "Dockerfile.sandbox"
        df_text = df_path.read_text(encoding="utf-8")
        self.assertNotRegex(
            df_text,
            pip_install_re,
            "Dockerfile.sandbox contains unpinned pip/pip3 install command",
        )
        self.assertIn("uv pip install", df_text)

    def test_cache_cleanup_workflow_permissions_scoped(self) -> None:
        """Prevent Scorecard Token-Permissions alerts in cache-cleanup.yml."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "cache-cleanup.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("permissions: read-all", workflow_text)
        self.assertNotIn("permissions:\n  actions: write", workflow_text)


if __name__ == "__main__":
    unittest.main()

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
    "MEMORY.md",
    "PLAN.md",
    "README.md",
    "SOUL.md",
    "__init__.py",
    "__main__.py",
    "agent",
    "agent_platform",
    "auth.py",
    "cli",
    "client",
    "config",
    "config.py",
    "cycle",
    "dashboard",
    "datasets",
    "evolution",
    "evolve_agent.sh",
    "extensions",
    "gateway",
    "generate_report.py",
    "giturl.py",
    "hf.py",
    "lead",
    "learn",
    "mcp",
    "memory",
    "pyproject.toml",
    "reports",
    "sakking_skills.py",
    "sandbox.py",
    "scripts",
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
LEGACY_LIBRARY_ITEMS = {
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
LEGACY_AGENT_SKILLS = {
    "sakthai-agent-planning",
    "sakthai-agent-reasoning",
    "sakthai-agent-sessions",
    "sakthai-agent-tools",
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
    "gateway",
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

    def test_legacy_library_items_and_nested_library_do_not_exist(self) -> None:
        self.assertFalse((REPO_ROOT / "library").exists(), "REPO_ROOT / library must not exist")
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                # Ensure no folder named 'library' exists
                lib_folder = REPO_ROOT / "personas" / persona / "library"
                self.assertFalse(
                    lib_folder.exists(),
                    f"personas/{persona}/library must not exist",
                )
                for item in LEGACY_LIBRARY_ITEMS:
                    item_path = REPO_ROOT / "personas" / persona / item
                    self.assertFalse(
                        item_path.exists(),
                        f"Legacy item personas/{persona}/{item} must be pruned",
                    )
                for item in LEGACY_AGENT_SKILLS:
                    item_path = REPO_ROOT / "personas" / persona / "agent" / item
                    self.assertFalse(
                        item_path.exists(),
                        f"Legacy agent skill personas/{persona}/agent/{item} must be pruned",
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
        for rel_path in ["scripts/bootstrap.sh"]:
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
        self.assertIn("permissions: {}", workflow_text)
        self.assertIn("permissions:\n      actions: write\n      contents: read", workflow_text)
        self.assertNotIn("permissions: read-all", workflow_text)
        self.assertTrue(
            "permissions: {}" in workflow_text or "permissions: read-all" in workflow_text,
            "cache-cleanup.yml top-level permissions must be scoped (empty mapping {} or read-all)",
        )
        self.assertNotIn("permissions:\n  actions: write", workflow_text)

    def test_all_core_subpackages_byte_identical_across_personas(self) -> None:
        """Ensure all core Python subpackages are byte-identical to canonical personas/sakthai/."""
        canonical_root = REPO_ROOT / "personas" / "sakthai"
        subpackages = (
            "agent",
            "agent_platform",
            "cli",
            "client",
            "cycle",
            "dashboard",
            "extensions",
            "gateway",
            "lead",
            "learn",
            "mcp",
            "memory",
            "team",
            "telegram",
            "web",
        )
        for persona in PERSONAS[1:]:
            p_root = REPO_ROOT / "personas" / persona
            for pkg in subpackages:
                c_pkg = canonical_root / pkg
                p_pkg = p_root / pkg
                self.assertTrue(p_pkg.is_dir(), f"Missing subpackage {pkg} in personas/{persona}")
                for c_file in c_pkg.rglob("*.py"):
                    rel = c_file.relative_to(c_pkg)
                    p_file = p_pkg / rel
                    self.assertTrue(
                        p_file.is_file(),
                        f"Missing file {rel} in personas/{persona}/{pkg}",
                    )
                    self.assertEqual(
                        p_file.read_bytes(),
                        c_file.read_bytes(),
                        f"personas/{persona}/{pkg}/{rel} differs from canonical personas/sakthai/{pkg}/{rel}",
                    )

    def test_handoff_md_skill_counts_match_actual_on_disk_counts(self) -> None:
        """Ensure Overlay Skills counts in HANDOFF.md match actual on-disk counts."""
        import re

        for persona in PERSONAS:
            sdir = REPO_ROOT / "personas" / persona / "skills"
            actual_count = (
                sum(1 for d in sdir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
                if sdir.is_dir()
                else 0
            )
            handoff_path = REPO_ROOT / "personas" / persona / "HANDOFF.md"
            handoff_text = handoff_path.read_text(encoding="utf-8")
            pattern = rf"\*\*{persona}\*\*.*\|\s*(\d+)\s*\|"
            m = re.search(pattern, handoff_text, re.IGNORECASE)
            self.assertIsNotNone(m, f"Could not find {persona} row in {handoff_path}")
            declared = int(m.group(1))  # type: ignore[union-attr]
            self.assertEqual(
                declared,
                actual_count,
                f"{handoff_path} declares {declared} skills for {persona}, but disk has {actual_count}",
            )

    def test_memory_md_skill_counts_match_actual_on_disk_counts(self) -> None:
        """Ensure Skills Overlay counts in MEMORY.md match actual on-disk counts."""
        import re

        for persona in PERSONAS:
            sdir = REPO_ROOT / "personas" / persona / "skills"
            actual_count = (
                sum(1 for d in sdir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
                if sdir.is_dir()
                else 0
            )
            mem_path = REPO_ROOT / "personas" / persona / "MEMORY.md"
            mem_text = mem_path.read_text(encoding="utf-8")
            m = re.search(r"Skills Overlay\*\*:\s*(\d+)\s*skills", mem_text)
            self.assertIsNotNone(m, f"Missing Skills Overlay declaration in {mem_path}")
            declared = int(m.group(1))  # type: ignore[union-attr]
            self.assertEqual(
                declared,
                actual_count,
                f"{mem_path} declares {declared} skills for {persona}, but disk has {actual_count}",
            )

    def test_plan_md_skill_counts_match_actual_on_disk_counts(self) -> None:
        """Ensure overlay skills counts in PLAN.md match actual on-disk counts."""
        import re

        for persona in PERSONAS:
            sdir = REPO_ROOT / "personas" / persona / "skills"
            actual_count = (
                sum(1 for d in sdir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
                if sdir.is_dir()
                else 0
            )
            plan_path = REPO_ROOT / "personas" / persona / "PLAN.md"
            plan_text = plan_path.read_text(encoding="utf-8")
            m = re.search(r"(\d+)\s+overlay skills", plan_text)
            self.assertIsNotNone(m, f"Missing overlay skills declaration in {plan_path}")
            declared = int(m.group(1))  # type: ignore[union-attr]
            self.assertEqual(
                declared,
                actual_count,
                f"{plan_path} declares {declared} skills for {persona}, but disk has {actual_count}",
            )


if __name__ == "__main__":
    unittest.main()

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
    "config",
    "datasets",
    "evolution",
    "evolve_agent.sh",
    "generate_report.py",
    "pyproject.toml",
    "reports",
    "sakthai",
    "skills",
    "tests",
}
EXPECTED_CONFIG_ITEMS = {
    "config.yaml",
    "gateway_voice_mode.json",
    "mcp.json",
    "workspace.yaml",
}
EXPECTED_HERMES_ITEMS = {
    "BACKPACK.md",
    "CYCLE.md",
    "HANDOFF.md",
    "MEMORY.md",
    "PLAN.md",
    "SOUL.md",
    "config.yaml",
}


class TestPersonaStructureParity(unittest.TestCase):
    def test_every_persona_has_exact_ten_top_level_items(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                pdir = REPO_ROOT / "personas" / persona
                actual = {
                    item.name
                    for item in pdir.iterdir()
                    if not item.name.endswith(".egg-info") and not item.name.startswith(".")
                }
                self.assertEqual(actual, EXPECTED_PERSONA_ITEMS)

    def test_every_persona_has_exact_four_config_files(self) -> None:
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                cdir = REPO_ROOT / "personas" / persona / "config"
                actual = {item.name for item in cdir.iterdir()}
                self.assertEqual(actual, EXPECTED_CONFIG_ITEMS)

    def test_all_personas_resolve_to_single_canonical_sakthai_package(self) -> None:
        canonical = (REPO_ROOT / "personas" / "sakthai" / "sakthai").resolve()
        self.assertTrue(canonical.is_dir())
        shared = REPO_ROOT / "personas" / "shared" / "sakthai"
        self.assertTrue(shared.is_symlink(), "personas/shared/sakthai must be a symlink")
        self.assertEqual(shared.resolve(), canonical)
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                pkg_path = REPO_ROOT / "personas" / persona / "sakthai"
                if persona != "sakthai":
                    self.assertTrue(
                        pkg_path.is_symlink(),
                        f"personas/{persona}/sakthai must be a symlink, not a duplicate directory",
                    )
                self.assertEqual(pkg_path.resolve(), canonical)

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

    def test_hermes_profiles_expose_all_seven_items(self) -> None:
        hermes_root = REPO_ROOT / "infra" / "hermes-agents"
        targets = [hermes_root / "default"] + [
            hermes_root / "profiles" / p for p in PERSONAS if p != "sakthai"
        ]
        for target in targets:
            with self.subTest(target=str(target.relative_to(REPO_ROOT))):
                actual = {item.name for item in target.iterdir()}
                self.assertEqual(actual, EXPECTED_HERMES_ITEMS)


if __name__ == "__main__":
    unittest.main()

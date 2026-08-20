"""Guard against drift between ci-cd-doctor skill copies.

The ci-cd-doctor skill is intentionally byte-identical across two locations:
  - .claude-plugins/ci-cd-doctor/skills/ci-cd-doctor/SKILL.md (plugin)
  - .agents/skills/ci-cd-doctor/SKILL.md (agents CLI)

This parity constraint allows the skill to be kept in sync with a single edit.
If the copies diverge, the constraint fails CI and requires explicit resolution.
"""

import unittest
from pathlib import Path


class TestCiCdDoctorSkillParity(unittest.TestCase):
    """Guard against ci-cd-doctor skill drift across the two locations."""

    REPO_ROOT = Path(__file__).resolve().parents[1]
    PLUGIN_SKILL = (
        REPO_ROOT / ".claude-plugins" / "ci-cd-doctor" / "skills" / "ci-cd-doctor" / "SKILL.md"
    )
    AGENTS_SKILL = REPO_ROOT / ".agents" / "skills" / "ci-cd-doctor" / "SKILL.md"

    def test_skill_byte_parity(self):
        """Both ci-cd-doctor SKILL.md copies must be byte-identical."""
        plugin_content = self.PLUGIN_SKILL.read_bytes()
        agents_content = self.AGENTS_SKILL.read_bytes()

        self.assertEqual(
            plugin_content,
            agents_content,
            f"ci-cd-doctor SKILL.md files diverged:\n"
            f"  Plugin: {self.PLUGIN_SKILL}\n"
            f"  Agents: {self.AGENTS_SKILL}\n"
            f"Edit one and copy the change to the other, then re-run.",
        )

    def test_both_files_exist(self):
        """Both ci-cd-doctor SKILL.md files must exist."""
        self.assertTrue(
            self.PLUGIN_SKILL.exists(),
            f"Plugin ci-cd-doctor SKILL.md not found at {self.PLUGIN_SKILL}",
        )
        self.assertTrue(
            self.AGENTS_SKILL.exists(),
            f"Agents ci-cd-doctor SKILL.md not found at {self.AGENTS_SKILL}",
        )


if __name__ == "__main__":
    unittest.main()

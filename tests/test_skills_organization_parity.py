"""Automated invariant tests for 6-agent skill organization, deduplication, and parity."""

from __future__ import annotations

import hashlib
import unittest
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")
SHARED_DIR = PERSONAS_DIR / "shared" / "skills"

UNIVERSAL_CYCLE_SLUGS = (
    "cycle-dream",
    "cycle-hope",
    "cycle-care",
    "cycle-joy",
    "cycle-trust",
    "cycle-growth",
    "auto-cycle-loop",
)


class TestSkillsOrganizationParity(unittest.TestCase):
    """Assert skills across all 6 personas follow structural and deduplication invariants."""

    def test_shared_universal_cycle_skills_exist(self) -> None:
        """Universal cycle skills must exist in personas/shared/skills/ under Sak- prefix."""
        self.assertTrue(SHARED_DIR.is_dir(), f"Shared skills directory missing: {SHARED_DIR}")
        for slug in UNIVERSAL_CYCLE_SLUGS:
            expected_name = f"Sak-{slug}"
            skill_md = SHARED_DIR / expected_name / "SKILL.md"
            self.assertTrue(
                skill_md.is_file(),
                f"Missing universal shared cycle skill: {skill_md}",
            )

    def test_no_double_prefixed_skills(self) -> None:
        """No skills should carry redundant double prefixes like SakThai-sakthai-*."""
        double_prefixed: list[str] = []
        for persona in PERSONAS:
            sdir = PERSONAS_DIR / persona / "skills"
            if not sdir.is_dir():
                continue
            for entry in sdir.iterdir():
                if entry.is_dir() and f"-{persona}-" in entry.name.lower():
                    double_prefixed.append(f"{persona}/{entry.name}")
        self.assertEqual(
            double_prefixed,
            [],
            f"Found double-prefixed skills that must be canonicalized: {double_prefixed}",
        )

    def test_no_duplicate_skill_bodies_across_personas(self) -> None:
        """No identical SKILL.md body content should be duplicated across different personas."""
        body_to_paths = defaultdict(list)
        for persona in PERSONAS:
            sdir = PERSONAS_DIR / persona / "skills"
            if not sdir.is_dir():
                continue
            for entry in sdir.iterdir():
                md = entry / "SKILL.md"
                if not md.is_file():
                    continue
                content = md.read_bytes()
                parts = content.split(b"---", 2)
                body = parts[2].strip() if len(parts) >= 3 else content.strip()
                # Hash normalized body
                body_hash = hashlib.sha256(b" ".join(body.split())).hexdigest()
                body_to_paths[body_hash].append(f"{persona}/{entry.name}")

        cross_persona_dupes = {
            h: paths
            for h, paths in body_to_paths.items()
            if len({p.split("/")[0] for p in paths}) > 1
        }
        self.assertEqual(
            cross_persona_dupes,
            {},
            f"Found identical skill bodies duplicated across personas: {list(cross_persona_dupes.values())[:5]}",
        )

    def test_all_skills_have_required_metadata(self) -> None:
        """Every skill must contain valid name, description, and version in frontmatter."""
        missing_metadata: list[str] = []
        roots = [SHARED_DIR] + [PERSONAS_DIR / p / "skills" for p in PERSONAS]
        for root in roots:
            if not root.is_dir():
                continue
            for md in sorted(root.rglob("SKILL.md")):
                try:
                    parts = md.read_text(encoding="utf-8").split("---", 2)
                    if len(parts) < 3:
                        missing_metadata.append(f"{md}: missing frontmatter fences")
                        continue
                    front = yaml.safe_load(parts[1])
                    if not isinstance(front, dict):
                        missing_metadata.append(f"{md}: frontmatter is not a dict")
                        continue
                    if not front.get("name"):
                        missing_metadata.append(f"{md}: missing 'name'")
                    if not front.get("description"):
                        missing_metadata.append(f"{md}: missing 'description'")
                    if not front.get("version"):
                        missing_metadata.append(f"{md}: missing 'version'")
                except Exception as exc:
                    missing_metadata.append(f"{md}: parse error {exc}")

        self.assertEqual(
            missing_metadata,
            [],
            f"Found {len(missing_metadata)} skills with missing metadata. Sample: {missing_metadata[:10]}",
        )


if __name__ == "__main__":
    unittest.main()

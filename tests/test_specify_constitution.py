"""Automated invariant tests for .specify Spec-Kit constitution and configuration."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECIFY_DIR = REPO_ROOT / ".specify"
CONSTITUTION_PATH = SPECIFY_DIR / "memory" / "constitution.md"
INTEGRATION_PATH = SPECIFY_DIR / "integration.json"
INIT_OPTIONS_PATH = SPECIFY_DIR / "init-options.json"
SCRIPTS_DIR = SPECIFY_DIR / "scripts" / "bash"
EXPECTED_PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")


class TestSpecifyConstitution(unittest.TestCase):
    """Enforce House of Sak .specify Constitution and Spec-Kit configuration invariants."""

    def test_constitution_exists_and_ratified(self) -> None:
        """Constitution must exist, be ratified, and contain core architectural invariants."""
        self.assertTrue(CONSTITUTION_PATH.is_file(), f"Missing constitution: {CONSTITUTION_PATH}")
        content = CONSTITUTION_PATH.read_text(encoding="utf-8")

        # Must not contain unreplaced boilerplate tokens
        self.assertNotIn("[PROJECT_NAME]", content)
        self.assertNotIn("[PRINCIPLE_1_NAME]", content)
        self.assertNotIn("[GOVERNANCE_RULES]", content)

        # Core architectural invariants
        self.assertIn("House of Sak Constitution", content)
        self.assertIn("96%", content, "Must enforce the 96% coverage floor")
        self.assertIn("personas/sakthai/", content, "Must define canonical package path")
        self.assertIn("Version**: 1.0.0", content)
        self.assertIn("Ratified**:", content)

        # Persona coverage
        content_lower = content.lower()
        for persona in EXPECTED_PERSONAS:
            self.assertIn(
                persona,
                content_lower,
                f"Persona '{persona}' must be referenced in the constitution",
            )

    def test_integration_json_validity(self) -> None:
        """integration.json must be valid JSON with multi-agent integrations configured."""
        self.assertTrue(INTEGRATION_PATH.is_file(), f"Missing integration.json: {INTEGRATION_PATH}")
        with INTEGRATION_PATH.open(encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("version", data)
        self.assertIn("installed_integrations", data)
        installed = data["installed_integrations"]
        self.assertIn("copilot", installed)
        self.assertIn("claude", installed)
        self.assertIn("gemini", installed)

    def test_init_options_validity(self) -> None:
        """init-options.json must be valid JSON pointing to speckit."""
        self.assertTrue(INIT_OPTIONS_PATH.is_file(), f"Missing init-options: {INIT_OPTIONS_PATH}")
        with INIT_OPTIONS_PATH.open(encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("speckit_version", data)
        self.assertEqual(data["speckit_version"], "0.15.1")

    def test_specify_bash_scripts_syntax(self) -> None:
        """All bash scripts in .specify/scripts/bash/ must be syntax-clean."""
        self.assertTrue(SCRIPTS_DIR.is_dir(), f"Missing scripts dir: {SCRIPTS_DIR}")
        script_files = sorted(SCRIPTS_DIR.glob("*.sh"))
        self.assertGreater(len(script_files), 0, "No bash scripts found in .specify/scripts/bash/")

        for script in script_files:
            self.assertTrue(
                os.access(script, os.X_OK),
                f"Script must be executable: {script.name}",
            )
            result = subprocess.run(
                ["bash", "-n", str(script)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"Syntax error in {script.name}:\n{result.stderr}",
            )

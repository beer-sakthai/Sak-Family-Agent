"""Guard against agent/eval.py and cli/eval.py drift across persona snapshots.

``agent/eval.py`` and ``cli/eval.py`` handle local model evaluation, MLOps metrics,
and persona readiness assessment. Like ``agent/guardrails.py`` and ``web/server.py``,
they exist in each persona's package tree. This test fails CI the moment any copy
diverges from ``personas/sakthai/agent/eval.py`` or ``personas/sakthai/cli/eval.py``.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ["sakjules", "saktan", "sakking", "saksee", "saksit"]
AGENT_EVAL_REL = Path("agent") / "eval.py"
CLI_EVAL_REL = Path("cli") / "eval.py"


class TestPersonaEvalParity(unittest.TestCase):
    def test_all_persona_agent_evals_are_identical(self) -> None:
        canonical = (REPO_ROOT / "personas" / "sakthai" / AGENT_EVAL_REL).read_bytes()
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                copy_path = REPO_ROOT / "personas" / persona / AGENT_EVAL_REL
                self.assertTrue(copy_path.is_file(), f"missing {copy_path}")
                self.assertEqual(
                    copy_path.read_bytes(),
                    canonical,
                    f"personas/{persona}/{AGENT_EVAL_REL} has drifted from the "
                    "canonical copy. Sync it (cp from personas/sakthai/) so "
                    "evaluation fixes reach every persona.",
                )

    def test_all_persona_cli_evals_are_identical(self) -> None:
        canonical = (REPO_ROOT / "personas" / "sakthai" / CLI_EVAL_REL).read_bytes()
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                copy_path = REPO_ROOT / "personas" / persona / CLI_EVAL_REL
                self.assertTrue(copy_path.is_file(), f"missing {copy_path}")
                self.assertEqual(
                    copy_path.read_bytes(),
                    canonical,
                    f"personas/{persona}/{CLI_EVAL_REL} has drifted from the "
                    "canonical copy. Sync it (cp from personas/sakthai/) so "
                    "evaluation CLI fixes reach every persona.",
                )


if __name__ == "__main__":
    unittest.main()

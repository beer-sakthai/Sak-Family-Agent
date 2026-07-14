"""Guard against security-guardrail drift across the six persona snapshots.

Each persona under ``personas/`` carries its own copy of the ``sakthai``
package. Security hardening applied to the canonical copy
(``personas/sakthai/sakthai/agent/guardrails.py``) must be synchronized to
every other persona, otherwise a fixed vulnerability silently survives in the
unsynced copies. This test fails CI the moment any copy diverges.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ["sakthai", "sakjules", "sakking", "saksee", "saksit", "saktan"]
GUARDRAILS_REL = Path("sakthai") / "agent" / "guardrails.py"


class TestPersonaGuardrailsParity(unittest.TestCase):
    def test_all_persona_guardrails_are_identical(self):
        canonical_path = REPO_ROOT / "personas" / "sakthai" / GUARDRAILS_REL
        canonical = canonical_path.read_bytes()
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                copy_path = REPO_ROOT / "personas" / persona / GUARDRAILS_REL
                self.assertTrue(copy_path.is_file(), f"missing {copy_path}")
                self.assertEqual(
                    copy_path.read_bytes(),
                    canonical,
                    f"personas/{persona}/{GUARDRAILS_REL} has drifted from the "
                    "canonical copy. Security fixes must be synced to all six "
                    "personas (cp from personas/sakthai/).",
                )


if __name__ == "__main__":
    unittest.main()

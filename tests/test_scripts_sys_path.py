"""Enforce AGENTS.md rule: scripts importing sakthai must insert personas/sakthai into sys.path."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _imports_sakthai(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "sakthai" or alias.name.startswith("sakthai.") for alias in node.names
            ):
                return True
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and (node.module == "sakthai" or node.module.startswith("sakthai."))
        ):
            return True
    return False


class TestScriptsSysPath(unittest.TestCase):
    def test_all_scripts_importing_sakthai_insert_canonical_sys_path(self) -> None:
        script_files = sorted(SCRIPTS_DIR.glob("*.py"))
        self.assertGreater(len(script_files), 0)
        for path in script_files:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            if _imports_sakthai(tree) or "from sakthai" in source or "import sakthai" in source:
                with self.subTest(script=path.name):
                    self.assertIn(
                        "sys.path.insert",
                        source,
                        f"scripts/{path.name} imports sakthai without inserting personas/sakthai into sys.path",
                    )
                    self.assertIn(
                        "personas",
                        source,
                        f"scripts/{path.name} must reference personas/sakthai in its sys.path setup",
                    )


if __name__ == "__main__":
    unittest.main()

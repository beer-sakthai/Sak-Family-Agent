"""Pytest fixtures and path resolution for PatchFlow service tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_sakthai_pkg = str(REPO_ROOT / "personas" / "sakthai")
if _sakthai_pkg not in sys.path:
    sys.path.append(_sakthai_pkg)

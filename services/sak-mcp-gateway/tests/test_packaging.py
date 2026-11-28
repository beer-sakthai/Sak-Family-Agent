"""Tests for M365 Copilot packaging and schema validation."""

from __future__ import annotations

import importlib.util
import tempfile
import zipfile
from pathlib import Path

M365_DIR = Path(__file__).resolve().parent.parent / "microsoft365"
PKG_SCRIPT = M365_DIR / "package_app.py"

_spec = importlib.util.spec_from_file_location("package_app", PKG_SCRIPT)
if not _spec or not _spec.loader:
    raise ImportError(f"Cannot load package_app from {PKG_SCRIPT}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

package_app = _mod.package_app
validate_package = _mod.validate_package


def test_validate_package_passes() -> None:
    warnings = validate_package(M365_DIR, strict=False)
    # Warnings about placeholders in development templates are expected
    placeholder_warnings = [w for w in warnings if "unresolved placeholder" in w]
    assert len(placeholder_warnings) >= 1


def test_package_app_creates_valid_zip() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_zip = Path(tmpdir) / "test-agent.zip"
        package_app(M365_DIR, out_zip, strict=False)
        assert out_zip.is_file()

        with zipfile.ZipFile(out_zip, "r") as zf:
            namelist = zf.namelist()
            assert "manifest.json" in namelist
            assert "declarativeAgent.json" in namelist
            assert "ai-plugin.json" in namelist
            assert "color.png" in namelist
            assert "outline.png" in namelist

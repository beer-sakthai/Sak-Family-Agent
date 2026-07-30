"""Regression tests for SakKing skill output security boundaries."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "personas" / "sakking" / "skills"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_comfyui_output_redacts_credentials(capsys) -> None:
    common = _load_module(
        "sakking_comfyui_common",
        SKILLS_ROOT / "SakKing-comfyui" / "scripts" / "_common.py",
    )

    common.emit_json({"api_key": "comfyui-secret", "message": "Bearer cloud-token"})
    common.log("authorization: Bearer cloud-token")

    captured = capsys.readouterr()
    assert "cloud-token" not in captured.out
    assert "cloud-token" not in captured.err
    assert "comfyui-secret" not in captured.out
    assert "***REDACTED***" in captured.out
    assert "***REDACTED***" in captured.err


def test_maps_output_redacts_precise_location(capsys) -> None:
    maps = _load_module(
        "sakking_maps_client",
        SKILLS_ROOT / "SakKing-maps" / "scripts" / "maps_client.py",
    )

    maps.print_json({"name": "Family cafe", "lat": "13.7563", "lon": "100.5018", "address": "home"})

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "name": "Family cafe",
        "lat": "[REDACTED]",
        "lon": "[REDACTED]",
        "address": "[REDACTED]",
    }


def test_p5js_dependency_has_subresource_integrity() -> None:
    viewer = (SKILLS_ROOT / "SakKing-p5js" / "templates" / "viewer.html").read_text()

    assert 'integrity="sha512-' in viewer
    assert 'crossorigin="anonymous"' in viewer
    assert 'referrerpolicy="no-referrer"' in viewer

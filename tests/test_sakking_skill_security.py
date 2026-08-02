"""Regression tests for SakKing skill output security boundaries."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "personas" / "sakking" / "skills"
SHARED_SKILLS_ROOT = REPO_ROOT / "personas" / "shared" / "skills"
P5_SCRIPT_URL = "https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"
P5_SCRIPT_INTEGRITY = (
    "sha512-I0Pwwz3PPNQkWes+rcSoQqikKFfRmTfGQrcNzZbm8ALaUyJuFdyRinl805shE8xT6iEWsWgv"
    "RxdXb3yhQNXKoA=="
)


class _CredentialDisplay:
    def __str__(self) -> str:
        return "client_secret=object-value"


def test_comfyui_output_redacts_credentials(capsys) -> None:
    common = runpy.run_path(
        str(SKILLS_ROOT / "SakKing-comfyui" / "scripts" / "_common.py"),
        run_name="sakking_comfyui_common",
    )

    common["emit_json"](
        {
            "api_key": "comfyui-secret",
            "access_token": "access-value",
            "clientSecret": "client-value",
            "display": _CredentialDisplay(),
            "message": "Bearer cloud-token",
        }
    )
    common["log"](
        "refresh_token=refresh-value authorization: Bearer cloud-token "
        '{"client_secret":"json-value"}'
    )

    captured = capsys.readouterr()
    assert "cloud-token" not in captured.out
    assert "cloud-token" not in captured.err
    assert "comfyui-secret" not in captured.out
    assert "access-value" not in captured.out
    assert "client-value" not in captured.out
    assert "object-value" not in captured.out
    assert "refresh-value" not in captured.err
    assert "json-value" not in captured.err
    assert "***REDACTED***" in captured.out
    assert "***REDACTED***" in captured.err


def test_maps_output_redacts_precise_location(capsys) -> None:
    maps = runpy.run_path(
        str(SHARED_SKILLS_ROOT / "Sak-maps" / "scripts" / "maps_client.py"),
        run_name="sakking_maps_client",
    )

    maps["print_json"](
        {"name": "Family cafe", "lat": "13.7563", "lon": "100.5018", "address": "home"}
    )

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "name": "Family cafe",
        "lat": "[REDACTED]",
        "lon": "[REDACTED]",
        "address": "[REDACTED]",
    }


def test_p5js_dependency_has_subresource_integrity() -> None:
    viewer = (SKILLS_ROOT / "SakKing-p5js" / "templates" / "viewer.html").read_text()

    expected_script = (
        f'<script src="{P5_SCRIPT_URL}" integrity="{P5_SCRIPT_INTEGRITY}" '
        'crossorigin="anonymous" referrerpolicy="no-referrer"></script>'
    )
    assert viewer.count(P5_SCRIPT_URL) == 1
    assert expected_script in viewer

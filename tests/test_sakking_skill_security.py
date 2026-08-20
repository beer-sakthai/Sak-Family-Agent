"""Regression tests for SakKing skill output security boundaries."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "personas" / "sakking" / "skills"
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
        str(SKILLS_ROOT / "SakKing-maps" / "scripts" / "maps_client.py"),
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


def test_maps_output_redacts_bbox_center_and_url_fields(capsys) -> None:
    """Regression test for a gap an adversarial review caught: cmd_nearby's
    center_lat/center_lon, cmd_bbox's min/max_lat/lon, and the maps_url/
    directions_url fields (which embed raw coordinates as URL query text)
    all bypassed the exact-key redaction until they were added to
    SENSITIVE_OUTPUT_KEYS — the py/clear-text-logging-sensitive-data
    suppression on print_json() is only justified if these are covered too."""
    maps = runpy.run_path(
        str(SKILLS_ROOT / "SakKing-maps" / "scripts" / "maps_client.py"),
        run_name="sakking_maps_client_bbox",
    )

    maps["print_json"](
        {
            "center_lat": 13.7563,
            "center_lon": 100.5018,
            "bounding_box": {
                "min_lat": 13.70,
                "max_lat": 13.80,
                "min_lon": 100.45,
                "max_lon": 100.55,
            },
            "results": [
                {
                    "name": "Family cafe",
                    "maps_url": "https://www.google.com/maps/search/?api=1&query=13.7563,100.5018",
                    "directions_url": (
                        "https://www.google.com/maps/dir/?api=1"
                        "&origin=13.75,100.50&destination=13.7563,100.5018"
                    ),
                }
            ],
        }
    )

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "center_lat": "[REDACTED]",
        "center_lon": "[REDACTED]",
        "bounding_box": {
            "min_lat": "[REDACTED]",
            "max_lat": "[REDACTED]",
            "min_lon": "[REDACTED]",
            "max_lon": "[REDACTED]",
        },
        "results": [
            {
                "name": "Family cafe",
                "maps_url": "[REDACTED]",
                "directions_url": "[REDACTED]",
            }
        ],
    }


def test_p5js_dependency_has_subresource_integrity() -> None:
    viewer = (SKILLS_ROOT / "SakKing-p5js" / "templates" / "viewer.html").read_text()

    expected_script = (
        f'<script src="{P5_SCRIPT_URL}" integrity="{P5_SCRIPT_INTEGRITY}" '
        'crossorigin="anonymous" referrerpolicy="no-referrer"></script>'
    )
    assert viewer.count(P5_SCRIPT_URL) == 1
    assert expected_script in viewer


def test_p5js_dependency_has_subresource_integrity_all_persona_copies() -> None:
    """Every persona's p5js viewer template must carry the same SRI-hardened
    script tag as SakKing's — a missing copy is exactly how CodeQL alert
    #15322 (js/functionality-from-untrusted-source) slipped into SakSee's."""
    viewer_paths = [
        REPO_ROOT
        / "personas"
        / "sakking"
        / "skills"
        / "SakKing-p5js"
        / "templates"
        / "viewer.html",
        REPO_ROOT / "personas" / "saksee" / "skills" / "SakSee-p5js" / "templates" / "viewer.html",
        REPO_ROOT
        / "sakthai-chat-cli"
        / "personas"
        / "sakthai"
        / "skills"
        / "creative"
        / "SakThai-p5js"
        / "templates"
        / "viewer.html",
    ]
    expected_script = (
        f'<script src="{P5_SCRIPT_URL}" integrity="{P5_SCRIPT_INTEGRITY}" '
        'crossorigin="anonymous" referrerpolicy="no-referrer"></script>'
    )
    for path in viewer_paths:
        viewer = path.read_text()
        assert viewer.count(P5_SCRIPT_URL) == 1, path
        assert expected_script in viewer, path

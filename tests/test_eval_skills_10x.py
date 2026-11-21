"""Tests for scripts/eval_skills_10x.py benchmark runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "eval_skills_10x.py"


def test_eval_skills_10x_script_executes(tmp_path: Path) -> None:
    output_html = tmp_path / "report.html"
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--trials",
        "2",
        "--persona",
        "sakking",
        "--output",
        str(output_html),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"Script failed: {proc.stderr}"
    assert "Skills Evaluation Benchmark (2 Trials)" in proc.stdout
    assert "Target:       sakking" in proc.stdout
    assert output_html.is_file()

    html_text = output_html.read_text(encoding="utf-8")
    assert "House of Sak — 10x Skills Evaluation Benchmark" in html_text
    assert "sakking" in html_text
    assert "The 10-Factor Skills Evaluation Rubric Standard" in html_text

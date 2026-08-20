"""Unit tests for scripts/run_eval_loop.py evaluation loop and HTML viewer generator."""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_eval_loop_module(script_rel_path: str):
    script_path = REPO_ROOT / script_rel_path
    spec = importlib.util.spec_from_file_location("run_eval_loop", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["scripts/run_eval_loop.py", "sakthai-chat-cli/scripts/run_eval_loop.py"])
def eval_module(request):
    return _load_eval_loop_module(request.param)


def test_run_evaluation(eval_module):
    results = eval_module.run_evaluation()
    assert "metrics" in results
    assert "cases" in results

    metrics = results["metrics"]
    assert "old_avg_score" in metrics
    assert "new_avg_score" in metrics
    assert "token_savings_pct" in metrics
    assert metrics["new_avg_score"] > metrics["old_avg_score"]
    assert len(results["cases"]) == 4


def test_to_html_formatting(eval_module):
    raw_text = "line1\nline2\\nline3```code```"
    formatted = eval_module._to_html(raw_text)
    assert "<br>" in formatted
    assert "```" not in formatted
    assert formatted == "line1<br>line2<br>line3code"


def test_generate_html_viewer(eval_module, tmp_path):
    results = eval_module.run_evaluation()
    out_file = tmp_path / "review_viewer.html"

    eval_module.generate_html_viewer(results, out_file)

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")

    assert "<!DOCTYPE html>" in content
    assert "Skill Evaluation Review Viewer" in content
    assert "Old Avg Score" in content
    assert "New Avg Score" in content
    assert "Case #1" in content
    assert "Case #4" in content
    assert "switchTab" in content
    assert "OLD_SKILL_BODY" not in content  # checks interpolation worked

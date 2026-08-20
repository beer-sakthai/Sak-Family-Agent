import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root (AGENTS.md convention)

from scripts.eval.compare import compare, load_results, render_report  # noqa: E402


def _results(model, simple=50.0, parallel=40.0, held_out=20.0):
    return {
        "model": model,
        "scores": {
            "categories": {
                "simple": {"count": 10, "strict": simple},
                "parallel": {"count": 10, "strict": parallel},
                "held_out": {"count": 10, "strict": held_out},
            }
        },
    }


def test_load_results_requires_scores(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text("model: x\n")
    with pytest.raises(ValueError, match="scores"):
        load_results(p)


def test_compare_marks_pass_regression_improved():
    targets = {"simple": 60.0, "parallel": 60.0, "held_out": 40.0}
    rows = compare(_results("old", 50.0, 40.0, 20.0), _results("new", 70.0, 30.0, 45.0), targets)
    by = {r["category"]: r for r in rows}
    assert by["simple"]["status"] == "pass"
    assert by["parallel"]["status"] == "regression"
    assert by["held_out"]["status"] == "pass"


def test_render_report_is_markdown_table():
    text = render_report(
        compare(_results("old"), _results("new", 70.0, 40.0, 20.0), {"simple": 60.0}),
        ("old", "new"),
    )
    assert "| Category |" in text
    assert "| simple |" in text
    assert "70.0" in text

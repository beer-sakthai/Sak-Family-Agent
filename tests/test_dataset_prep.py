import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root (AGENTS.md convention)

from scripts.dataset_prep.build_v12 import (  # noqa: E402
    build_v12,
    category_report,
    load_jsonl,
    strip_tags,
    synthesize_held_out,
    synthesize_parallel,
    synthesize_simple,
    validate_balance,
)


def _row(category="source"):
    return {
        "messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        "tools": [
            {"name": "get_time", "description": "returns time", "parameters": {"type": "object"}}
        ],
        "_category": category,
    }


def test_load_jsonl_reads_rows_and_raises_on_bad_json(tmp_path):
    p = tmp_path / "rows.jsonl"
    p.write_text(json.dumps(_row()) + "\nnot-json\n")
    with pytest.raises(ValueError):
        load_jsonl(p)


def test_strip_tags_removes_category():
    rows = strip_tags([_row("simple")])
    assert "_category" not in rows[0]
    assert "messages" in rows[0] and "tools" in rows[0]


def test_synthesize_simple_has_one_tool_call():
    row = synthesize_simple("weather")
    assert row["_category"] == "simple"
    assert len(row["tools"]) == 1
    assert row["messages"][-1]["role"] == "assistant"
    assert "get_weather" in row["messages"][-1]["content"]


def test_synthesize_parallel_invokes_all_tools():
    tools = [
        {"name": "get_temp", "description": "t", "parameters": {"type": "object"}},
        {"name": "get_wind", "description": "w", "parameters": {"type": "object"}},
    ]
    row = synthesize_parallel(["Bangkok", "Chiang Mai"], tools)
    assert row["_category"] == "parallel"
    assert len(row["tools"]) == 2
    assert "get_temp" in row["messages"][-1]["content"]
    assert "get_wind" in row["messages"][-1]["content"]


def test_synthesize_held_out_declines_missing_tools():
    tools = [{"name": "get_time", "description": "t", "parameters": {"type": "object"}}]
    row = synthesize_held_out(tools)
    assert row["_category"] == "held_out"
    assert "get_time" not in row["messages"][-1]["content"]
    assert "cannot" in row["messages"][-1]["content"].lower()


def test_category_report_counts():
    rows = [_row("simple"), _row("simple"), _row("held_out"), _row("source")]
    assert category_report(rows) == {"simple": 2, "held_out": 1, "source": 1}


def test_validate_balance_raises_below_minimum():
    with pytest.raises(ValueError, match="simple"):
        validate_balance([_row("simple")], {"simple": 2})


def test_build_v12_writes_stripped_rows_and_report(tmp_path):
    src = tmp_path / "src.jsonl"
    src.write_text(json.dumps(_row("source")) + "\n")
    out = tmp_path / "v12.jsonl"
    report = tmp_path / "report.json"
    build_v12([src], out, report, min_counts={"simple": 1})
    lines = out.read_text().splitlines()
    assert len(lines) == 2
    assert "_category" not in json.loads(lines[0])
    assert json.loads(report.read_text())["simple"] >= 1

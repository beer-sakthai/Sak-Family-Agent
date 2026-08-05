import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root (AGENTS.md convention)

from scripts.eval.run_bench import (  # noqa: E402
    aggregate,
    parse_tool_calls,
    render_yaml,
    run_bench,
    score_sample,
)


def test_parse_tool_calls_extracts_named_calls():
    text = 'Sure! <tool_call>{"name": "get_weather", "arguments": {"city": "BKK"}}</tool_call> done'
    calls = parse_tool_calls(text)
    assert calls == [{"name": "get_weather", "arguments": {"city": "BKK"}}]


def test_parse_tool_calls_tolerates_function_key():
    text = '{"function": {"name": "f1", "arguments": {"a": 1}}}'
    assert parse_tool_calls(text) == [{"name": "f1", "arguments": {"a": 1}}]


def test_score_sample_selection_requires_exact_names():
    expected = [{"name": "a", "arguments": {}}]
    assert score_sample('{"name": "a", "arguments": {}}', expected) == (True, True)
    assert score_sample('{"name": "b", "arguments": {}}', expected) == (False, False)


def test_score_sample_accepts_string_tool_names():
    expected = ["get_weather"]
    assert score_sample('{"name": "get_weather", "arguments": {}}', expected) == (True, True)
    assert score_sample('{"name": "get_other", "arguments": {}}', expected) == (False, False)


def test_score_sample_arguments_must_match():
    expected = [{"name": "a", "arguments": {"city": "BKK"}}]
    assert score_sample('{"name": "a", "arguments": {"city": "BKK"}}', expected) == (True, True)
    assert score_sample('{"name": "a", "arguments": {"city": "NYC"}}', expected) == (True, False)


def test_aggregate_counts_and_weights():
    rows = [
        {"category": "simple", "selection": True, "arguments": True},
        {"category": "simple", "selection": False, "arguments": False},
        {"category": "parallel", "selection": True, "arguments": True},
    ]
    agg = aggregate(rows)
    assert agg["categories"]["simple"]["strict"] == 50.0
    assert agg["categories"]["parallel"]["strict"] == 100.0
    assert agg["overall"]["strict"] == round((1 + 1) / 3 * 100, 2)


def test_aggregate_counts_irrelevance_category():
    rows = [{"category": "irrelevance", "selection": True, "arguments": True}]
    agg = aggregate(rows)
    assert agg["categories"]["irrelevance"]["count"] == 1
    assert agg["unknown_count"] == 0


def test_render_yaml_matches_eval_results_schema():
    agg = aggregate([{"category": "simple", "selection": True, "arguments": True}])
    text = render_yaml(
        agg,
        model="Nanthasit/x-r2",
        benchmark="sakthai-bench-v3",
        run_id="20260805_000000",
        status="completed",
        summary="ok",
    )
    doc = yaml_safe_load(text)
    assert doc["model"] == "Nanthasit/x-r2"
    assert doc["scores"]["categories"]["simple"]["count"] == 1
    assert doc["status"] == "completed"


def yaml_safe_load(text):
    import yaml

    return yaml.safe_load(text)


def test_run_bench_injects_predictor():
    def predict(messages, tools):
        return '{"name": "a", "arguments": {}}'

    rows = [
        {
            "messages": [],
            "tools": [],
            "expected_tools": [{"name": "a", "arguments": {}}],
            "category": "simple",
        }
    ]
    results = run_bench(rows, predict)
    assert results[0]["selection"] is True

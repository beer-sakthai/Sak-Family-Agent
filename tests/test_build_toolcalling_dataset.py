"""Unit tests for dataset build row generators in training/hf-jobs/build_toolcalling_dataset.py."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

# Load module dynamically because directory name 'hf-jobs' contains a hyphen
MODULE_PATH = Path(__file__).resolve().parents[1] / "training" / "hf-jobs" / "build_toolcalling_dataset.py"
spec = importlib.util.spec_from_file_location("build_toolcalling_dataset", MODULE_PATH)
assert spec is not None and spec.loader is not None
build_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_module)


def test_generate_tool_rows_helper() -> None:
    templates = ["Do {item}", "Please {item}"]
    items = ["task_a", "task_b"]
    arg_builder = lambda item: {"item_name": item}

    rows = list(build_module.generate_tool_rows("dummy_tool", templates, items, arg_builder, sample_size=1))

    assert len(rows) == len(items)
    for user_text, tool_name, args in rows:
        assert tool_name == "dummy_tool"
        assert "item_name" in args
        assert args["item_name"] in items
        assert any(tmpl.format(item=args["item_name"]) == user_text for tmpl in templates)


def test_learn_rows() -> None:
    rows = list(build_module.learn_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["learn"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "learn"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["value"], str)
        assert isinstance(args["kind"], str)
        assert isinstance(args["key"], str)


def test_recall_rows() -> None:
    rows = list(build_module.recall_rows())
    assert len(rows) > 0

    for user_text, tool_name, args in rows:
        assert tool_name == "recall"
        assert isinstance(user_text, str) and len(user_text) > 0
        if "limit" in args:
            assert isinstance(args["limit"], int)
            assert args["limit"] > 0


def test_search_rows() -> None:
    rows = list(build_module.search_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["search"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "search"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["query"], str)
        assert args["query"] in build_module.SEARCH_TOPICS


def test_forget_rows() -> None:
    rows = list(build_module.forget_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["forget"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "forget"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["fact_id"], int)


def test_read_file_rows() -> None:
    rows = list(build_module.read_file_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["read_file"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "read_file"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["path"], str)
        assert args["path"] in build_module.FILES


def test_run_command_rows() -> None:
    rows = list(build_module.run_command_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["run_command"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "run_command"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["command"], str)
        assert args["command"] in build_module.COMMANDS
        if "timeout" in args:
            assert isinstance(args["timeout"], (int, float))


def test_telegram_rows() -> None:
    rows = list(build_module.telegram_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["send_telegram_message"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "send_telegram_message"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["message"], str)
        assert args["message"] in build_module.TG_MSGS


def test_agent_loop_rows() -> None:
    rows = list(build_module.agent_loop_rows())
    assert len(rows) > 0

    tool_def = build_module.TOOL_MAP["run_agent_loop"]
    required_params = tool_def["function"]["parameters"]["required"]

    for user_text, tool_name, args in rows:
        assert tool_name == "run_agent_loop"
        assert isinstance(user_text, str) and len(user_text) > 0
        for param in required_params:
            assert param in args
        assert isinstance(args["task"], str)
        assert args["task"] in build_module.BIG_TASKS
        if "max_iterations" in args:
            assert isinstance(args["max_iterations"], int)


def test_build() -> None:
    dataset = build_module.build()
    assert len(dataset) > 0

    negatives_count = len(build_module.NEGATIVES)
    tool_calls_count = len(dataset) - negatives_count
    assert tool_calls_count > 0

    found_tool_calls = 0
    found_no_tool_calls = 0

    for row in dataset:
        # JSON serializable check
        json_str = json.dumps(row, ensure_ascii=False)
        assert isinstance(json_str, str)

        assert "tools" in row
        assert row["tools"] == build_module.TOOLS

        assert "messages" in row
        messages = row["messages"]
        assert len(messages) == 3

        # Message 1: system
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == build_module.SYSTEM_PROMPT

        # Message 2: user
        assert messages[1]["role"] == "user"
        assert isinstance(messages[1]["content"], str) and len(messages[1]["content"]) > 0

        # Message 3: assistant
        assert messages[2]["role"] == "assistant"
        assert "tool_calls" in messages[2]

        tool_calls = messages[2]["tool_calls"]
        if len(tool_calls) > 0:
            found_tool_calls += 1
            assert messages[2]["content"] == ""
            assert len(tool_calls) == 1
            call = tool_calls[0]
            assert call["type"] == "function"
            fn = call["function"]
            assert fn["name"] in build_module.TOOL_MAP
            assert isinstance(fn["arguments"], dict)

            # Schema required params check
            req = build_module.TOOL_MAP[fn["name"]]["function"]["parameters"].get("required", [])
            for r in req:
                assert r in fn["arguments"]
        else:
            found_no_tool_calls += 1
            assert isinstance(messages[2]["content"], str) and len(messages[2]["content"]) > 0

    assert found_no_tool_calls == negatives_count
    assert found_tool_calls == tool_calls_count

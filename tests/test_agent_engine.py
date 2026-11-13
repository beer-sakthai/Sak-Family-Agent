import dataclasses

import pytest

from app.agent_platform.agent_engine import (
    AgentEngineMode,
    UnifiedAgentConfig,
    UnifiedAgentRuntime,
)
from app.agent_platform.safety import DataLossGuardrail


def sample_add_tool(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def sample_destructive_tool(table_name: str) -> str:
    """Execute drop table."""
    return f"DROP TABLE {table_name};"


def sample_failing_tool(msg: str) -> str:
    """Raise an error intentionally."""
    raise ValueError(f"Failure: {msg}")


def test_runtime_registers_and_executes_safe_tool():
    config = UnifiedAgentConfig(
        name="calculator_agent",
        engine=AgentEngineMode.ANTIGRAVITY,
        model="gemini-2.5-flash",
    )
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("add", sample_add_tool)

    result = runtime.execute_tool("add", {"a": 10, "b": 32})
    assert result["status"] == "success"
    assert result["output"] == 42


def test_runtime_intercepts_destructive_tool_execution():
    guard = DataLossGuardrail()
    config = UnifiedAgentConfig(
        name="db_agent",
        engine=AgentEngineMode.ADK,
        model="gemini-3.7-flash",
    )
    runtime = UnifiedAgentRuntime(config=config, guardrail=guard)
    runtime.register_tool("drop_table", sample_destructive_tool)

    result = runtime.execute_tool("drop_table", {"table_name": "users"})
    assert result["status"] == "blocked"
    assert "Destructive database operation" in result["reason"]
    assert "impact" in result


def test_runtime_tracks_execution_history():
    config = UnifiedAgentConfig(
        name="history_agent",
        engine=AgentEngineMode.ANTIGRAVITY,
        model="gemini-2.5-flash",
    )
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("add", sample_add_tool)
    runtime.execute_tool("add", {"a": 2, "b": 3})

    assert len(runtime.history) == 1
    assert runtime.history[0]["tool"] == "add"
    assert runtime.history[0]["arguments"] == {"a": 2, "b": 3}
    assert runtime.history[0]["status"] == "success"
    assert runtime.history[0]["output"] == 5


def test_runtime_allows_destructive_tool_with_valid_approval_token():
    guard = DataLossGuardrail()
    config = UnifiedAgentConfig(
        name="authorized_db_agent",
        engine=AgentEngineMode.ADK,
        model="gemini-3.7-flash",
    )
    runtime = UnifiedAgentRuntime(config=config, guardrail=guard)
    runtime.register_tool("drop_table", sample_destructive_tool)

    expected_output = "DROP TABLE audit_logs;"
    token = guard.generate_approval_token(expected_output)

    result = runtime.execute_tool("drop_table", {"table_name": "audit_logs"}, approval_token=token)
    assert result["status"] == "success"
    assert result["output"] == expected_output
    assert len(runtime.history) == 1
    assert runtime.history[0]["status"] == "success"


def test_runtime_handles_unregistered_tool():
    config = UnifiedAgentConfig(name="test_agent")
    runtime = UnifiedAgentRuntime(config=config)

    result = runtime.execute_tool("unknown_tool", {"x": 1})
    assert result["status"] == "error"
    assert "Tool 'unknown_tool' not registered" in result["error"]
    assert len(runtime.history) == 0


def test_runtime_handles_tool_exception():
    config = UnifiedAgentConfig(name="error_agent")
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("fail", sample_failing_tool)

    result = runtime.execute_tool("fail", {"msg": "invalid param"})
    assert result["status"] == "error"
    assert "Failure: invalid param" in result["error"]
    assert len(runtime.history) == 1
    assert runtime.history[0]["status"] == "error"


def test_unified_agent_config_defaults():
    config = UnifiedAgentConfig(name="default_agent")
    assert config.name == "default_agent"
    assert config.engine == AgentEngineMode.ANTIGRAVITY
    assert config.model == "gemini-2.5-flash"
    assert config.max_turns == 150
    assert config.instruction == "You are an autonomous AI pair programming agent."


def test_unified_agent_runtime_default_guardrail():
    config = UnifiedAgentConfig(name="default_guard_agent")
    runtime = UnifiedAgentRuntime(config=config)
    assert isinstance(runtime.guardrail, DataLossGuardrail)


def test_runtime_pre_execution_intercepts_destructive_arguments():
    executed = False

    def execute_sql(query: str) -> str:
        nonlocal executed
        executed = True
        return "Query executed successfully"

    guard = DataLossGuardrail()
    config = UnifiedAgentConfig(
        name="sql_agent",
        engine=AgentEngineMode.ANTIGRAVITY,
    )
    runtime = UnifiedAgentRuntime(config=config, guardrail=guard)
    runtime.register_tool("execute_sql", execute_sql)

    args = {"query": "DROP TABLE users;"}
    result = runtime.execute_tool("execute_sql", args)

    assert result["status"] == "blocked"
    assert "Destructive database operation (DROP)" in result["reason"]
    assert executed is False, (
        "Tool function must not be executed when arguments contain destructive payload"
    )
    assert len(runtime.history) == 1
    assert runtime.history[0]["status"] == "blocked"
    assert runtime.history[0]["arguments"] == {"query": "DROP TABLE users;"}


def test_runtime_history_arguments_immutability():
    config = UnifiedAgentConfig(name="immutability_agent")
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("add", sample_add_tool)

    args = {"a": 10, "b": 20}
    result = runtime.execute_tool("add", args)
    assert result["status"] == "success"

    # Mutate caller dict
    args["a"] = 999
    assert runtime.history[0]["arguments"]["a"] == 10


def test_unified_agent_config_frozen():
    config = UnifiedAgentConfig(name="frozen_agent")
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.name = "new_name"  # type: ignore

from sakthai.agent_platform.agent_engine import (
    AgentEngineMode,
    UnifiedAgentConfig,
    UnifiedAgentRuntime,
)
from sakthai.agent_platform.safety import DataLossGuardrail


def sample_add_tool(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def sample_destructive_tool(table_name: str) -> str:
    """Execute drop table."""
    return f"DROP TABLE {table_name};"


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


def test_runtime_unregistered_tool():
    config = UnifiedAgentConfig(name="test_agent")
    runtime = UnifiedAgentRuntime(config=config)
    result = runtime.execute_tool("nonexistent", {})
    assert result["status"] == "error"
    assert "not registered" in result["error"]


def test_runtime_tool_exception_handling():
    def failing_tool():
        raise RuntimeError("Tool execution failed internally")

    config = UnifiedAgentConfig(name="test_agent")
    runtime = UnifiedAgentRuntime(config=config)
    runtime.register_tool("failing", failing_tool)
    result = runtime.execute_tool("failing", {})
    assert result["status"] == "error"
    assert "Tool execution failed internally" in result["error"]

"""Integration tests for the agent loop (sakthai.agent.loop)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.loop import run_agent
from sakthai.agent.providers import AgentError, Block, Response
from sakthai.agent.tools import BUILTIN_TOOLS, Tool


class MockProvider:
    """A mock provider that returns canned responses."""

    def __init__(self, responses: list[Response]):
        self.responses = responses
        self._call_count = 0
        self.requests: list[list[Block]] = []

    def __call__(self, *args, **kwargs) -> Response:
        if self._call_count >= len(self.responses):
            raise AssertionError("MockProvider received more calls than expected.")

        # Record the message history for inspection
        self.requests.append(kwargs.get("messages", []))

        response = self.responses[self.call_count]
        self.call_count += 1

        if isinstance(response, Exception):
            raise response

        return response

    @property
    def call_count(self) -> int:
        return self._call_count


@pytest.fixture
def mock_tool():
    """A simple mock tool for testing."""
    handler = MagicMock(return_value="tool output")
    return Tool(
        name="mock_tool",
        description="A mock tool.",
        input_schema={"type": "object", "properties": {"arg": {"type": "string"}}},
        handler=handler,
    )


@pytest.fixture
def memory_store(tmp_path):
    """Provides an empty, isolated MemoryStore."""
    from sakthai.memory.store import MemoryStore

    with MemoryStore(tmp_path / "memory.db") as store:
        yield store


def test_run_agent_simple_text_response(memory_store, mock_tool, caplog):
    """Test that the agent loop correctly handles a simple text response."""
    result = run_agent(
        task="Test task",
        client=MagicMock(),
        store=memory_store,
        tools=[mock_tool],
        provider="anthropic",  # provider must be specified for client build
    )

    assert result.stop_reason == "stop"
    assert result.output == "Final answer."
    assert result.iterations == 1
    assert not result.tool_calls
    # This test now uses the real provider call path, so we can't assert call count on a mock.


@patch("sakthai.agent.loop._call_anthropic")
def test_run_agent_single_tool_call(mock_call_anthropic, memory_store, mock_tool):
    """Test the agent loop with a single tool call."""
    tool_use_block = Block("tool_use", id="call1", name="mock_tool", input={"arg": "value"})
    mock_call_anthropic.side_effect = [
        Response("tool_use", [tool_use_block]),
        Response("end_turn", [Block("text", text="OK, tool output was 'tool output'.")]),
    ]

    result = run_agent(
        task="Use the mock tool.",
        client=MagicMock(),
        store=memory_store,
        tools=[mock_tool],
        provider="anthropic",
    )

    assert result.stop_reason == "stop"
    assert result.output == "OK, tool output was 'tool output'."
    assert result.iterations == 2
    assert len(result.tool_calls) == 1
    assert mock_call_anthropic.call_count == 2
    mock_tool.handler.assert_called_once_with(arg="value")

    # Check that the tool result was passed back to the model
    last_request_messages = mock_call_anthropic.call_args.kwargs["messages"]
    tool_result_message = next((m for m in last_request_messages if m.get("role") == "tool"), None)
    assert tool_result_message is not None
    assert tool_result_message["content"][0]["tool_use_id"] == "call1"
    assert tool_result_message["content"][0]["content"] == "tool output"


@patch("sakthai.agent.loop._call_anthropic")
def test_run_agent_max_iterations(mock_call_anthropic, memory_store, mock_tool):
    """Test that the agent loop respects the max_iterations limit."""
    # Simulate a loop where the model keeps trying to use the tool
    tool_use_block = Block("tool_use", id="call1", name="mock_tool", input={"arg": "value"})
    tool_response = Response("tool_use", [tool_use_block])
    mock_call_anthropic.side_effect = [tool_response, tool_response, tool_response]

    with pytest.raises(AgentError, match="Agent hit the iteration cap"):
        run_agent(
            task="Test task",
            client=MagicMock(),
            store=memory_store,
            tools=[mock_tool],
            max_iterations=2,
            provider="anthropic",
        )

    assert mock_call_anthropic.call_count == 2
    assert mock_tool.handler.call_count == 2


@patch("sakthai.agent.loop._call_anthropic")
def test_run_agent_provider_error(mock_call_anthropic, memory_store, mock_tool):
    """Test that the agent loop propagates errors from the provider."""
    mock_call_anthropic.side_effect = AgentError("API is down")

    with pytest.raises(AgentError, match="API is down"):
        run_agent(
            task="Test task",
            client=MagicMock(),
            store=memory_store,
            tools=[mock_tool],
            provider="anthropic",
        )


@patch("sakthai.agent.loop.uuid4")
def test_run_agent_logs_session(mock_uuid, memory_store, mock_tool, tmp_path):
    """Test that a session log is written to the configured directory."""
    mock_uuid.return_value.hex = "testsession"
    sessions_dir_path = tmp_path / "sessions"
    sessions_dir_path.mkdir()

    with (
        patch("sakthai.config.sessions_dir", return_value=sessions_dir_path),
        patch(
            "sakthai.agent.loop._call_anthropic",
            return_value=Response("end_turn", [Block("text", text="Done.")]),
        ),
    ):
        run_agent(
            task="Test task",
            client=MagicMock(),
            store=memory_store,
            tools=[mock_tool],
            provider="anthropic",
        )

    session_file = (
        sessions_dir_path
        / f"{int(list(mock_uuid.return_value.fields)[0])}_{mock_uuid.return_value.hex}.json"
    )
    assert session_file.exists()
    assert '"task": "Test task"' in session_file.read_text()
    assert '"output": "Done."' in session_file.read_text()


class TestAgentTurn:
    """Unit tests for the _agent_turn helper function."""

    @pytest.fixture
    def common_args(self):
        """Provide common arguments for _agent_turn calls."""
        from sakthai.agent.usage import UsageTracker

        return {
            "client": MagicMock(),
            "model": "test-model",
            "system": "test-system",
            "tools": BUILTIN_TOOLS,
            "messages": [{"role": "user", "content": "test"}],
            "iteration": 1,
            "on_token": None,
            "max_tokens": 1024,
            "tool_schemas": [],
            "usage_tracker": MagicMock(spec=UsageTracker),
        }

    @patch("sakthai.agent.loop._call_gemini")
    def test_agent_turn_google(self, mock_call_gemini, common_args):
        """Test that _agent_turn dispatches to _call_gemini for the 'google' provider."""
        from sakthai.agent.loop import _agent_turn

        mock_response = MagicMock()
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_call_gemini.return_value = mock_response

        response = _agent_turn(provider="google", **common_args)

        assert response is mock_response
        mock_call_gemini.assert_called_once()
        common_args["usage_tracker"].record.assert_called_once_with(
            input_tokens=10, output_tokens=5
        )

    @patch("sakthai.agent.loop._call_openai_compat")
    def test_agent_turn_openai(self, mock_call_openai, common_args):
        """Test that _agent_turn dispatches to _call_openai_compat for 'openai'."""
        from sakthai.agent.loop import _agent_turn

        mock_response = MagicMock()
        mock_response.usage = {"input_tokens": 20, "output_tokens": 15}
        mock_call_openai.return_value = mock_response

        response = _agent_turn(provider="openai", **common_args)

        assert response is mock_response
        mock_call_openai.assert_called_once()
        common_args["usage_tracker"].record.assert_called_once_with(
            input_tokens=20, output_tokens=15
        )

    @patch("sakthai.agent.loop._call_anthropic")
    @patch("sakthai.agent.loop.extract_usage")
    def test_agent_turn_anthropic(self, mock_extract_usage, mock_call_anthropic, common_args):
        """Test that _agent_turn dispatches to _call_anthropic for other providers."""
        from sakthai.agent.loop import _agent_turn

        mock_response = MagicMock()
        mock_call_anthropic.return_value = mock_response
        mock_extract_usage.return_value = {"input_tokens": 30, "output_tokens": 25}

        response = _agent_turn(provider="anthropic", **common_args)

        assert response is mock_response
        mock_call_anthropic.assert_called_once()
        mock_extract_usage.assert_called_once_with(mock_response)
        common_args["usage_tracker"].record.assert_called_once_with(
            input_tokens=30, output_tokens=25
        )

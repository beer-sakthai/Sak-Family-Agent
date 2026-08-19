from unittest.mock import MagicMock, patch

import pytest
from teams_copilot_mcp import server


def test_resolve_path_fills_placeholders():
    result = server._resolve_path("/teams/{team_id}/channels/{channel_id}", {"team_id": "T1", "channel_id": "C1"})
    assert result == "/teams/T1/channels/C1"


def test_resolve_path_raises_on_missing_param():
    with pytest.raises(ValueError, match="channel_id"):
        server._resolve_path("/teams/{team_id}/channels/{channel_id}", {"team_id": "T1"})


def test_resolve_path_raises_on_control_characters():
    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server._resolve_path("/teams/{team_id}/channels/{channel_id}", {"team_id": "T1\n", "channel_id": "C1"})

    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server._resolve_path("/teams/{team_id}/channels/{channel_id}", {"team_id": "T1", "channel_id": "C1\r\n"})


def test_execute_action_raises_on_unknown_id():
    with pytest.raises(ValueError, match="does_not_exist"):
        server.execute_action(action_id="does_not_exist")


def test_execute_action_gates_delegated_auth_actions():
    with pytest.raises(NotImplementedError, match="delegated"):
        server.execute_action(action_id="copilot_retrieval_query")


def test_execute_action_dispatches_to_graph_client():
    fake_client = MagicMock()
    fake_client.request.return_value = {"id": "chan-1"}

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        result = server.execute_action(
            action_id="list_channels",
            path_params={"team_id": "T1"},
        )

    fake_client.request.assert_called_once_with(
        "GET", "/teams/T1/channels", params=None, json_body=None
    )
    assert result == {"id": "chan-1"}


def test_execute_raw_passes_through_to_graph_client():
    fake_client = MagicMock()
    fake_client.request.return_value = {"ok": True}

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        result = server.execute_raw(
            method="POST", path="/custom/path", query_params={"$top": 5}, body={"a": 1}
        )

    fake_client.request.assert_called_once_with(
        "POST", "/custom/path", params={"$top": 5}, json_body={"a": 1}
    )
    assert result == {"ok": True}


def test_send_channel_message_builds_body():
    fake_client = MagicMock()
    fake_client.request.return_value = {}

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        server.send_channel_message(team_id="T1", channel_id="C1", content="hello")

    fake_client.request.assert_called_once_with(
        "POST",
        "/teams/T1/channels/C1/messages",
        json_body={"body": {"content": "hello"}},
    )


def test_list_calendar_events_builds_query_params():
    fake_client = MagicMock()
    fake_client.request.return_value = {"value": []}

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        server.list_calendar_events(user_id="u1", top=10)

    fake_client.request.assert_called_once_with(
        "GET",
        "/users/u1/calendar/events",
        params={"$top": 10, "$orderby": "start/dateTime"},
    )


def test_copilot_retrieval_query_tool_never_calls_graph_client():
    fake_client = MagicMock()

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        with pytest.raises(NotImplementedError):
            server.copilot_retrieval_query(query_text="find docs", data_source="sharePoint")

    assert fake_client.request.call_count == 0


def test_search_actions_result_includes_delegated_auth_flag():
    results = server.search_actions("copilot")
    entry = next(r for r in results if r["id"] == "copilot_retrieval_query")
    assert entry["requires_delegated_auth"] is True


def test_list_channels_calls_graph_client():
    fake_client = MagicMock()
    fake_client.request.return_value = {"value": []}

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        server.list_channels(team_id="T1")

    fake_client.request.assert_called_once_with("GET", "/teams/T1/channels")


def test_get_meeting_transcript_calls_graph_client():
    fake_client = MagicMock()
    fake_client.request.return_value = "WEBVTT\n..."

    with patch("teams_copilot_mcp.server.get_client", return_value=fake_client):
        result = server.get_meeting_transcript(
            user_id="u1", meeting_id="m1", transcript_id="t1"
        )

    fake_client.request.assert_called_once_with(
        "GET", "/users/u1/onlineMeetings/m1/transcripts/t1/content"
    )
    assert result == "WEBVTT\n..."


def test_main_runs_mcp_server():
    with patch.object(server.mcp, "run") as mock_run:
        server.main()
        mock_run.assert_called_once()
def test_convenience_tools_reject_control_characters():
    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server.list_channels(team_id="T1\r\n")

    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server.send_channel_message(team_id="T1", channel_id="C1\n", content="hi")

    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server.list_calendar_events(user_id="u1\x00")

    with pytest.raises(ValueError, match="Control characters are not allowed"):
        server.get_meeting_transcript(user_id="u1", meeting_id="m1\t", transcript_id="t1")

"""Unit tests for Multi-Agent Session Gateway, Telegram dispatcher, and REST API."""

from __future__ import annotations

import json

from sakthai.agent.session_gateway import (
    GatewaySession,
    SessionManager,
)
from sakthai.telegram.gateway_bot import TelegramGatewayDispatcher
from sakthai.web.gateway_api import GatewayApiHandler


def test_gateway_session_basic_lifecycle() -> None:
    session = GatewaySession("test_session_1", initial_persona="sakthai")
    assert session.active_persona == "sakthai"
    assert len(session.turns) == 0

    route = session.add_user_message("Can you review my python code?")
    assert route.selected_persona == "sakthai"
    assert len(session.turns) == 1
    assert session.turns[0].role == "user"

    msg = session.add_assistant_response("Code reviewed successfully.")
    assert len(session.turns) == 2
    assert msg.role == "assistant"
    assert msg.persona == "sakthai"
    assert session.charge_levels["sakthai"] == 95


def test_gateway_session_auto_handoff() -> None:
    session = GatewaySession("test_session_2", initial_persona="sakthai")

    # Asking for slides switches to saksee
    route = session.add_user_message("Generate a PowerPoint presentation deck with slides.")
    assert route.selected_persona == "saksee"
    assert session.active_persona == "saksee"
    assert len(session.handoff_history) == 1
    assert session.handoff_history[0].from_persona == "sakthai"
    assert session.handoff_history[0].to_persona == "saksee"


def test_gateway_session_sliding_window() -> None:
    session = GatewaySession("test_session_3", max_turns=4)
    for i in range(10):
        session.add_user_message(f"Message {i}")
    assert len(session.turns) == 4
    assert session.turns[-1].content == "Message 9"


def test_gateway_session_recharge() -> None:
    session = GatewaySession("test_session_4")
    session.charge_levels["sakthai"] = 30
    session.recharge_all(50)
    assert session.charge_levels["sakthai"] == 80


def test_session_manager_thread_safety_and_ttl() -> None:
    manager = SessionManager(ttl_seconds=100)
    s1 = manager.get_or_create("sess_1")
    s2 = manager.get_or_create("sess_2")

    assert manager.get("sess_1") is s1
    assert manager.get("sess_2") is s2
    assert "sess_1" in manager.list_sessions()
    assert "sess_2" in manager.list_sessions()

    assert manager.delete("sess_1") is True
    assert manager.get("sess_1") is None


def test_telegram_gateway_dispatcher_commands() -> None:
    dispatcher = TelegramGatewayDispatcher()

    # /start
    resp, persona, meta = dispatcher.handle_message(12345, "/start")
    assert "Sak-Family Multi-Agent Gateway" in resp
    assert persona == "gateway"

    # /persona
    resp, persona, meta = dispatcher.handle_message(12345, "/persona sakjules")
    assert "Switched active persona to @sakjules" in resp
    assert persona == "sakjules"

    # /status
    resp, persona, meta = dispatcher.handle_message(12345, "/status")
    assert "Sak-Family Persona Charge Status" in resp
    assert "@sakjules" in resp

    # /help
    resp, persona, meta = dispatcher.handle_message(12345, "/help")
    assert "Gateway Commands:" in resp

    # Normal message
    resp, persona, meta = dispatcher.handle_message(12345, "Write a marketing newsletter")
    assert persona == "saksit"
    assert "**SakSit" in resp

    # /reset
    resp, persona, meta = dispatcher.handle_message(12345, "/reset")
    assert "Session memory reset" in resp


def test_gateway_api_handler_chat_and_sessions() -> None:
    api = GatewayApiHandler()

    # Bad request
    status, headers, body = api.handle_chat_request({})
    assert status == 400
    assert "Missing or empty" in body

    # Successful chat request
    status, headers, body = api.handle_chat_request(
        {
            "session_id": "web_user_1",
            "message": "Fix the failing CI docker build pipeline",
        }
    )
    assert status == 200
    data = json.loads(body)
    assert data["success"] is True
    assert data["persona"] == "sakjules"
    assert data["intent"]["category"] == "automation_ci"
    assert "**SakJules" in data["reply"]

    # Sessions endpoint
    status, headers, body = api.handle_sessions_request()
    assert status == 200
    sessions_data = json.loads(body)
    assert len(sessions_data["sessions"]) >= 1
    assert any(s["session_id"] == "web_user_1" for s in sessions_data["sessions"])

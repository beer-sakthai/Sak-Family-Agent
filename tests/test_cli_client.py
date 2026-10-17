"""Unit tests for 'sakthai client' CLI command group."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sakthai.agent.loop import AgentResult
from sakthai.cli import main
from sakthai.client import ClientConfig, save_client


def test_cli_client_list_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))
    runner = CliRunner()
    res = runner.invoke(main, ["client", "list"])
    assert res.exit_code == 0
    assert "No clients provisioned yet" in res.output


def test_cli_client_list_and_show(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))
    cfg = ClientConfig(
        client_id="acme-solar",
        company_name="Acme Solar Inc",
        currency="USD",
        port=8085,
    )
    save_client(cfg)

    runner = CliRunner()

    # List Table
    res = runner.invoke(main, ["client", "list"])
    assert res.exit_code == 0
    assert "acme-solar" in res.output
    assert "Acme Solar Inc" in res.output

    # List JSON
    res_json = runner.invoke(main, ["client", "list", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert len(data) == 1
    assert data[0]["client_id"] == "acme-solar"

    # Show text
    res_show = runner.invoke(main, ["client", "show", "acme-solar"])
    assert res_show.exit_code == 0
    assert "Client Workspace:" in res_show.output
    assert "Acme Solar Inc" in res_show.output

    # Show JSON
    res_show_json = runner.invoke(main, ["client", "show", "acme-solar", "--json"])
    assert res_show_json.exit_code == 0
    show_data = json.loads(res_show_json.output)
    assert show_data["client_id"] == "acme-solar"
    assert "workspace_dir" in show_data


def test_cli_client_onboard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients_dir = tmp_path / "clients"
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(clients_dir))

    price_book = tmp_path / "prices.md"
    price_book.write_text(
        "# Roofing\n- Roof Inspection: $99\n- Tile Repair: $250\n", encoding="utf-8"
    )

    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "client",
            "onboard",
            "--client-id",
            "top-roofing",
            "--company",
            "Top Roofing Co",
            "--price-book",
            str(price_book),
            "--currency",
            "USD",
            "--allowed-users",
            "123,456",
            "--port",
            "8090",
        ],
    )
    assert res.exit_code == 0
    assert "Successfully Onboarded Client:" in res.output
    assert "top-roofing" in res.output

    # Verify JSON mode
    res_json = runner.invoke(
        main,
        [
            "client",
            "onboard",
            "--client-id",
            "json-client",
            "--company",
            "JSON Co",
            "--json",
        ],
    )
    assert res_json.exit_code == 0
    out_data = json.loads(res_json.output)
    assert out_data["success"] is True
    assert out_data["client_id"] == "json-client"


def test_cli_client_test(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients_dir = tmp_path / "clients"
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(clients_dir))

    cfg = ClientConfig(client_id="test-hvac", company_name="Test HVAC")
    save_client(cfg)

    def _mock_run_persona(persona: str, task: str, **kwargs):
        if "rocket" in task.lower():
            text = "Sorry, we do not provide rocket repair. Please contact support for help."
        elif "alice" in task.lower():
            text = "Thank you Alice, your contact details have been recorded."
        else:
            text = "For standard HVAC inspection, our price quote is $99."
        return AgentResult(
            text=text,
            iterations=1,
            stop_reason="end_turn",
            usage={"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
        )

    runner = CliRunner()
    with patch("sakthai.client.verifier.run_persona_task", side_effect=_mock_run_persona):
        res = runner.invoke(main, ["client", "test", "test-hvac"])
        assert res.exit_code == 0
        assert "Pre-Flight Verification Report" in res.output
        assert "PASSED ✅" in res.output

        # Test JSON flag
        res_json = runner.invoke(main, ["client", "test", "test-hvac", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["all_passed"] is True
        assert data["total_tests"] == 3

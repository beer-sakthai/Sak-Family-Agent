"""Comprehensive tests for sakthai.cli.extensions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.extensions import (
    ExtensionError,
    ExtensionInfo,
    ExtensionUpdateResult,
    ExtensionValidationResult,
    InstallResult,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_extensions_list_empty(runner: CliRunner, sakthai_home: Path) -> None:
    res = runner.invoke(main, ["extensions", "list"])
    assert res.exit_code == 0
    assert "no extensions installed" in res.output

    res_p = runner.invoke(main, ["extensions", "list", "--persona", "sakking"])
    assert res_p.exit_code == 0
    assert "persona 'sakking'" in res_p.output

    res_all = runner.invoke(main, ["extensions", "list", "--all-personas"])
    assert res_all.exit_code == 0
    assert "all scopes" in res_all.output


def test_extensions_list_with_items_and_json(runner: CliRunner) -> None:
    fake_list = [
        ExtensionInfo(
            name="ext1",
            url="https://github.com/foo/ext1",
            path=Path("/tmp/ext1"),
            skills=["s1"],
            mcp_servers=["m1"],
            persona="saksee",
            description="Web tools",
            commit_sha="abcdef1234",
        ),
        ExtensionInfo(
            name="ext2",
            url="https://github.com/foo/ext2",
            path=Path("/tmp/ext2"),
            skills=[],
            mcp_servers=[],
            persona=None,
        ),
    ]
    with patch("sakthai.cli.extensions.list_extensions", return_value=fake_list):
        res = runner.invoke(main, ["extensions", "list"])
        assert res.exit_code == 0
        assert "ext1" in res.output
        assert "Web tools" in res.output
        assert "abcdef1234" in res.output
        assert "[shared] ext2" in res.output

        res_json = runner.invoke(main, ["extensions", "list", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert len(data) == 2
        assert data[0]["name"] == "ext1"


def test_extensions_install_cli(runner: CliRunner) -> None:
    fake_res = InstallResult(
        extension=ExtensionInfo(
            name="bar", url="https://github.com/foo/bar", path=Path("/tmp/bar")
        ),
        already_installed=False,
        skills_found=["s1"],
        mcp_servers_found=["srv1"],
    )
    with patch("sakthai.cli.extensions.install_extension", return_value=fake_res):
        res = runner.invoke(main, ["extensions", "install", "https://github.com/foo/bar"])
        assert res.exit_code == 0
        assert "installed: bar [shared]" in res.output
        assert "skills: s1" in res.output
        assert "mcp   : srv1" in res.output

    # Already installed
    fake_res_already = InstallResult(
        extension=ExtensionInfo(
            name="bar", url="https://github.com/foo/bar", path=Path("/tmp/bar")
        ),
        already_installed=True,
    )
    with patch("sakthai.cli.extensions.install_extension", return_value=fake_res_already):
        res_already = runner.invoke(
            main, ["extensions", "install", "https://github.com/foo/bar", "--persona", "sakjules"]
        )
        assert res_already.exit_code == 0
        assert "already installed: bar [persona: sakjules]" in res_already.output

    # Error
    with patch(
        "sakthai.cli.extensions.install_extension", side_effect=ExtensionError("git failed")
    ):
        res_err = runner.invoke(main, ["extensions", "install", "https://github.com/foo/bad"])
        assert res_err.exit_code != 0
        assert "git failed" in res_err.output


def test_extensions_info_cli(runner: CliRunner) -> None:
    fake_info = ExtensionInfo(
        name="my-ext",
        url="https://github.com/foo/my-ext",
        path=Path("/tmp/my-ext"),
        skills=["skill-a"],
        mcp_servers=["mcp-a"],
        persona="saksee",
        description="Demo description",
        version="1.2.0",
        commit_sha="1234567890",
    )
    with patch("sakthai.cli.extensions.get_extension_info", return_value=fake_info):
        res = runner.invoke(main, ["extensions", "info", "my-ext", "--persona", "saksee"])
        assert res.exit_code == 0
        assert "Extension: my-ext (scope: saksee)" in res.output
        assert "Demo description" in res.output
        assert "1.2.0" in res.output
        assert "1234567890" in res.output
        assert "skill-a" in res.output
        assert "mcp-a" in res.output

        res_json = runner.invoke(
            main, ["extensions", "info", "my-ext", "--persona", "saksee", "--json"]
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["name"] == "my-ext"
        assert data["version"] == "1.2.0"

    with patch("sakthai.cli.extensions.get_extension_info", return_value=None):
        res_none = runner.invoke(main, ["extensions", "info", "unknown"])
        assert res_none.exit_code != 0
        assert "not found in target scope" in res_none.output


def test_extensions_info_cli_minimal(runner: CliRunner) -> None:
    fake_info = ExtensionInfo(
        name="min-ext",
        url="https://github.com/foo/min-ext",
        path=Path("/tmp/min-ext"),
    )
    with patch("sakthai.cli.extensions.get_extension_info", return_value=fake_info):
        res = runner.invoke(main, ["extensions", "info", "min-ext"])
        assert res.exit_code == 0
        assert "Extension: min-ext (scope: shared)" in res.output
        assert "(none)" in res.output


def test_extensions_validate_cli(runner: CliRunner) -> None:
    # No extensions to validate
    with patch("sakthai.cli.extensions.list_extensions", return_value=[]):
        res_empty = runner.invoke(main, ["extensions", "validate"])
        assert res_empty.exit_code == 0
        assert "(no extensions to validate)" in res_empty.output

    # Valid extension text mode
    fake_val_ok = ExtensionValidationResult(
        name="ext-ok",
        valid=True,
        path=Path("/tmp/ext-ok"),
        containment_valid=True,
        manifest_valid=True,
        skills_valid=True,
        persona=None,
    )
    with patch("sakthai.cli.extensions.validate_extension", return_value=fake_val_ok):
        res_ok = runner.invoke(main, ["extensions", "validate", "ext-ok"])
        assert res_ok.exit_code == 0
        assert "[PASS] ext-ok [shared]" in res_ok.output

        # Validate with list of extensions discovered
        with patch(
            "sakthai.cli.extensions.list_extensions",
            return_value=[ExtensionInfo(name="ext-ok", url="u", path=Path("/p"))],
        ):
            res_all = runner.invoke(main, ["extensions", "validate"])
            assert res_all.exit_code == 0
            assert "[PASS] ext-ok [shared]" in res_all.output

    # Invalid extension text mode
    fake_val_fail = ExtensionValidationResult(
        name="ext-bad",
        valid=False,
        path=Path("/tmp/ext-bad"),
        containment_valid=True,
        manifest_valid=False,
        skills_valid=False,
        diagnostics=["Broken manifest", "Broken frontmatter"],
        persona="sakking",
    )
    with patch("sakthai.cli.extensions.validate_extension", return_value=fake_val_fail):
        res_fail = runner.invoke(
            main, ["extensions", "validate", "ext-bad", "--persona", "sakking"]
        )
        assert res_fail.exit_code == 1
        assert "[FAIL] ext-bad [sakking]" in res_fail.output
        assert "Broken manifest" in res_fail.output

    # Validation raising ExtensionError
    with patch(
        "sakthai.cli.extensions.validate_extension", side_effect=ExtensionError("corrupted")
    ):
        res_err = runner.invoke(main, ["extensions", "validate", "ext-err"])
        assert res_err.exit_code == 1
        assert "[FAIL] ext-err" in res_err.output

        res_err_json = runner.invoke(main, ["extensions", "validate", "ext-err", "--json"])
        assert res_err_json.exit_code == 1
        data = json.loads(res_err_json.output)
        assert data["valid"] is False

    # Valid extension json mode
    with patch("sakthai.cli.extensions.validate_extension", return_value=fake_val_ok):
        res_json = runner.invoke(main, ["extensions", "validate", "ext-ok", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["valid"] is True


def test_extensions_update_cli(runner: CliRunner) -> None:
    # Missing args
    res_noarg = runner.invoke(main, ["extensions", "update"])
    assert res_noarg.exit_code != 0
    assert "Specify an extension NAME" in res_noarg.output

    # No extensions installed when updating --all
    with patch("sakthai.cli.extensions.list_extensions", return_value=[]):
        res_empty = runner.invoke(main, ["extensions", "update", "--all"])
        assert res_empty.exit_code == 0
        assert "(no extensions found to update)" in res_empty.output

    # Success update
    fake_up_ok = ExtensionUpdateResult(
        name="ext1", success=True, updated=True, message="Updated successfully", commit_sha="12345"
    )
    with patch("sakthai.cli.extensions.update_extension", return_value=fake_up_ok):
        res_ok = runner.invoke(main, ["extensions", "update", "ext1"])
        assert res_ok.exit_code == 0
        assert "[OK] ext1 [shared]: Updated successfully" in res_ok.output

        # Update all with items
        with patch(
            "sakthai.cli.extensions.list_extensions",
            return_value=[ExtensionInfo(name="ext1", url="u", path=Path("/p"))],
        ):
            res_all = runner.invoke(main, ["extensions", "update", "--all"])
            assert res_all.exit_code == 0
            assert "[OK] ext1 [shared]: Updated successfully" in res_all.output

    # Failed update
    fake_up_fail = ExtensionUpdateResult(
        name="ext1", success=False, updated=False, message="git pull failed"
    )
    with patch("sakthai.cli.extensions.update_extension", return_value=fake_up_fail):
        res_fail = runner.invoke(main, ["extensions", "update", "ext1", "--persona", "saksee"])
        assert res_fail.exit_code == 1
        assert "[FAIL] ext1 [saksee]: git pull failed" in res_fail.output

    # ExtensionError on update
    with patch(
        "sakthai.cli.extensions.update_extension", side_effect=ExtensionError("not on disk")
    ):
        res_err = runner.invoke(main, ["extensions", "update", "ext1"])
        assert res_err.exit_code == 1
        assert "[ERROR] ext1: not on disk" in res_err.output


def test_extensions_remove_cli(runner: CliRunner) -> None:
    with patch(
        "sakthai.cli.extensions.remove_extension", side_effect=ExtensionError("escapes base")
    ):
        res = runner.invoke(main, ["extensions", "remove", "bad-ext"])
        assert res.exit_code != 0
        assert "escapes base" in res.output

    # Success shared
    with patch("sakthai.cli.extensions.remove_extension", return_value=True):
        res_ok = runner.invoke(main, ["extensions", "remove", "good-ext"])
        assert res_ok.exit_code == 0
        assert "removed: good-ext" in res_ok.output

    # Success persona
    with patch("sakthai.cli.extensions.remove_extension", return_value=True):
        res_p = runner.invoke(main, ["extensions", "remove", "good-ext", "--persona", "saktan"])
        assert res_p.exit_code == 0
        assert "removed: good-ext from persona 'saktan'" in res_p.output

    # Not installed
    with patch("sakthai.cli.extensions.remove_extension", return_value=False):
        res_fail = runner.invoke(main, ["extensions", "remove", "not-ext", "--persona", "sakthai"])
        assert res_fail.exit_code != 0
        assert "no extension named 'not-ext' is installed from persona 'sakthai'" in res_fail.output

"""Tests for the cloud runtime stub (sakthai.cloud).

All hermetic: Google ADK is not installed in CI, and the tests that depend on
its presence/absence patch ``adk_installed`` so they hold either way. The memory
tools run against an isolated store via the ``sakthai_home`` fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.cloud import runtime
from sakthai.cloud.runtime import (
    DEFAULT_CLOUD_MODEL,
    CloudRuntimeError,
    build_adk_agent,
    cloud_status,
    render_manifest,
    resolve_cloud_spec,
)
from sakthai.cloud.tools import forget_fact, learn_fact, recall_memory, search_memory

# -- spec / config -------------------------------------------------------


def test_resolve_cloud_spec_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_CLOUD_STAGING_BUCKET",
    ):
        monkeypatch.delenv(var, raising=False)
    spec = resolve_cloud_spec()
    assert spec.project is None
    assert spec.location == "us-central1"
    assert spec.model == DEFAULT_CLOUD_MODEL
    assert spec.use_vertex is False
    assert spec.staging_bucket is None


def test_resolve_cloud_spec_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "True")
    monkeypatch.setenv("GOOGLE_CLOUD_STAGING_BUCKET", "gs://demo-bucket")
    spec = resolve_cloud_spec()
    assert spec.project == "demo-project"
    assert spec.location == "europe-west1"
    assert spec.use_vertex is True
    assert spec.staging_bucket == "gs://demo-bucket"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("True", True), ("1", True), ("yes", True), ("on", True), ("false", False), ("", False)],
)
def test_use_vertexai_parsing(monkeypatch: pytest.MonkeyPatch, value: str, expected: bool) -> None:
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", value)
    assert resolve_cloud_spec().use_vertex is expected


# -- status / readiness --------------------------------------------------


def test_cloud_status_not_ready_without_adk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "adk_installed", lambda: False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    status = cloud_status()
    assert status["adk_installed"] is False
    assert status["ready"] is False


def test_cloud_status_ready_when_all_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "adk_installed", lambda: True)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "True")  # credential via Vertex
    status = cloud_status()
    assert status["ready"] is True
    assert status["project"] == "demo-project"


# -- manifest ------------------------------------------------------------


def test_render_manifest_round_trips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    data = yaml.safe_load(render_manifest())
    assert data["name"] == "sakthai-memory-agent"
    assert data["runtime"] == "google-adk"
    assert data["project"] == "demo-project"
    assert "learn_fact" in data["tools"]
    assert "forget_fact" in data["tools"]


# -- build (lazy ADK import) ---------------------------------------------


def test_build_adk_agent_raises_without_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "adk_installed", lambda: False)
    with pytest.raises(CloudRuntimeError, match="cloud"):
        build_adk_agent()


# -- memory tools (go through MemoryStore) -------------------------------


def test_memory_tools_round_trip(sakthai_home: Path) -> None:
    msg = learn_fact("the sky is blue", kind="note")
    assert "Saved fact #1" in msg
    assert "the sky is blue" in recall_memory()
    assert "the sky is blue" in search_memory("sky")
    assert "Forgot fact #1" in forget_fact(1)
    assert "No fact #1" in forget_fact(1)


def test_recall_empty(sakthai_home: Path) -> None:
    assert recall_memory() == "Memory is empty."


# -- CLI -----------------------------------------------------------------


def test_cli_cloud_status(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "adk_installed", lambda: False)
    result = CliRunner().invoke(main, ["cloud", "status"])
    assert result.exit_code == 0
    assert "SakThai Cloud Status" in result.output


def test_cli_cloud_manifest(sakthai_home: Path) -> None:
    result = CliRunner().invoke(main, ["cloud", "manifest"])
    assert result.exit_code == 0
    assert "sakthai-memory-agent" in result.output


def test_cli_cloud_scaffold(sakthai_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "deploy"
    result = CliRunner().invoke(main, ["cloud", "scaffold", str(target)])
    assert result.exit_code == 0
    assert (target / "manifest.yaml").is_file()
    # Second run without --force fails; with --force succeeds.
    again = CliRunner().invoke(main, ["cloud", "scaffold", str(target)])
    assert again.exit_code != 0
    forced = CliRunner().invoke(main, ["cloud", "scaffold", str(target), "--force"])
    assert forced.exit_code == 0


def test_cli_cloud_build_without_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "adk_installed", lambda: False)
    result = CliRunner().invoke(main, ["cloud", "build"])
    assert result.exit_code != 0

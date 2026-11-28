"""Tests for LaunchDarkly Server SDK, OpenTelemetry, and AI SDK integration."""

import tomllib
from pathlib import Path

import ldai
import ldclient
import ldotel
from ldclient.config import Config
from ldotel.tracing import Hook, HookOptions


def test_launchdarkly_otel_module_metadata() -> None:
    """Verifies that ldotel is imported with valid version metadata."""
    assert hasattr(ldotel, "__version__")
    assert isinstance(ldotel.__version__, str)


def test_launchdarkly_otel_hook_instantiation() -> None:
    """Verifies that Hook and HookOptions can be instantiated and configured."""
    options = HookOptions()
    hook = Hook(options=options)
    assert hook is not None

    config = Config(sdk_key="test-sdk-key", hooks=[hook], offline=True)
    assert len(config.hooks) == 1
    assert config.hooks[0] is hook


def test_launchdarkly_server_sdk_metadata() -> None:
    """Verifies that ldclient is imported with valid version metadata."""
    assert hasattr(ldclient, "__version__")
    assert isinstance(ldclient.__version__, str)


def test_launchdarkly_ai_sdk_metadata() -> None:
    """Verifies that ldai exports AI Agent, Model, and Judge configuration symbols."""
    assert hasattr(ldai, "__version__")
    assert isinstance(ldai.__version__, str)
    assert hasattr(ldai, "LDAIClient")
    assert hasattr(ldai, "AIAgentConfig")
    assert hasattr(ldai, "AICompletionConfig")
    assert hasattr(ldai, "ToolRegistry")
    assert hasattr(ldai, "Judge")


def test_launchdarkly_pyproject_dependencies() -> None:
    """Verifies that the LaunchDarkly SDK packages used by the app are declared."""
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    assert pyproject_path.exists()

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    assert any("launchdarkly-server-sdk-otel" in dep for dep in deps)
    assert any("launchdarkly-server-sdk>=" in dep for dep in deps)
    assert any("launchdarkly-server-sdk-ai" in dep for dep in deps)

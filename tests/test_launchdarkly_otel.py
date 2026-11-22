"""Tests for LaunchDarkly Server SDK, OpenTelemetry, AI SDK, and Observability integration."""

import importlib.metadata
import tomllib
from pathlib import Path

import ldai
import ldclient
import ldobserve
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


def test_launchdarkly_observability_metadata() -> None:
    """Verifies that ldobserve exports core observability components and has distribution version."""
    assert hasattr(ldobserve, "ObservabilityConfig")
    assert hasattr(ldobserve, "ObservabilityPlugin")
    assert hasattr(ldobserve, "observe")
    version = importlib.metadata.version("launchdarkly-observability")
    assert isinstance(version, str)
    assert len(version) > 0


def test_launchdarkly_observability_plugin_config() -> None:
    """Verifies that ObservabilityConfig and ObservabilityPlugin can be instantiated."""
    config = ldobserve.ObservabilityConfig(
        service_name="sakthai-agent",
        service_version="2.0.0",
        environment="test",
    )
    plugin = ldobserve.ObservabilityPlugin(config=config)
    assert plugin is not None
    metadata = plugin.metadata()
    assert metadata.name == "launchdarkly-observability"


def test_launchdarkly_pyproject_dependencies() -> None:
    """Verifies that all four LaunchDarkly Python SDK packages are declared in pyproject.toml."""
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    assert pyproject_path.exists()

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    assert any("launchdarkly-server-sdk-otel" in dep for dep in deps)
    assert any("launchdarkly-server-sdk>=" in dep for dep in deps)
    assert any("launchdarkly-server-sdk-ai" in dep for dep in deps)
    assert any("launchdarkly-observability" in dep for dep in deps)

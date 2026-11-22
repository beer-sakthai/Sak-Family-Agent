"""Tests for LaunchDarkly Server SDK OpenTelemetry integration."""

import tomllib
from pathlib import Path

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


def test_launchdarkly_otel_pyproject_dependency() -> None:
    """Verifies that launchdarkly-server-sdk-otel is declared in pyproject.toml."""
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    assert pyproject_path.exists()

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    assert any("launchdarkly-server-sdk-otel" in dep for dep in deps)

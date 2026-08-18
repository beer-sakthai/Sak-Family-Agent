"""Tests for scripts/diagnose_personas.py.

This module tests the diagnostic reporting and helper functions in scripts/diagnose_personas.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "diagnose_personas.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("diagnose_personas", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagnose_personas = _load_module()


@pytest.fixture(autouse=True)
def reset_diagnose_globals() -> None:
    """Reset failures and warnings lists before and after each test."""
    diagnose_personas.failures.clear()
    diagnose_personas.warnings.clear()
    yield
    diagnose_personas.failures.clear()
    diagnose_personas.warnings.clear()


def test_info_without_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info() with label only."""
    diagnose_personas.info("model")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] model\n"


def test_info_with_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test info() with label and detail string."""
    diagnose_personas.info("model", "config.yaml")
    captured = capsys.readouterr()
    assert captured.out == "  [INFO] model — config.yaml\n"


def test_warn_without_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn() records warning label and prints output without detail."""
    diagnose_personas.warn("naming convention")
    captured = capsys.readouterr()
    assert captured.out == "  [WARN] naming convention\n"
    assert diagnose_personas.warnings == ["naming convention"]


def test_warn_with_detail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test warn() records warning label and prints output with detail."""
    diagnose_personas.warn("naming convention", "needs rename")
    captured = capsys.readouterr()
    assert captured.out == "  [WARN] naming convention — needs rename\n"
    assert diagnose_personas.warnings == ["naming convention"]


def test_check_pass(capsys: pytest.CaptureFixture[str]) -> None:
    """Test check() when ok is True."""
    diagnose_personas.check("skills compose", True, "5 skills")
    captured = capsys.readouterr()
    assert captured.out == "  [PASS] skills compose — 5 skills\n"
    assert diagnose_personas.failures == []


def test_check_fail(capsys: pytest.CaptureFixture[str]) -> None:
    """Test check() when ok is False appends to failures list."""
    diagnose_personas.check("skills compose", False, "missing skills")
    captured = capsys.readouterr()
    assert captured.out == "  [FAIL] skills compose — missing skills\n"
    assert diagnose_personas.failures == ["skills compose"]


def test_persona_model_config_path() -> None:
    """Test persona_model_config_path returns correct Path."""
    path = diagnose_personas.persona_model_config_path("sakthai")
    assert path == diagnose_personas.PERSONAS_DIR / "sakthai" / "config" / "config.yaml"


def test_persona_mcp_config_path() -> None:
    """Test persona_mcp_config_path returns correct Path."""
    path = diagnose_personas.persona_mcp_config_path("sakthai")
    assert path == diagnose_personas.PERSONAS_DIR / "sakthai" / "config" / "mcp.json"

"""Security tests verifying repository credential hygiene and secret redaction."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sakthai.config import redact_secrets

REPO_ROOT = Path(__file__).resolve().parents[1]

# Patterns for active credential formats
SUSPICIOUS_TOKEN_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI / Mistral style
    re.compile(r"hf_[a-zA-Z0-9]{34,}"),  # Hugging Face live token
    re.compile(r"ck_[a-zA-Z0-9]{20,}"),  # Composio live consumer key
    re.compile(r"KGAT-[a-zA-Z0-9]{20,}"),  # Kaggle API token
]


def test_redact_secrets_filters_common_tokens() -> None:
    sample_text = (
        "Authorization: Bearer sk-1234567890abcdef1234567890\n"
        "Composio key: ck_1234567890abcdef1234567890\n"
        "HuggingFace token: hf_0123456789012345678901234567890123\n"
        "Password: secret_password_value"
    )
    redacted = redact_secrets(sample_text)
    assert "sk-1234567890abcdef" not in redacted
    assert "ck_1234567890abcdef" not in redacted
    assert "hf_0123456789012345" not in redacted
    assert "[REDACTED]" in redacted


def test_persona_and_service_configs_have_no_hardcoded_keys() -> None:
    config_paths = list(REPO_ROOT.glob("personas/*/config/config.yaml"))
    config_paths += list(REPO_ROOT.glob("services/*/config/config.yaml"))
    config_paths += list(REPO_ROOT.glob("personas/*/config/mcp.json"))

    assert len(config_paths) > 0

    for path in config_paths:
        content = path.read_text(encoding="utf-8")
        for pattern in SUSPICIOUS_TOKEN_PATTERNS:
            matches = pattern.findall(content)
            assert not matches, f"Suspicious credential pattern found in {path}: {matches}"


def test_env_example_has_no_live_tokens() -> None:
    env_example = REPO_ROOT / ".env.example"
    if not env_example.exists():
        pytest.skip(".env.example does not exist")

    content = env_example.read_text(encoding="utf-8")
    for pattern in SUSPICIOUS_TOKEN_PATTERNS:
        matches = pattern.findall(content)
        assert not matches, f"Live token found in .env.example: {matches}"

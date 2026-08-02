"""Shared test utilities for secret detection tests."""

import pytest


def run_secret_detection_tests(secret_detection_func):
    """
    A generic test runner for any function that detects secrets in a string.
    This allows secret detection logic to be tested consistently.
    """

    # --- True Positives ---
    assert secret_detection_func("here is sk-ant-api03-abc123def456 my key")
    assert secret_detection_func("sk-or-v1-abcdef1234567890abcdef")
    assert secret_detection_func("use ghp_abcdefghijklmnopqrstuvwxyz12")
    assert secret_detection_func("ghu_abcdef123456")
    assert secret_detection_func("SLACK_TOKEN is xoxb-123-456-abcdef")
    assert secret_detection_func("xapp-1-ABC-123456-xyz")
    assert secret_detection_func("ntn_37257299567bdiGRuYDIjhNH8uFribb461")
    assert secret_detection_func("Authorization: Bearer dsm_bYxe4QUvPsDjRThUu2Qb3z")
    assert secret_detection_func("export ANTHROPIC_API_KEY=something")
    assert secret_detection_func("OPENAI_API_KEY=sk-blah")
    assert secret_detection_func("sk-proj-1234567890abcdefghij")
    assert secret_detection_func("password=my_super_secret_123")
    assert secret_detection_func("password: hunter2abc")
    assert secret_detection_func("secret=abc123def456")
    assert secret_detection_func("secret: my_api_secret_key")
    assert secret_detection_func("token=abcdef1234567890")
    assert secret_detection_func("token: eyJhbGciOiJIUzI1NiJ9")
    assert secret_detection_func("export OPENROUTER_API_KEY=sk-or-xyz")
    assert secret_detection_func("SLACK_BOT_TOKEN=xoxb-abc")
    assert secret_detection_func("GITHUB_TOKEN=ghp_abc123")
    assert secret_detection_func("AKIAIOSFODNN7EXAMPLE")
    assert secret_detection_func("-----BEGIN RSA PRIVATE KEY-----\nMIIEow...")
    assert secret_detection_func("-----BEGIN PRIVATE KEY-----\nMIIEvQ...")
    assert secret_detection_func("export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG")
    assert secret_detection_func("DATABASE_URL=postgres://user:pass@host/db")
    assert secret_detection_func('{"api_key": "sk-abc123def456"}')
    assert secret_detection_func("headers={'Authorization': 'Bearer sk-abcdef123456'}")
    assert secret_detection_func("Bearer sk-abcdef123456 was used")

    # --- False Positives ---
    assert not secret_detection_func("sort these messages by topic")
    assert not secret_detection_func("I asked about sk")
    assert not secret_detection_func("the key insight is that we need to refactor")
    assert not secret_detection_func("the bearer of bad news")
    assert not secret_detection_func("parse the JWT token from the header")
    assert not secret_detection_func("ask the user for their preferences")
    assert not secret_detection_func("token=abc")
    assert not secret_detection_func("the password field should be validated")
    assert not secret_detection_func("reset your password using the link")
    assert not secret_detection_func("the secret to success is consistency")
    assert not secret_detection_func("it's no secret that we need to refactor")


@pytest.mark.parametrize(
    "secret",
    [
        "sk-ant-api03-abc123def456",
        "sk-or-v1-abcdef1234567890abcdef",
        "ghp_abcdefghijklmnopqrstuvwxyz12",
        "ghu_abcdef123456",
        "xoxb-123-456-abcdef",
        "xapp-1-ABC-123456-xyz",
        "ntn_37257299567bdiGRuYDIjhNH8uFribb461",
        "dsm_bYxe4QUvPsDjRThUu2Qb3z",
        "sk-proj-1234567890abcdefghij",
        "my_super_secret_123",
        "my_api_secret_key",
        "abcdef1234567890",
        "eyJhbGciOiJIUzI1NiJ9",
        "AKIAIOSFODNN7EXAMPLE",
        "wJalrXUtnFEMI/K7MDENG",
        "postgres://user:pass@host/db",
    ],
)
def test_true_positives(secret_detection_func, secret):
    """Parametrized tests for various secret formats."""
    assert secret_detection_func(f"some text with {secret} inside")
    assert secret_detection_func(f"secret={secret}")
    assert secret_detection_func(f"export KEY={secret}")


@pytest.mark.parametrize(
    "prose",
    [
        "sort these messages by topic",
        "I asked about sk",
        "the key insight is that we need to refactor",
        "the bearer of bad news",
        "parse the JWT token from the header",
        "ask the user for their preferences",
        "token=abc",
        "the password field should be validated",
        "the secret to success is consistency",
    ],
)
def test_false_positives(secret_detection_func, prose):
    """Parametrized tests for normal text that shouldn't trigger detection."""
    assert not secret_detection_func(prose)

"""Unit tests for House of Sak PR codename generator."""

from __future__ import annotations

import pytest

from scripts.generate_pr_codename import (
    detect_persona,
    format_pr_comment,
    generate_codename,
    main,
)


def test_detect_persona_mappings() -> None:
    # SakJules detection
    assert detect_persona([".github/workflows/ci.yml"]) == "sakjules"
    assert detect_persona(["scripts/check.py"], pr_title="fix: ci security") == "sakjules"

    # SakSee detection
    assert detect_persona(["apps/sak_agent_dashboard/package.json"]) == "saksee"

    # SakThai detection
    assert (
        detect_persona(["personas/sakthai/model_card.py"], pr_title="hf: sync models") == "sakthai"
    )

    # SakTan detection
    assert detect_persona(["personas/saktan/memory_health.py"]) == "saktan"

    # SakSit detection
    assert detect_persona(["docs/community.md", "README.md"]) == "saksit"

    # Default fallback
    assert detect_persona([]) == "sakking"


def test_generate_codename_deterministic() -> None:
    code1 = generate_codename("sakjules", "PR-1234")
    code2 = generate_codename("sakjules", "PR-1234")
    assert code1 == code2
    assert code1.startswith("SakJules · ")

    code_thai = generate_codename("sakthai", "PR-5678")
    assert code_thai.startswith("SakThai · ")


def test_format_pr_comment() -> None:
    comment = format_pr_comment("sakjules", "SakJules · Aegis Sentinel (07)")
    assert "### 🛡️ House of Sak Operational Codename" in comment
    assert "**`SakJules · Aegis Sentinel (07)`**" in comment
    assert "SakJules" in comment
    assert "Master of Automation & CI/CD" in comment


def test_main_cli(capsys: pytest.CaptureFixture[str]) -> None:
    ret = main(
        [
            "--pr-number",
            "1897",
            "--pr-title",
            "ci: extract reusable pull request sync workflow",
            "--changed-files",
            ".github/workflows/reusable.yml",
        ]
    )
    assert ret == 0
    captured = capsys.readouterr()
    assert "House of Sak Operational Codename" in captured.out
    assert "SakJules" in captured.out

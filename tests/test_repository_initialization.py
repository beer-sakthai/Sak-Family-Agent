"""Tests for repository initialization workflow, handoff schema, and soul templates."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_initialize_repository_script_executable() -> None:
    script_path = REPO_ROOT / "scripts" / "initialize_repository.sh"
    assert script_path.is_file(), "scripts/initialize_repository.sh does not exist"
    assert os.access(script_path, os.X_OK), "scripts/initialize_repository.sh is not executable"


def test_initialize_repository_check_mode() -> None:
    script_path = REPO_ROOT / "scripts" / "initialize_repository.sh"
    res = subprocess.run(
        [str(script_path), "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"initialize_repository.sh --check failed: {res.stderr}\n{res.stdout}"
    )
    assert "structure validation completed" in res.stdout


def test_inter_agent_handoff_schema_valid() -> None:
    schema_path = REPO_ROOT / "docs" / "schemas" / "inter-agent-handoff.schema.json"
    assert schema_path.is_file(), "docs/schemas/inter-agent-handoff.schema.json does not exist"

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    # Valid schema according to Draft 2020-12
    jsonschema.Draft202012Validator.check_schema(schema)

    sample_envelope = {
        "protocol_version": "1.0.0-draft",
        "handoff_id": "ho_20261116_test_01",
        "message_type": "data-request",
        "status": "requested",
        "sender": {"agent": "saksit", "role": "Social / Content Specialist"},
        "recipient": {"agents": ["saksee"], "role": "Web / Browser Specialist"},
        "created_at": "2026-11-16T22:30:00Z",
        "updated_at": "2026-11-16T22:30:00Z",
        "task": {
            "title": "Test Task",
            "objective": "Verify schema validation",
            "scope": "repo",
            "acceptance_criteria": ["Criteria 1"],
        },
        "payload": {
            "summary": "Sample summary",
        },
        "constraints": {
            "charge_required": "active",
            "approval_required": False,
            "cost_limit_usd": 0,
        },
        "recovery": {
            "resumable": True,
        },
    }

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(sample_envelope))
    assert not errors, f"Sample envelope failed schema validation: {[e.message for e in errors]}"


def test_all_six_soul_templates_exist() -> None:
    templates_dir = REPO_ROOT / "docs" / "soul-templates"
    assert templates_dir.is_dir(), "docs/soul-templates directory does not exist"

    personas = ["sakthai", "sakking", "saksee", "saksit", "saktan", "sakjules"]
    for persona in personas:
        template_file = templates_dir / f"{persona}_soul_template.md"
        assert template_file.is_file(), f"Missing template for {persona}: {template_file}"
        content = template_file.read_text(encoding="utf-8")
        assert len(content) > 100
        assert persona in content.lower()

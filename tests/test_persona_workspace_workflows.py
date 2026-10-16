"""Validation tests for the 6 Sak Family Agent persona workspace manifests and workflow schemas."""

from __future__ import annotations

import pathlib

import yaml

from sakthai.config import PERSONA_NAMES
from sakthai.skills import resolve_skill_names

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"


def test_sakthai_sakking_saktan_workspace_manifests():
    for agent, expected_role in [
        ("sakthai", "Main Lead & HF Master"),
        ("sakking", "General Assistant & Runner"),
        ("saktan", "Daily Ops & Rhythm"),
    ]:
        manifest_path = PERSONAS_DIR / agent / "config" / "workspace.yaml"
        assert manifest_path.exists(), f"Missing {manifest_path}"
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["agent_name"].lower() == agent
        assert expected_role in data["role"]


def test_saksee_saksit_sakjules_workspace_manifests():
    for agent, expected_role in [
        ("saksee", "Web / Browser Specialist"),
        ("saksit", "Social / Content Specialist"),
        ("sakjules", "Master of GitHub, CI/CD & Automation"),
    ]:
        manifest_path = PERSONAS_DIR / agent / "config" / "workspace.yaml"
        assert manifest_path.exists(), f"Missing {manifest_path}"
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["agent_name"].lower() == agent
        assert expected_role in data["role"]


def test_primary_skills_resolve_for_their_persona():
    """Each workspace's primary skills must load for that persona via `--with-skills`.

    Five once named skills that did not exist, so `run --with-skills` refused them.
    """
    for agent in PERSONA_NAMES:
        data = yaml.safe_load(
            (PERSONAS_DIR / agent / "config" / "workspace.yaml").read_text(encoding="utf-8")
        )
        _, missing = resolve_skill_names(data.get("primary_skills") or [], persona=agent)
        assert not missing, f"{agent} workspace.yaml names missing skill(s): {missing}"


def test_all_six_workspaces_match_schema():
    schema_path = PERSONAS_DIR / "shared" / "config" / "workflow_schema.yaml"
    assert schema_path.exists(), f"Missing {schema_path}"

    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    required_keys = schema["required_keys"]

    for agent in ["sakthai", "sakking", "saktan", "saksee", "saksit", "sakjules"]:
        config_path = PERSONAS_DIR / agent / "config" / "workspace.yaml"
        assert config_path.exists(), f"Missing config for {agent}"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        for k in required_keys:
            assert k in config, f"Missing key {k} in {agent}/config/workspace.yaml"

import re

import yaml

from app.agent_platform.harness_exporter import (
    export_harness_agent_spec,
    export_v1_pipeline_step,
    generate_harness_uid,
)


def test_generate_harness_uid():
    assert generate_harness_uid("Code Review Agent") == "ca_code_review_agent"
    assert generate_harness_uid("PR-Security--Scanner") == "ca_pr_security_scanner"


def test_generate_harness_uid_variations():
    # Already prefixed with ca_
    assert generate_harness_uid("ca_code_review_agent") == "ca_code_review_agent"
    # Special characters and multiple separators
    assert generate_harness_uid("!! Special & Agent !!") == "ca_special_agent"
    assert generate_harness_uid("Linter") == "ca_linter"
    # Strict formatting check: ca_<slug> where slug is lowercase alphanumeric with single underscores
    uid = generate_harness_uid("My Complex AI Agent 2.0!")
    assert re.match(r"^ca_[a-z0-9]+(?:_[a-z0-9]+)*$", uid) is not None


def test_export_harness_agent_spec_structure():
    spec_yaml = export_harness_agent_spec(
        name="Security Scanner",
        task="1. Inspect PR diff\n2. Flag high severity issues",
        llm_connector_id="harness_gemini_connector",
        mcp_connectors=["github_mcp"],
    )
    assert "version: 1" in spec_yaml
    assert (
        "pkg.harness.io/vrvdt5ius7uwygso8s0bia/harness-agents/harness-ai-agent:latest" in spec_yaml
    )
    assert "PLUGIN_HARNESS_CONNECTOR: ${{inputs.llmConnector.id}}" in spec_yaml
    assert "PLUGIN_ALLOWED_DOMAINS: ${{inputs.allowedDomains}}" in spec_yaml
    assert (
        "PLUGIN_MCP_SERVERS: <+connectorInputs.resolveList(<+inputs.mcpConnectors>)>" in spec_yaml
    )
    assert "harness_gemini_connector" in spec_yaml
    assert "github_mcp" in spec_yaml

    # Valid YAML syntax
    parsed = yaml.safe_load(spec_yaml)
    assert parsed["version"] == 1
    assert "agent" in parsed
    assert "step" in parsed["agent"]
    assert "inputs" in parsed["agent"]
    assert "mcpConnectors" in parsed["agent"]["inputs"]
    assert "layout" in parsed["agent"]


def test_export_harness_agent_spec_without_mcp():
    spec_yaml = export_harness_agent_spec(
        name="Simple Explainer",
        task="Explain the given code snippet",
        llm_connector_id="default_llm",
        mcp_connectors=None,
    )
    assert "version: 1" in spec_yaml
    assert "PLUGIN_MCP_SERVERS" not in spec_yaml
    assert "PLUGIN_MCP_FORMAT" not in spec_yaml
    assert "mcpConnectors" not in spec_yaml

    parsed = yaml.safe_load(spec_yaml)
    assert "mcpConnectors" not in parsed["agent"]["inputs"]
    # Check layout does not contain mcpConnectors
    layout_items = parsed["agent"]["layout"][0]["items"]
    assert "mcpConnectors" not in layout_items


def test_export_harness_agent_spec_custom_params():
    spec_yaml = export_harness_agent_spec(
        name="Domain Specific Agent",
        task="Check dependencies",
        llm_connector_id="anthropic_connector",
        allowed_domains="api.github.com,npm.pkg.github.com",
        max_turns=300,
    )
    assert "PLUGIN_MAX_TURNS: 300" in spec_yaml
    assert 'default: "api.github.com,npm.pkg.github.com"' in spec_yaml
    assert "anthropic_connector" in spec_yaml


def test_export_v1_pipeline_step():
    step_yaml = export_v1_pipeline_step(
        agent_name="Code Review Agent",
        custom_inputs={"repo_name": "<+inputs.repo_name>", "branch": "<+inputs.branch>"},
    )
    assert "uses: ca_code_review_agent@1.0.0" in step_yaml
    assert "repo_name: <+inputs.repo_name>" in step_yaml
    assert "branch: <+inputs.branch>" in step_yaml

    parsed = yaml.safe_load(step_yaml)
    assert isinstance(parsed, list)
    assert parsed[0]["name"] == "code_review_agent"
    assert parsed[0]["template"]["uses"] == "ca_code_review_agent@1.0.0"
    assert parsed[0]["template"]["with"]["repo_name"] == "<+inputs.repo_name>"


def test_export_v1_pipeline_step_custom_version():
    step_yaml = export_v1_pipeline_step(
        agent_name="Security Scanner",
        custom_inputs={"target_dir": "/workspace"},
        version="2.0.0",
    )
    assert "uses: ca_security_scanner@2.0.0" in step_yaml
    parsed = yaml.safe_load(step_yaml)
    assert parsed[0]["template"]["uses"] == "ca_security_scanner@2.0.0"


def test_export_v1_pipeline_step_empty_custom_inputs():
    step_yaml = export_v1_pipeline_step(
        agent_name="Simple Notifier Agent",
        custom_inputs={},
    )
    assert "uses: ca_simple_notifier_agent@1.0.0" in step_yaml
    assert "with:" not in step_yaml

    parsed = yaml.safe_load(step_yaml)
    assert isinstance(parsed, list)
    assert parsed[0]["name"] == "simple_notifier_agent"
    assert parsed[0]["template"]["uses"] == "ca_simple_notifier_agent@1.0.0"
    assert "with" not in parsed[0]["template"]

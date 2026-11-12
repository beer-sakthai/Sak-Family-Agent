from sakthai.agent_platform.harness_exporter import (
    export_harness_agent_spec,
    export_v1_pipeline_step,
    generate_harness_uid,
)


def test_generate_harness_uid():
    assert generate_harness_uid("Code Review Agent") == "ca_code_review_agent"
    assert generate_harness_uid("PR-Security--Scanner") == "ca_pr_security_scanner"


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


def test_export_harness_agent_spec_without_mcp():
    spec_yaml = export_harness_agent_spec(
        name="Standalone Agent",
        task="Echo hello",
        llm_connector_id="harness_llm",
        mcp_connectors=None,
    )
    assert "version: 1" in spec_yaml
    assert "PLUGIN_MCP_SERVERS" not in spec_yaml
    assert "mcpConnectors" not in spec_yaml


def test_export_v1_pipeline_step():
    step_yaml = export_v1_pipeline_step(
        agent_name="Code Review Agent",
        custom_inputs={"repo_name": "<+inputs.repo_name>", "branch": "<+inputs.branch>"},
    )
    assert "uses: ca_code_review_agent@1.0.0" in step_yaml
    assert "repo_name: <+inputs.repo_name>" in step_yaml

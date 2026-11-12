import re

def generate_harness_uid(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return f"ca_{cleaned}"

def export_harness_agent_spec(
    name: str,
    task: str,
    llm_connector_id: str = "your_llm_connector_id",
    mcp_connectors: list[str] | None = None,
    allowed_domains: str = "",
    max_turns: int = 150,
) -> str:
    mcp_list = mcp_connectors or []
    has_mcp = len(mcp_list) > 0

    task_indented = "\n".join(f"                {line}" for line in task.strip().splitlines())

    mcp_env = ""
    if has_mcp:
        mcp_env = (
            "              PLUGIN_MCP_FORMAT: harness\n"
            "              PLUGIN_MCP_SERVERS: <+connectorInputs.resolveList(<+inputs.mcpConnectors>)>"
        )

    mcp_inputs = ""
    if has_mcp:
        items_yaml = "\n".join(f"        - {conn}" for conn in mcp_list)
        mcp_inputs = f"""    mcpConnectors:
      type: array
      default:
{items_yaml}
      ui:
        component: array
        input:
          inputType: connector
          inputConfig:
            connectorTypes:
              - Mcp
"""

    layout_items = ["llmConnector", "allowedDomains"]
    if has_mcp:
        layout_items.append("mcpConnectors")
    layout_yaml = "\n".join(f"        - {item}" for item in layout_items)

    env_block = f"""            env:
              PLUGIN_TASK: |
{task_indented}
              PLUGIN_MAX_TURNS: {max_turns}
              PLUGIN_HARNESS_CONNECTOR: ${{{{inputs.llmConnector.id}}}}
              PLUGIN_ALLOWED_DOMAINS: ${{{{inputs.allowedDomains}}}}"""
    if mcp_env:
        env_block += f"\n{mcp_env}"

    inputs_block = f"""  inputs:
    llmConnector:
      type: connector
      required: true
      default: {llm_connector_id}
      ui:
        connectorCategories:
          - AI

    allowedDomains:
      type: string
      default: "{allowed_domains}"
"""
    if mcp_inputs:
        inputs_block += f"\n{mcp_inputs}"

    return f"""version: 1
agent:
  step:
    group:
      steps:
        - name: Agent
          if: <+Always>
          id: agent
          run:
            container:
              image: pkg.harness.io/vrvdt5ius7uwygso8s0bia/harness-agents/harness-ai-agent:latest
{env_block}

{inputs_block}
  layout:
    - title: Agent Configuration
      items:
{layout_yaml}
"""

def export_v1_pipeline_step(agent_name: str, custom_inputs: dict[str, str]) -> str:
    uid = generate_harness_uid(agent_name)
    with_block = "\n".join(f"      {k}: {v}" for k, v in custom_inputs.items())
    return f"""- name: {agent_name.lower().replace(' ', '_')}
  template:
    uses: {uid}@1.0.0
    with:
{with_block}
"""

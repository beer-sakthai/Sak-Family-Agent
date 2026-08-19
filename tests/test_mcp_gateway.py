# tests/test_mcp_gateway.py
import pytest

from sakthai.mcp.gateway import MCPGateway
from sakthai.mcp.models import MCPToolDefinition, TransportType
from sakthai.mcp.security import SecurityViolationError, validate_tool_arguments


def test_validate_tool_arguments_clean():
    args = {"path": "safe/file.txt", "query": "select 1"}
    validated = validate_tool_arguments(args)
    assert validated == args


def test_validate_tool_arguments_reject_control_chars():
    args = {"path": "bad\x00file.txt"}
    with pytest.raises(SecurityViolationError, match="Control character detected"):
        validate_tool_arguments(args)


def test_validate_tool_arguments_reject_path_traversal():
    args = {"path": "../../etc/passwd"}
    with pytest.raises(SecurityViolationError, match="Path traversal detected"):
        validate_tool_arguments(args)


@pytest.mark.asyncio
async def test_mcp_gateway_registration_and_invocation():
    gateway = MCPGateway()
    tool = MCPToolDefinition(
        name="read_file",
        description="Read file safely",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
    )

    async def mock_handler(args):
        return {"content": f"data from {args['path']}"}

    gateway.register_tool(
        server_id="fs_server",
        transport=TransportType.STDIO,
        tool=tool,
        handler=mock_handler,
    )

    tools = gateway.list_tools()
    assert len(tools) == 1
    assert tools[0]["qualified_name"] == "fs_server::read_file"

    res = await gateway.invoke_tool("fs_server::read_file", {"path": "docs/readme.txt"})
    assert res == {"content": "data from docs/readme.txt"}

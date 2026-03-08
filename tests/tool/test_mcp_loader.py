"""Tests for tool/mcp/loader.py ToolSource protocol implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import Tool


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client with test tools."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.tools = [
        Tool(name="test_tool", description="A test tool", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}}),
        Tool(name="another_tool", description="Another tool", inputSchema={"type": "object"}),
    ]
    client.call_tool = AsyncMock(return_value="tool result")
    return client


@pytest.fixture
def mcp_loader(mock_mcp_client):
    """Create an MCPLoader with mocked clients."""
    with patch('src.tool.mcp.loader.MCPClient', return_value=mock_mcp_client):
        from src.tool.mcp import MCPLoader
        loader = MCPLoader([{"command": "test"}])
        loader.clients = [mock_mcp_client]
        return loader


@pytest.mark.asyncio
async def test_mcp_loader_get_tools_format(mcp_loader):
    """Test that get_tools() returns List[ToolDescription] with correct fields."""
    tools = mcp_loader.get_tools()

    assert isinstance(tools, list)
    assert len(tools) == 2

    # Check first tool has all required ToolDescription fields
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["description"] == "A test tool"
    assert "inputSchema" in tools[0]
    assert tools[0]["inputSchema"]["type"] == "object"

    # Check second tool
    assert tools[1]["name"] == "another_tool"
    assert tools[1]["description"] == "Another tool"


@pytest.mark.asyncio
async def test_mcp_loader_execute_success(mcp_loader, mock_mcp_client):
    """Test that execute() calls the correct tool and returns result."""
    result = await mcp_loader.execute("test_tool", {"query": "test"})

    mock_mcp_client.call_tool.assert_called_once_with("test_tool", {"query": "test"})
    assert result == "tool result"


@pytest.mark.asyncio
async def test_mcp_loader_execute_not_found(mcp_loader):
    """Test that execute() raises ValueError when tool not found."""
    with pytest.raises(ValueError) as exc_info:
        await mcp_loader.execute("nonexistent_tool", {})

    assert "nonexistent_tool" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mcp_loader_load_delegates(mcp_loader):
    """Test that load() delegates to load_all()."""
    await mcp_loader.load()
    # load() calls load_all() which iterates clients
    mock_mcp_client = mcp_loader.clients[0]
    mock_mcp_client.connect.assert_called()


@pytest.mark.asyncio
async def test_mcp_loader_close_delegates(mcp_loader):
    """Test that close() delegates to close_all()."""
    await mcp_loader.close()
    mock_mcp_client = mcp_loader.clients[0]
    mock_mcp_client.close.assert_called()
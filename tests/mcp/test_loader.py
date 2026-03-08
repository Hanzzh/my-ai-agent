"""Tests for MCP loader."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import Tool


@pytest.mark.asyncio
async def test_mcp_loader_init():
    """Test MCP loader initializes with multiple server configs."""
    from src.mcp.loader import MCPLoader

    server_configs = [
        {"command": "python", "args": ["server1.py"]},
        {"command": "node", "args": ["server2.js"]},
        {"command": "python", "args": ["server3.py"], "env": {"TEST": "value"}}
    ]

    loader = MCPLoader(server_configs)

    # Verify clients were created
    assert len(loader.clients) == 3
    assert all(client.server_params == config for client, config in zip(loader.clients, server_configs))


@pytest.mark.asyncio
async def test_mcp_loader_load_all_and_get_tools():
    """Test MCP loader connects to all servers and collects tools."""
    from src.mcp.loader import MCPLoader

    server_configs = [
        {"command": "python", "args": ["server1.py"]},
        {"command": "node", "args": ["server2.js"]}
    ]

    with patch('src.mcp.client.stdio_client') as mock_stdio_client, \
         patch('src.mcp.client.ClientSession') as mock_session_class:

        # Setup mocks for both servers
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (MagicMock(), MagicMock())

        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock()

        # Mock different tools for each server
        mock_tools_server1 = [
            Tool(name="tool1", description="Tool 1", inputSchema={"type": "object"}),
            Tool(name="tool2", description="Tool 2", inputSchema={"type": "object"})
        ]
        mock_tools_server2 = [
            Tool(name="tool3", description="Tool 3", inputSchema={"type": "object"})
        ]

        # Make list_tools return different tools on each call
        mock_session.list_tools.side_effect = [
            MagicMock(tools=mock_tools_server1),
            MagicMock(tools=mock_tools_server2)
        ]

        # Create loader and load all
        loader = MCPLoader(server_configs)
        await loader.load_all()

        # Verify both servers were connected
        assert mock_session.initialize.call_count == 2
        assert mock_session.list_tools.call_count == 2

        # Get all tools
        tools = loader.get_all_tools()

        # Verify all tools are collected
        assert len(tools) == 3
        assert "tool1" in tools
        assert "tool2" in tools
        assert "tool3" in tools

        # Verify mapping structure (client, tool)
        for tool_name, (client, tool) in tools.items():
            assert isinstance(client, object)  # MCPClient instance
            assert isinstance(tool, Tool)
            assert tool.name == tool_name


@pytest.mark.asyncio
async def test_mcp_loader_close_all():
    """Test MCP loader closes all connections."""
    from src.mcp.loader import MCPLoader

    server_configs = [
        {"command": "python", "args": ["server1.py"]},
        {"command": "node", "args": ["server2.js"]},
        {"command": "python", "args": ["server3.py"]}
    ]

    with patch('src.mcp.client.stdio_client') as mock_stdio_client, \
         patch('src.mcp.client.ClientSession') as mock_session_class:

        # Setup mocks
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (MagicMock(), MagicMock())

        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))

        # Create loader and connect all
        loader = MCPLoader(server_configs)
        await loader.load_all()

        # Close all connections
        await loader.close_all()

        # Verify all sessions and stdio contexts were closed
        assert mock_session.__aexit__.call_count == 3
        assert mock_stdio_context.__aexit__.call_count == 3

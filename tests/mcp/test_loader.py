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
    from src.mcp.client import MCPClient

    server_configs = [
        {"command": "python", "args": ["server1.py"]},
        {"command": "node", "args": ["server2.js"]}
    ]

    # We'll mock at the create_mcp_session level since that's what the client uses now
    with patch('src.mcp.client.create_mcp_session') as mock_create_session:

        # Setup mock to return different tools for each server
        mock_tools_server1 = [
            Tool(name="tool1", description="Tool 1", inputSchema={"type": "object"}),
            Tool(name="tool2", description="Tool 2", inputSchema={"type": "object"})
        ]
        mock_tools_server2 = [
            Tool(name="tool3", description="Tool 3", inputSchema={"type": "object"})
        ]

        # Create a mock async context manager
        async def mock_session_gen(server_params):
            mock_session = MagicMock()
            mock_session.call_tool = AsyncMock()
            if "server1.py" in str(server_params):
                yield mock_session, mock_tools_server1
            else:
                yield mock_session, mock_tools_server2

        # Patch the connect method to avoid actual connection
        async def mock_connect(self):
            # Simulate connection by setting tools directly
            if "server1.py" in str(self.server_params):
                self._session_holder = {"session": MagicMock(), "tools": mock_tools_server1}
            else:
                self._session_holder = {"session": MagicMock(), "tools": mock_tools_server2}

        with patch.object(MCPClient, 'connect', mock_connect):
            # Create loader and load all
            loader = MCPLoader(server_configs)
            await loader.load_all()

            # Get all tools
            tools = loader.get_all_tools()

            # Verify all tools are collected
            assert len(tools) == 3
            assert "tool1" in tools
            assert "tool2" in tools
            assert "tool3" in tools

            # Verify mapping structure (client, tool)
            for tool_name, (client, tool) in tools.items():
                assert isinstance(client, MCPClient)
                assert isinstance(tool, Tool)
                assert tool.name == tool_name


@pytest.mark.asyncio
async def test_mcp_loader_close_all():
    """Test MCP loader closes all connections."""
    from src.mcp.loader import MCPLoader
    from src.mcp.client import MCPClient

    server_configs = [
        {"command": "python", "args": ["server1.py"]},
        {"command": "node", "args": ["server2.js"]},
        {"command": "python", "args": ["server3.py"]}
    ]

    # Mock connect to set up a fake session holder
    async def mock_connect(self):
        self._session_holder = {"session": MagicMock(), "tools": []}

    # Mock close to clear the session holder
    async def mock_close(self):
        self._session_holder = None
        self._closing = False

    with patch.object(MCPClient, 'connect', mock_connect), \
         patch.object(MCPClient, 'close', mock_close):

        # Create loader and connect all
        loader = MCPLoader(server_configs)
        await loader.load_all()

        # Verify all clients were connected
        for client in loader.clients:
            assert client._session_holder is not None

        # Close all connections
        await loader.close_all()

        # Verify all clients were closed
        for client in loader.clients:
            assert client._session_holder is None

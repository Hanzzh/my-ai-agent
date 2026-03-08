"""Tests for MCP client wrapper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import Tool


@pytest.mark.asyncio
async def test_mcp_client_connect():
    """Test MCP client connects and initializes session."""
    from src.mcp.client import MCPClient

    server_params = {
        "command": "python",
        "args": ["server.py"],
        "env": {"TEST": "value"}
    }

    # Mock the stdio_client and ClientSession
    with patch('src.mcp.client.stdio_client') as mock_stdio_client, \
         patch('src.mcp.client.ClientSession') as mock_session_class:

        # Setup mocks
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (MagicMock(), MagicMock())

        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock()

        # Mock tool list
        mock_tools = [
            Tool(name="test_tool", description="A test tool", inputSchema={"type": "object"})
        ]
        mock_session.list_tools.return_value.tools = mock_tools

        # Create client and connect
        client = MCPClient(server_params)
        await client.connect()

        # Verify connection was made
        mock_stdio_context.__aenter__.assert_called_once()
        mock_session.__aenter__.assert_called_once()
        mock_session.initialize.assert_called_once()
        mock_session.list_tools.assert_called_once()

        # Verify tools were loaded
        assert client.tools == mock_tools
        assert client.session == mock_session


@pytest.mark.asyncio
async def test_mcp_client_call_tool():
    """Test calling a tool through MCP client."""
    from src.mcp.client import MCPClient

    server_params = {"command": "python"}

    with patch('src.mcp.client.stdio_client') as mock_stdio_client, \
         patch('src.mcp.client.ClientSession') as mock_session_class:

        # Setup mock stdio context
        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (MagicMock(), MagicMock())

        # Setup mock session
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))

        # Mock tool call result
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Tool execution result")]
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        # Create client and connect
        client = MCPClient(server_params)
        await client.connect()

        # Call tool
        result = await client.call_tool("test_tool", {"param": "value"})

        # Verify call was made
        mock_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})
        assert result == "Tool execution result"


@pytest.mark.asyncio
async def test_mcp_client_close():
    """Test MCP client closes connections properly."""
    from src.mcp.client import MCPClient

    server_params = {"command": "python"}

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

        # Create client and connect
        client = MCPClient(server_params)
        await client.connect()

        # Close client
        await client.close()

        # Verify cleanup
        mock_session.__aexit__.assert_called_once_with(None, None, None)
        mock_stdio_context.__aexit__.assert_called_once_with(None, None, None)

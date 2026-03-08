"""MCP client wrapper."""

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import Tool
from typing import List, Dict, Any


class MCPClient:
    """Wrapper for MCP server connection and tool execution."""

    def __init__(self, server_params: Dict[str, Any]):
        """Initialize MCP client with server parameters."""
        self.server_params = server_params
        self.session: ClientSession = None
        self.tools: List[Tool] = []

    async def connect(self):
        """Connect to MCP server and initialize session."""
        server_params = StdioServerParameters(
            command=self.server_params["command"],
            args=self.server_params.get("args", []),
            env=self.server_params.get("env")
        )

        self.stdio_context = stdio_client(server_params)
        read, write = await self.stdio_context.__aenter__()

        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

        self.tools = (await self.session.list_tools()).tools

    async def call_tool(self, name: str, arguments: Dict) -> str:
        """Execute a tool and return result text."""
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text

    async def close(self):
        """Clean up connections."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_context'):
            await self.stdio_context.__aexit__(None, None, None)

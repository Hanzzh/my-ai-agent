"""MCP server loader for managing multiple servers."""

import logging
from typing import List, Dict, Tuple, Any
from .client import MCPClient
from ..base import ToolDescription

logger = logging.getLogger(__name__)


class MCPLoader:
    """Manages multiple MCP server connections.

    Implements the ToolSource protocol for integration with ToolRegistry.
    """

    def __init__(self, server_configs: List[Dict]):
        """Initialize MCP loader with list of server parameter dicts."""
        self.clients: List[MCPClient] = []
        for config in server_configs:
            self.clients.append(MCPClient(config))

    async def load(self) -> None:
        """Initialize/load tools from this source (ToolSource protocol).

        Alias for load_all() for backward compatibility.
        """
        await self.load_all()

    async def load_all(self):
        """Connect to all configured MCP servers."""
        for client in self.clients:
            await client.connect()

    def get_tools(self) -> List[ToolDescription]:
        """Return list of tools from this source (ToolSource protocol).

        Returns ToolDescription objects suitable for LLM consumption.
        """
        tools: List[ToolDescription] = []
        for client in self.clients:
            for tool in client.tools:
                tools.append(ToolDescription(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.inputSchema
                ))
        return tools

    def get_all_tools(self) -> Dict[str, Tuple[MCPClient, object]]:
        """Return mapping of tool_name -> (client, tool)."""
        tools = {}
        for client in self.clients:
            for tool in client.tools:
                tools[tool.name] = (client, tool)
        return tools

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name (ToolSource protocol).

        Args:
            name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result as string

        Raises:
            ValueError: If tool not found in any client
        """
        for client in self.clients:
            # Check if this client has the tool
            tool_names = [t.name for t in client.tools]
            if name in tool_names:
                return await client.call_tool(name, arguments)

        available = [t.name for t in self.get_tools()]
        raise ValueError(f"Tool '{name}' not found. Available: {available}")

    async def close(self) -> None:
        """Cleanup resources (ToolSource protocol).

        Alias for close_all() for backward compatibility.
        """
        await self.close_all()

    async def close_all(self):
        """Close all connections."""
        for client in self.clients:
            await client.close()

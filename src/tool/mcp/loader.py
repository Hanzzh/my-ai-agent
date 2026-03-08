"""MCP server loader for managing multiple servers."""

from .client import MCPClient
from typing import List, Dict, Tuple


class MCPLoader:
    """Manages multiple MCP server connections."""

    def __init__(self, server_configs: List[Dict]):
        """Initialize MCP loader with list of server parameter dicts."""
        self.clients: List[MCPClient] = []
        for config in server_configs:
            self.clients.append(MCPClient(config))

    async def load_all(self):
        """Connect to all configured MCP servers."""
        for client in self.clients:
            await client.connect()

    def get_all_tools(self) -> Dict[str, Tuple[MCPClient, object]]:
        """Return mapping of tool_name -> (client, tool)."""
        tools = {}
        for client in self.clients:
            for tool in client.tools:
                tools[tool.name] = (client, tool)
        return tools

    async def close_all(self):
        """Close all connections."""
        for client in self.clients:
            await client.close()

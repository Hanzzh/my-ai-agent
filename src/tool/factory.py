"""Factory for creating configured tool registries."""

from typing import List, Dict
from .registry import ToolRegistry
from .mcp import MCPLoader
from .embedded import EmbeddedToolSource


def create_tool_registry(
    mcp_servers: List[Dict],
    permissions_path: str = "permissions.yaml"
) -> ToolRegistry:
    """Create a ToolRegistry with all sources configured.

    Args:
        mcp_servers: List of MCP server configurations
        permissions_path: Path to permissions.yaml file

    Returns:
        Configured ToolRegistry ready to be loaded
    """
    registry = ToolRegistry()

    # Add MCP source
    mcp_loader = MCPLoader(mcp_servers)
    registry.add_source(mcp_loader)

    # Add embedded tools source
    embedded_source = EmbeddedToolSource(permissions_path)
    registry.add_source(embedded_source)

    return registry
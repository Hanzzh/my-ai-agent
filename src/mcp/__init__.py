"""MCP client and server integration.

.. deprecated::
    Use :mod:`src.tool.mcp` instead. This module redirects to the new location.
"""

from src.tool.mcp import MCPClient, MCPLoader

__all__ = ['MCPClient', 'MCPLoader']
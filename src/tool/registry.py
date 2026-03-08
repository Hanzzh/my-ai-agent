"""Tool registry for aggregating tools from multiple sources."""

import logging
from typing import Protocol, List, Dict, Any, Tuple
from .base import Tool, ToolDescription

logger = logging.getLogger(__name__)


class ToolSource(Protocol):
    """Protocol for things that provide tools."""

    async def load(self) -> None:
        """Initialize/load tools from this source."""
        ...

    def get_tools(self) -> List[ToolDescription]:
        """Return list of tools from this source."""
        ...

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name."""
        ...

    async def close(self) -> None:
        """Cleanup resources."""
        ...


class ToolRegistry:
    """
    Registry that aggregates tools from multiple sources (MCP, embedded, etc.).

    Agents use this to get tools without knowing where they come from.
    """

    def __init__(self):
        self._sources: List[ToolSource] = []
        self._tools_cache: List[ToolDescription] = []

    def add_source(self, source: ToolSource) -> None:
        """Add a tool source (MCP server, embedded tool, etc.)"""
        self._sources.append(source)
        logger.info(f"Added tool source: {source.__class__.__name__}")

    async def load_all(self) -> None:
        """Load tools from all sources."""
        for source in self._sources:
            await source.load()
        self._refresh_cache()
        logger.info(f"Loaded {len(self._tools_cache)} tools from {len(self._sources)} sources")

    def get_tools(self) -> List[ToolDescription]:
        """Return all available tools (for LLM consumption)."""
        return self._tools_cache

    def get_tool_names(self) -> List[str]:
        """Return list of all tool names."""
        return [t["name"] for t in self._tools_cache]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name across all sources."""
        for source in self._sources:
            tool_names = [t["name"] for t in source.get_tools()]
            if name in tool_names:
                return await source.execute(name, arguments)

        raise ValueError(f"Tool '{name}' not found. Available: {self.get_tool_names()}")

    async def close_all(self) -> None:
        """Close all sources."""
        for source in self._sources:
            await source.close()
        self._tools_cache = []

    def _refresh_cache(self) -> None:
        """Refresh the cached tool list from all sources."""
        self._tools_cache = []
        for source in self._sources:
            self._tools_cache.extend(source.get_tools())
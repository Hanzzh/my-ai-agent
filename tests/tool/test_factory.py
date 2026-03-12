"""Tests for tool factory."""

import pytest
from src.tool.factory import create_tool_registry
from src.tool.registry import ToolRegistry


def test_create_tool_registry_returns_registry():
    """Factory should return a ToolRegistry instance."""
    registry = create_tool_registry(mcp_servers=[])

    assert isinstance(registry, ToolRegistry)


def test_create_tool_registry_has_mcp_source():
    """Registry should have MCP source when servers provided."""
    registry = create_tool_registry(mcp_servers=[
        {"name": "test", "command": "echo", "args": [], "env": {}}
    ])

    assert len(registry._sources) >= 1


def test_create_tool_registry_has_embedded_source():
    """Registry should have embedded source."""
    registry = create_tool_registry(mcp_servers=[])

    source_types = [type(s).__name__ for s in registry._sources]
    assert "EmbeddedToolSource" in source_types
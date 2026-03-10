"""Tests for EmbeddedToolSource."""

import pytest
from src.tool.embedded.source import EmbeddedToolSource


@pytest.mark.asyncio
async def test_embedded_source_has_toolsource_methods():
    """EmbeddedToolSource should implement ToolSource protocol."""
    source = EmbeddedToolSource("/tmp/test_permissions.yaml")

    # Should have required methods
    assert hasattr(source, 'load')
    assert hasattr(source, 'get_tools')
    assert hasattr(source, 'execute')
    assert hasattr(source, 'close')

    # Should be callable
    assert callable(source.load)
    assert callable(source.get_tools)
    assert callable(source.execute)
    assert callable(source.close)
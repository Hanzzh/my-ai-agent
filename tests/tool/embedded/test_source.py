"""Tests for EmbeddedToolSource."""

import pytest
import tempfile
import os
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


@pytest.mark.asyncio
async def test_embedded_source_loads_permissions():
    """EmbeddedToolSource should load permissions from YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
allow:
  - Bash(ls)
  - Bash(cat)
forbid:
  - Bash(rm)
""")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        assert "ls" in source._allowed_commands
        assert "cat" in source._allowed_commands
        assert "rm" in source._forbidden_commands
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_creates_empty_config_if_missing():
    """EmbeddedToolSource should create empty permissions if file missing."""
    temp_path = "/tmp/nonexistent_permissions_12345.yaml"

    # Make sure file doesn't exist
    if os.path.exists(temp_path):
        os.unlink(temp_path)

    source = EmbeddedToolSource(temp_path)
    await source.load()

    assert source._allowed_commands == []
    assert source._forbidden_commands == []

    # Should create the file
    assert os.path.exists(temp_path)

    # Cleanup
    os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_parses_bash_tool_format():
    """EmbeddedToolSource should parse Bash(command) format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
allow:
  - Bash(git)
  - Bash(ls)
forbid:
  - Bash(passwd)
""")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        assert "git" in source._allowed_commands
        assert "ls" in source._allowed_commands
        assert "passwd" in source._forbidden_commands
        assert "Bash" not in source._allowed_commands  # Should extract just the command
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_returns_tool_descriptions():
    """EmbeddedToolSource should return ToolDescription list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("allow:\n  - Bash(echo)\nforbid: []\n")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()
        tools = source.get_tools()

        assert len(tools) == 1
        assert isinstance(tools[0], dict)
        assert tools[0]["name"] == "bash"
        assert "description" in tools[0]
        assert "inputSchema" in tools[0]
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_executes_tool():
    """EmbeddedToolSource should execute tools by name."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("allow:\n  - Bash(echo)\nforbid: []\n")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        result = await source.execute("bash", {"command": "echo test"})
        assert "test" in result
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_raises_for_unknown_tool():
    """EmbeddedToolSource should raise for unknown tool name."""
    source = EmbeddedToolSource()
    await source.load()

    with pytest.raises(ValueError, match="Unknown tool"):
        await source.execute("unknown_tool", {})
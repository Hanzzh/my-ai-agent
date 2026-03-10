"""Tests for BashTool."""

import pytest
from src.tool.embedded.bash import BashTool


def test_bash_tool_has_required_attributes():
    """BashTool should have name, description, and inputSchema."""
    tool = BashTool(allowed_commands=[], forbidden_commands=[])

    assert tool.name == "bash"
    assert "bash commands" in tool.description.lower()
    assert "command" in tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_bash_tool_denies_command_not_in_allowlist():
    """Commands not in allowlist should be denied."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])
    result = await tool.execute(command="pwd")

    assert "not allowed" in result.lower()
    assert "pwd" in result


@pytest.mark.asyncio
async def test_bash_tool_denies_forbidden_command():
    """Forbidden commands should be denied even if in allowlist."""
    tool = BashTool(allowed_commands=["rm"], forbidden_commands=["rm"])
    result = await tool.execute(command="rm file.txt")

    assert "forbidden" in result.lower()
    assert "rm" in result


@pytest.mark.asyncio
async def test_bash_tool_allows_command_in_allowlist():
    """Commands in allowlist (not forbidden) should be allowed."""
    tool = BashTool(allowed_commands=["echo"], forbidden_commands=[])
    # This will test actual execution in next task
    # For now, just check it doesn't return permission error
    result = await tool.execute(command="echo hello")
    # Should not contain permission denial message
    assert "not allowed" not in result.lower()
    assert "forbidden" not in result.lower()
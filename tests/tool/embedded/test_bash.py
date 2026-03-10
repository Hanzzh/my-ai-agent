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


@pytest.mark.asyncio
async def test_bash_tool_executes_allowed_command():
    """BashTool should execute allowed commands and return output."""
    tool = BashTool(allowed_commands=["echo"], forbidden_commands=[])
    result = await tool.execute(command="echo hello")

    assert "hello" in result


@pytest.mark.asyncio
async def test_bash_tool_returns_stdout_and_stderr():
    """BashTool should return both stdout and stderr combined."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])
    result = await tool.execute(command="ls /nonexistent_dir_12345")

    # ls should output error to stderr for nonexistent directory
    assert result  # Should have some output
    # The exit code and error message should be in output


@pytest.mark.asyncio
async def test_bash_tool_never_raises_exception():
    """BashTool should always return a string, never raise."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])

    # Even for failing commands
    result = await tool.execute(command="ls /nonexistent_dir_12345")
    assert isinstance(result, str)

    # Even for invalid commands
    result2 = await tool.execute(command="nonexistent_command_xyz")
    assert isinstance(result2, str)
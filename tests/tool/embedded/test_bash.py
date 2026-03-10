"""Tests for BashTool."""

import pytest
from src.tool.embedded.bash import BashTool


def test_bash_tool_has_required_attributes():
    """BashTool should have name, description, and inputSchema."""
    tool = BashTool(allowed_commands=[], forbidden_commands=[])

    assert tool.name == "bash"
    assert "bash commands" in tool.description.lower()
    assert "command" in tool.inputSchema["properties"]
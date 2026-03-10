"""Embedded bash tool for command execution."""

from typing import List


class BashTool:
    """Embedded tool for executing bash commands."""

    name: str = "bash"
    description: str = "Execute bash commands. Allowed commands are restricted by configuration."
    inputSchema: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            }
        },
        "required": ["command"]
    }

    def __init__(self, allowed_commands: List[str], forbidden_commands: List[str]):
        self.allowed_commands = allowed_commands
        self.forbidden_commands = forbidden_commands

    async def execute(self, command: str) -> str:
        """Execute a bash command if allowed."""
        raise NotImplementedError
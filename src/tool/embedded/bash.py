"""Embedded bash tool for command execution."""

from typing import List, Any


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

    async def execute(self, **kwargs: Any) -> str:
        """Execute a bash command if allowed.

        Args:
            **kwargs: Must contain 'command' key with the bash command to execute.

        Returns:
            Command output as string.

        Raises:
            ValueError: If 'command' is not provided in kwargs.
            NotImplementedError: Tool implementation not yet complete.
        """
        command = kwargs.get("command")
        if command is None:
            raise ValueError("Missing required argument: command")
        raise NotImplementedError
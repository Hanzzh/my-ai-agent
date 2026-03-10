"""Embedded bash tool for command execution."""

import asyncio
from typing import List, Any, Tuple


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

    def _parse_command_name(self, command: str) -> str:
        """Extract command name from command string."""
        return command.strip().split()[0] if command.strip() else ""

    def _check_permission(self, command: str) -> Tuple[bool, str]:
        """Check if command is allowed.

        Returns:
            Tuple of (is_allowed, error_message)
        """
        cmd_name = self._parse_command_name(command)

        # Forbid takes precedence
        if cmd_name in self.forbidden_commands:
            return False, f"Error: Command '{cmd_name}' is forbidden."

        # Check allowlist
        if cmd_name not in self.allowed_commands:
            allowed = ", ".join(self.allowed_commands) if self.allowed_commands else "none"
            return False, f"Error: Command '{cmd_name}' is not allowed. Allowed commands: {allowed}"

        return True, ""

    async def execute(self, **kwargs: Any) -> str:
        """Execute a bash command if allowed.

        Args:
            **kwargs: Must contain 'command' key with the bash command to execute.

        Returns:
            Command output as string. Returns error message if command is missing
            or execution fails.
        """
        command = kwargs.get("command")
        if command is None:
            return "Error: Missing required argument: command"

        is_allowed, error_msg = self._check_permission(command)
        if not is_allowed:
            return error_msg

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Combine stdout and stderr
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            result = output
            if error:
                result += error

            return result.strip() if result.strip() else "(no output)"

        except Exception as e:
            return f"Error executing command: {str(e)}"
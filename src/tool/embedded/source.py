"""Embedded tool source for ToolRegistry integration."""

import os
import re
from typing import List, Dict, Any
import yaml

from ..base import ToolDescription
from .bash import BashTool


class EmbeddedToolSource:
    """ToolSource implementation for embedded tools."""

    def __init__(self, permissions_path: str = "permissions.yaml"):
        self.permissions_path = permissions_path
        self._tools: List[BashTool] = []
        self._allowed_commands: List[str] = []
        self._forbidden_commands: List[str] = []

    def _parse_tool_permission(self, permission: str) -> tuple:
        """Parse 'Tool(command)' format into (tool_name, command).

        Returns:
            Tuple of (tool_name, command) or (tool_name, "") if invalid format.
        """
        match = re.match(r"(\w+)\((\w+)\)", permission.strip())
        if match:
            return match.group(1), match.group(2)
        return permission.strip(), ""

    async def load(self) -> None:
        """Load permissions and initialize tools."""
        # Create empty permissions file if not exists
        if not os.path.exists(self.permissions_path):
            with open(self.permissions_path, 'w') as f:
                yaml.dump({"allow": [], "forbid": []}, f)

        # Load permissions
        with open(self.permissions_path, 'r') as f:
            permissions = yaml.safe_load(f) or {}

        # Parse allow list
        for permission in permissions.get("allow", []):
            tool_name, command = self._parse_tool_permission(permission)
            if tool_name == "Bash" and command:
                self._allowed_commands.append(command)

        # Parse forbid list
        for permission in permissions.get("forbid", []):
            tool_name, command = self._parse_tool_permission(permission)
            if tool_name == "Bash" and command:
                self._forbidden_commands.append(command)

        # Create BashTool with parsed permissions
        bash_tool = BashTool(
            allowed_commands=self._allowed_commands,
            forbidden_commands=self._forbidden_commands
        )
        self._tools = [bash_tool]

    def get_tools(self) -> List[ToolDescription]:
        """Return list of embedded tools."""
        return [
            ToolDescription(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.inputSchema
            )
            for tool in self._tools
        ]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute an embedded tool by name."""
        for tool in self._tools:
            if tool.name == name:
                return await tool.execute(**arguments)

        raise ValueError(f"Unknown tool: {name}. Available: {[t.name for t in self._tools]}")

    async def close(self) -> None:
        """No cleanup needed for embedded tools."""
        pass
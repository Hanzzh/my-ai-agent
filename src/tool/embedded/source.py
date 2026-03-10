"""Embedded tool source for ToolRegistry integration."""

from typing import List, Dict, Any
from ..base import ToolDescription
from .bash import BashTool


class EmbeddedToolSource:
    """ToolSource implementation for embedded tools."""

    def __init__(self, permissions_path: str = "permissions.yaml"):
        self.permissions_path = permissions_path
        self._tools: List[BashTool] = []
        self._allowed_commands: List[str] = []
        self._forbidden_commands: List[str] = []

    async def load(self) -> None:
        """Load permissions and initialize tools."""
        raise NotImplementedError

    def get_tools(self) -> List[ToolDescription]:
        """Return list of embedded tools."""
        raise NotImplementedError

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute an embedded tool by name."""
        raise NotImplementedError

    async def close(self) -> None:
        """No cleanup needed for embedded tools."""
        pass
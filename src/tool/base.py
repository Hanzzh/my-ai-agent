"""Tool interface definitions."""

from typing import Protocol, Any, Dict
from typing_extensions import TypedDict


class ToolDescription(TypedDict):
    """Description of a tool for LLM consumption."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Tool(Protocol):
    """Protocol for all tools (MCP, embedded, etc.)."""

    name: str
    description: str
    inputSchema: Dict[str, Any]

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given arguments."""
        ...


class ToolResult:
    """Result from tool execution."""

    def __init__(self, name: str, result: str, error: str = None):
        self.name = name
        self.result = result
        self.error = error

    @property
    def is_error(self) -> bool:
        return self.error is not None
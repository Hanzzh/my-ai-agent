"""Agent factory and base class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..llm.base import LLMProvider
from ..tool.registry import ToolRegistry


class Agent(ABC):
    """Abstract base for all agent patterns."""

    @abstractmethod
    async def initialize(self):
        """Initialize the agent (connect to MCP servers, etc.)."""
        pass

    @abstractmethod
    async def run(self, question: str, **kwargs) -> str:
        """Run the agent with a question."""
        pass

    def clear_history(self) -> None:
        """Clear conversation history. Optional, default does nothing."""
        pass

    @property
    def history_length(self) -> int:
        """Number of message exchanges in the conversation. Default returns 0."""
        return 0


class AgentFactory:
    """Factory to create agents based on configuration."""

    @staticmethod
    def create_agent(
        agent_type: str,
        llm: LLMProvider,
        tool_registry: ToolRegistry = None,
        mcp_loader: Any = None,  # Deprecated, kept for backward compatibility
        verbose: bool = False,
        **kwargs
    ) -> Agent:
        """Create an agent instance based on type.

        Args:
            agent_type: Type of agent to create ("react")
            llm: LLM provider for generating responses
            tool_registry: ToolRegistry for accessing tools (preferred)
            mcp_loader: Deprecated - use tool_registry instead
            verbose: Whether to print intermediate steps
            **kwargs: Additional arguments passed to the agent
        """
        # Handle deprecated mcp_loader parameter
        if mcp_loader is not None and tool_registry is None:
            from ..tool import ToolRegistry
            tool_registry = ToolRegistry()
            tool_registry.add_source(mcp_loader)

        if agent_type == "react":
            from .react import ReActAgent
            return ReActAgent(
                llm=llm,
                tool_registry=tool_registry,
                verbose=verbose,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

"""Agent factory and base class."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..llm.base import LLMProvider
from ..tool.mcp.loader import MCPLoader


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
        mcp_loader: MCPLoader,
        verbose: bool = False,
        **kwargs
    ) -> Agent:
        """Create an agent instance based on type."""
        if agent_type == "react":
            from .react import ReActAgent
            # Pass verbose explicitly to ReActAgent
            return ReActAgent(
                llm=llm,
                mcp_loader=mcp_loader,
                verbose=verbose,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

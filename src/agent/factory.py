"""Agent factory and base class."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..llm.base import LLMProvider
from ..mcp.loader import MCPLoader


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


class AgentFactory:
    """Factory to create agents based on configuration."""

    @staticmethod
    def create_agent(
        agent_type: str,
        llm: LLMProvider,
        mcp_loader: MCPLoader,
        **kwargs
    ) -> Agent:
        """Create an agent instance based on type."""
        if agent_type == "react":
            from .react import ReActAgent
            return ReActAgent(llm=llm, mcp_loader=mcp_loader, **kwargs)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

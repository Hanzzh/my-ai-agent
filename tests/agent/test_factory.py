"""Tests for agent factory and base class."""

import pytest
from src.agent.factory import Agent, AgentFactory
from src.agent.react import ReActAgent
from src.llm.base import LLMProvider
from src.tool.mcp.loader import MCPLoader


# Mock LLM Provider for testing
class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def chat(self, messages, **kwargs):
        """Return mock response."""
        return "Mock response"

    def get_model_info(self):
        """Return mock model info."""
        return {"name": "mock-model", "provider": "test"}


# Mock Agent for testing
class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, llm, mcp_loader, **kwargs):
        """Initialize mock agent."""
        self.llm = llm
        self.mcp_loader = mcp_loader
        self.kwargs = kwargs
        self.initialized = False

    async def initialize(self):
        """Initialize mock agent."""
        self.initialized = True

    async def run(self, question, **kwargs):
        """Run mock agent."""
        return f"Mock answer to: {question}"


def test_agent_abstract_base():
    """Test that Agent is an abstract base class that cannot be instantiated."""
    with pytest.raises(TypeError):
        # Should raise TypeError because Agent is abstract
        Agent()


def test_agent_factory_unknown_type():
    """Test that AgentFactory raises ValueError for unknown agent types."""
    llm = MockLLMProvider()
    mcp_loader = MCPLoader([])

    with pytest.raises(ValueError, match="Unknown agent type: unknown"):
        AgentFactory.create_agent("unknown", llm=llm, mcp_loader=mcp_loader)


def test_agent_factory_create_react():
    """Test that AgentFactory can create a ReAct agent."""
    llm = MockLLMProvider()
    mcp_loader = MCPLoader([])

    agent = AgentFactory.create_agent("react", llm=llm, mcp_loader=mcp_loader)

    assert agent is not None
    assert hasattr(agent, 'initialize')
    assert hasattr(agent, 'run')
    assert isinstance(agent, ReActAgent)

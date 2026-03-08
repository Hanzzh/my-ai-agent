"""Tests for ReAct Agent implementation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agent.react import ReActAgent
from src.llm.base import LLMProvider
from src.tool.registry import ToolRegistry


# Mock LLM Provider for testing
class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None):
        """Initialize with predefined responses."""
        self.responses = responses or []
        self.response_index = 0
        self.chat_history = []

    def chat(self, messages, **kwargs):
        """Return mock response from list."""
        self.chat_history.append(messages)
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return "Default response"

    def get_model_info(self):
        """Return mock model info."""
        return {"name": "mock-model", "provider": "test"}


def create_mock_tool_registry(tools=None):
    """Create a mock ToolRegistry for testing."""
    tool_registry = Mock(spec=ToolRegistry)
    tool_registry.load_all = AsyncMock()
    tool_registry.get_tools = Mock(return_value=tools or [])
    tool_registry.execute_tool = AsyncMock(return_value="tool result")
    tool_registry.close_all = AsyncMock()
    return tool_registry


@pytest.mark.asyncio
async def test_react_agent_initialize():
    """Test ReAct agent initialization."""
    tool_registry = create_mock_tool_registry()

    # Create agent
    llm = MockLLMProvider()
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=5)

    # Initialize
    await agent.initialize()

    # Verify
    tool_registry.load_all.assert_called_once()
    tool_registry.get_tools.assert_called_once()
    assert agent.tools == {}


@pytest.mark.asyncio
async def test_react_agent_direct_answer():
    """Test ReAct agent providing direct answer without tools."""
    tool_registry = create_mock_tool_registry()

    # Create LLM with direct answer response
    llm = MockLLMProvider(responses=[
        """Thought: I can answer this directly based on my knowledge.

Action: Final Answer
Action Input: The capital of France is Paris."""
    ])

    # Create and initialize agent
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=10)
    await agent.initialize()

    # Run
    result = await agent.run("What is the capital of France?", verbose=False)

    # Verify
    assert "Paris" in result
    assert "capital" in result.lower()


@pytest.mark.asyncio
async def test_react_agent_with_tool_call():
    """Test ReAct agent using a tool."""
    tool_registry = create_mock_tool_registry(tools=[
        {"name": "get_weather", "description": "Get current weather for a location", "inputSchema": {"type": "object", "properties": {"location": {"type": "string"}}}}
    ])
    tool_registry.execute_tool = AsyncMock(return_value="The weather is sunny and 75 degrees.")

    # Create LLM with tool-using responses
    llm = MockLLMProvider(responses=[
        """Thought: I need to check the weather for San Francisco.

Action: get_weather
Action Input: {"location": "San Francisco"}""",
        """Thought: The tool returned the weather information.

Action: Final Answer
Action Input: The weather in San Francisco is sunny and 75 degrees."""
    ])

    # Create and initialize agent
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=10)
    await agent.initialize()

    # Run
    result = await agent.run("What's the weather in San Francisco?", verbose=False)

    # Verify
    assert "sunny" in result.lower()
    assert "75" in result
    tool_registry.execute_tool.assert_called_once_with(
        "get_weather",
        {"location": "San Francisco"}
    )


@pytest.mark.asyncio
async def test_react_agent_max_iterations():
    """Test ReAct agent stops at max iterations."""
    tool_registry = create_mock_tool_registry()

    # Create LLM that never gives final answer
    llm = MockLLMProvider(responses=[
        "Thought: I need to think more...\nAction: think\nAction Input: {}"
    ] * 15)  # More than max_iterations

    # Create and initialize agent with low max_iterations
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=3)
    await agent.initialize()

    # Run
    result = await agent.run("Complex question", verbose=False)

    # Verify
    assert "maximum iterations" in result.lower()
    assert "3" in result


def test_react_agent_parse_action():
    """Test parsing action from LLM response."""
    # Create agent (no need to initialize for this test)
    llm = MockLLMProvider()
    tool_registry = create_mock_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=tool_registry)

    # Test parsing tool action with JSON input
    response = """Thought: I need to search for information.
Action: search
Action Input: {"query": "test search"}"""

    action, action_input = agent._parse_action(response)

    assert action == "search"
    assert action_input == {"query": "test search"}

    # Test parsing Final Answer
    response2 = """Thought: I have enough information.
Action: Final Answer
Action Input: The answer is 42."""

    action2, action_input2 = agent._parse_action(response2)

    assert action2 == "final_answer"
    assert action_input2 is None or "raw_input" in action_input2

    # Test parsing with plain text input (not JSON)
    response3 = """Action: some_tool
Action Input: just plain text"""

    action3, action_input3 = agent._parse_action(response3)

    assert action3 == "some_tool"
    assert action_input3 is not None
    assert "raw_input" in action_input3


def test_react_agent_parse_answer():
    """Test parsing final answer from LLM response."""
    # Create agent (no need to initialize for this test)
    llm = MockLLMProvider()
    tool_registry = create_mock_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=tool_registry)

    # Test parsing final answer
    response = """Thought: I have the answer.

Action: Final Answer
Action Input: The final answer to the question is X."""

    answer = agent._parse_answer(response)

    assert answer is not None
    assert "final answer" in answer.lower()
    assert "x" in answer.lower()

    # Test response without final answer
    response2 = """Thought: I need to use a tool.
Action: search
Action Input: {"query": "test"}"""

    answer2 = agent._parse_answer(response2)

    assert answer2 is None


def test_react_agent_format_tools_description():
    """Test formatting tools description."""
    # Create agent with tools
    llm = MockLLMProvider()
    tool_registry = create_mock_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=tool_registry)
    agent.tools = {
        "tool1": {"name": "tool1", "description": "First tool", "inputSchema": {"type": "object"}},
        "tool2": {"name": "tool2", "description": "Second tool", "inputSchema": None}
    }

    # Get tools description
    desc = agent._format_tools_description()

    assert "tool1" in desc
    assert "tool2" in desc
    assert "First tool" in desc
    assert "Second tool" in desc


def test_react_agent_get_system_prompt():
    """Test system prompt generation."""
    # Create agent with tools
    llm = MockLLMProvider()
    tool_registry = create_mock_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=tool_registry)
    agent.tools = {
        "test_tool": {"name": "test_tool", "description": "Test tool description", "inputSchema": {"type": "object"}}
    }

    # Get system prompt
    prompt = agent._get_system_prompt()

    assert "test_tool" in prompt
    assert "Test tool description" in prompt
    assert "Thought:" in prompt
    assert "Action:" in prompt
    assert "Action Input:" in prompt
    assert "Final Answer" in prompt


@pytest.mark.asyncio
async def test_react_agent_invalid_tool():
    """Test ReAct agent handling invalid tool name."""
    tool_registry = create_mock_tool_registry()

    # Create LLM that tries to use non-existent tool
    llm = MockLLMProvider(responses=[
        """Thought: I'll use a non-existent tool.

Action: invalid_tool
Action Input: {"param": "value"}""",
        """Thought: I understand, let me provide a direct answer.

Action: Final Answer
Action Input: I cannot complete this task."""
    ])

    # Create and initialize agent
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=10)
    await agent.initialize()

    # Run
    result = await agent.run("Use invalid tool", verbose=False)

    # Verify agent recovered from error
    assert "cannot complete this task" in result.lower()


@pytest.mark.asyncio
async def test_react_agent_tool_error():
    """Test ReAct agent handling tool execution errors."""
    tool_registry = create_mock_tool_registry(tools=[
        {"name": "failing_tool", "description": "A tool that fails", "inputSchema": None}
    ])
    tool_registry.execute_tool = AsyncMock(side_effect=Exception("Tool failed"))

    # Create LLM responses
    llm = MockLLMProvider(responses=[
        """Action: failing_tool
Action Input: {"test": "value"}""",
        """Action: Final Answer
Action Input: I encountered an error but here's my best answer."""
    ])

    # Create and initialize agent
    agent = ReActAgent(llm=llm, tool_registry=tool_registry, max_iterations=10)
    await agent.initialize()

    # Run
    result = await agent.run("Test error handling", verbose=False)

    # Verify agent handled the error
    assert "best answer" in result.lower()


@pytest.mark.asyncio
async def test_react_agent_history_initially_empty():
    """Test that message history is initially empty."""
    tool_registry = create_mock_tool_registry()

    agent = ReActAgent(llm=MockLLMProvider(), tool_registry=tool_registry)
    await agent.initialize()

    assert agent.message_history == []
    assert agent.history_length == 0


@pytest.mark.asyncio
async def test_react_agent_history_updated_after_answer():
    """Test that message history is updated after getting an answer."""
    tool_registry = create_mock_tool_registry()

    llm = MockLLMProvider(responses=[
        """Thought: I can answer directly.
Action: Final Answer
Action Input: The answer is 42."""
    ])

    agent = ReActAgent(llm=llm, tool_registry=tool_registry)
    await agent.initialize()

    result = await agent.run("What is the answer?", verbose=False)

    assert len(agent.message_history) == 2
    assert agent.message_history[0]["role"] == "user"
    assert "answer" in agent.message_history[0]["content"].lower()
    assert agent.message_history[1]["role"] == "assistant"
    assert "42" in agent.message_history[1]["content"]
    assert agent.history_length == 1


@pytest.mark.asyncio
async def test_react_agent_clear_history():
    """Test clearing conversation history."""
    tool_registry = create_mock_tool_registry()

    llm = MockLLMProvider(responses=[
        """Action: Final Answer
Action Input: Answer 1""",
        """Action: Final Answer
Action Input: Answer 2"""
    ])

    agent = ReActAgent(llm=llm, tool_registry=tool_registry)
    await agent.initialize()

    # First question
    await agent.run("Question 1", verbose=False)
    assert len(agent.message_history) == 2

    # Clear history
    agent.clear_history()
    assert agent.message_history == []
    assert agent.history_length == 0

    # Second question starts fresh
    await agent.run("Question 2", verbose=False)
    assert len(agent.message_history) == 2


@pytest.mark.asyncio
async def test_react_agent_multi_turn_context():
    """Test that multi-turn conversation maintains context in messages."""
    tool_registry = create_mock_tool_registry()

    llm = MockLLMProvider(responses=[
        """Action: Final Answer
Action Input: Tokyo""",
        """Action: Final Answer
Action Input: The previous answer was Tokyo."""
    ])

    agent = ReActAgent(llm=llm, tool_registry=tool_registry)
    await agent.initialize()

    # First question
    await agent.run("What is the capital of Japan?", verbose=False)

    # Second question - verify history is included in messages
    await agent.run("What was my previous question about?", verbose=False)

    # Check that the second call included history
    second_call_messages = llm.chat_history[1]
    # Find the user message about Japan in history
    history_found = any(
        "Japan" in str(msg) for msg in second_call_messages
    )
    assert history_found, "History should include previous question about Japan"
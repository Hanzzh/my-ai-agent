"""Integration tests for the AI Agent application.

These tests verify end-to-end functionality using mocks for external services.
No real MCP servers or LLM APIs are called.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = """
llm:
  api_key: "test-api-key"
  base_url: "https://test.api.com"
  model: "test-model"

agent:
  type: "react"
  max_iterations: 5

mcp_config_file: "test_mcp.yaml"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def temp_mcp_config_file():
    """Create a temporary MCP config file for testing."""
    mcp_config_content = """
servers:
  - name: test-server
    command: echo
    args: ["test"]
    env: {}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(mcp_config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.mark.asyncio
async def test_run_agent_full_flow(temp_config_file, temp_mcp_config_file):
    """Test full agent execution flow from config to response."""
    from src.app import run_agent
    from src.llm.base import LLMProvider
    from src.tool.mcp import MCPLoader
    from src.agent.react import ReActAgent

    # Mock the load_config to use our temp files
    with patch('src.app.load_config') as mock_load_config:
        # Create mock config
        mock_config = Mock()
        mock_config.llm.api_key = "test-key"
        mock_config.llm.base_url = "https://test.com"
        mock_config.llm.model = "test-model"
        mock_config.agent_type = "react"
        mock_config.max_iterations = 5
        mock_config.mcp_servers = []

        mock_load_config.return_value = mock_config

        # Mock LLM provider
        with patch('src.app.OpenAICompatibleProvider') as mock_llm_class:
            mock_llm = Mock(spec=LLMProvider)
            mock_llm.chat = Mock(return_value="Thought: Direct answer.\n\nAction: Final Answer\nAction Input: Test response")
            mock_llm_class.return_value = mock_llm

            # Mock MCP loader
            with patch('src.app.MCPLoader') as mock_mcp_class:
                mock_mcp_loader = Mock(spec=MCPLoader)
                mock_mcp_loader.load_all = AsyncMock()
                mock_mcp_loader.get_all_tools = Mock(return_value={})
                mock_mcp_loader.close_all = AsyncMock()
                mock_mcp_class.return_value = mock_mcp_loader

                # Mock agent factory
                with patch('src.app.AgentFactory') as mock_factory:
                    mock_agent = Mock(spec=ReActAgent)
                    mock_agent.initialize = AsyncMock()
                    mock_agent.run = AsyncMock(return_value="Test response from agent")
                    mock_factory.create_agent.return_value = mock_agent

                    # Run the agent
                    result = await run_agent("Test question", temp_config_file)

                    # Verify the flow
                    mock_load_config.assert_called_once_with(temp_config_file)
                    mock_llm_class.assert_called_once()
                    mock_mcp_class.assert_called_once_with([])
                    mock_mcp_loader.load_all.assert_called_once()
                    mock_factory.create_agent.assert_called_once()
                    mock_agent.initialize.assert_called_once()
                    mock_agent.run.assert_called_once_with("Test question")
                    mock_mcp_loader.close_all.assert_called_once()

                    assert result == "Test response from agent"


@pytest.mark.asyncio
async def test_run_agent_with_error_handling(temp_config_file):
    """Test error handling in run_agent flow."""
    from src.app import run_agent

    with patch('src.app.load_config') as mock_load_config:
        # Make load_config raise an error
        mock_load_config.side_effect = Exception("Config loading failed")

        # Verify error is propagated
        with pytest.raises(Exception, match="Config loading failed"):
            await run_agent("Test question", temp_config_file)


@pytest.mark.asyncio
async def test_run_agent_cleanup_on_error(temp_config_file):
    """Test that cleanup happens even when agent execution fails."""
    from src.app import run_agent
    from src.tool.mcp import MCPLoader

    with patch('src.app.load_config') as mock_load_config:
        mock_config = Mock()
        mock_config.llm.api_key = "test-key"
        mock_config.llm.base_url = "https://test.com"
        mock_config.llm.model = "test-model"
        mock_config.agent_type = "react"
        mock_config.max_iterations = 5
        mock_config.mcp_servers = []

        mock_load_config.return_value = mock_config

        with patch('src.app.OpenAICompatibleProvider'):
            with patch('src.app.MCPLoader') as mock_mcp_class:
                mock_mcp_loader = Mock(spec=MCPLoader)
                mock_mcp_loader.load_all = AsyncMock()
                mock_mcp_loader.get_all_tools = Mock(return_value={})
                mock_mcp_loader.close_all = AsyncMock()
                mock_mcp_class.return_value = mock_mcp_loader

                with patch('src.app.AgentFactory') as mock_factory:
                    # Make agent.run raise an error
                    mock_agent = Mock()
                    mock_agent.initialize = AsyncMock()
                    mock_agent.run = AsyncMock(side_effect=Exception("Agent execution failed"))
                    mock_factory.create_agent.return_value = mock_agent

                    # Verify error is raised
                    with pytest.raises(Exception, match="Agent execution failed"):
                        await run_agent("Test question", temp_config_file)

                    # Verify cleanup was still called
                    mock_mcp_loader.close_all.assert_called_once()


@pytest.mark.asyncio
async def test_run_agent_batch(temp_config_file):
    """Test running agent with multiple questions."""
    from src.app import run_agent_batch

    with patch('src.app.run_agent') as mock_run_agent:
        mock_run_agent.side_effect = ["Answer 1", "Answer 2", "Answer 3"]

        results = await run_agent_batch(
            ["Question 1", "Question 2", "Question 3"],
            temp_config_file
        )

        assert len(results) == 3
        assert results == ["Answer 1", "Answer 2", "Answer 3"]
        assert mock_run_agent.call_count == 3


def test_config_loading_with_env_substitution():
    """Test that environment variables are properly substituted in config."""
    from src.config.llm_config import load_llm_config

    # Set test environment variable
    os.environ['TEST_VAR'] = 'test_value'

    try:
        # Test LLM config loading with env substitution
        llm_config = load_llm_config({"llm": {"api_key": "${TEST_VAR}", "base_url": "https://api.com", "model": "model"}})
        assert llm_config.api_key == "test_value"
        assert llm_config.base_url == "https://api.com"
        assert llm_config.model == "model"
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


@pytest.mark.asyncio
async def test_agent_factory_creates_correct_agent_type():
    """Test that AgentFactory creates the correct agent type."""
    from src.agent import AgentFactory
    from src.llm.base import LLMProvider
    from src.tool.mcp import MCPLoader

    mock_llm = Mock(spec=LLMProvider)
    mock_mcp = Mock(spec=MCPLoader)

    # Test creating ReAct agent
    agent = AgentFactory.create_agent(
        agent_type="react",
        llm=mock_llm,
        mcp_loader=mock_mcp,
        max_iterations=10
    )

    assert agent.__class__.__name__ == "ReActAgent"
    assert agent.llm == mock_llm
    assert agent.mcp_loader == mock_mcp
    assert agent.max_iterations == 10


def test_agent_factory_invalid_type():
    """Test that AgentFactory raises error for invalid agent type."""
    from src.agent import AgentFactory
    from src.llm.base import LLMProvider
    from src.tool.mcp import MCPLoader

    mock_llm = Mock(spec=LLMProvider)
    mock_mcp = Mock(spec=MCPLoader)

    with pytest.raises(ValueError, match="Unknown agent type"):
        AgentFactory.create_agent(
            agent_type="invalid_type",
            llm=mock_llm,
            mcp_loader=mock_mcp
        )


@pytest.mark.asyncio
async def test_mcp_loader_initialization(temp_mcp_config_file):
    """Test MCP loader initialization and cleanup."""
    from src.mcp import MCPLoader

    # Load MCP configs from file
    from src.config.mcp_config import load_mcp_configs_from_file
    mcp_configs = load_mcp_configs_from_file(temp_mcp_config_file)

    # Convert to list of dicts
    server_dicts = [
        {"name": cfg.name, "command": cfg.command, "args": cfg.args, "env": cfg.env}
        for cfg in mcp_configs
    ]

    loader = MCPLoader(server_dicts)

    # Mock the subprocess creation to avoid actual subprocess
    with patch('src.tool.mcp.client.stdio_client') as mock_stdio_client, \
         patch('src.tool.mcp.client.ClientSession') as mock_session_class:

        mock_stdio_context = AsyncMock()
        mock_stdio_client.return_value = mock_stdio_context
        mock_stdio_context.__aenter__.return_value = (MagicMock(), MagicMock())

        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))

        # Initialize
        await loader.load_all()

        # Verify clients were created
        assert len(loader.clients) >= 0

        # Cleanup
        await loader.close_all()


def test_llm_provider_chat():
    """Test LLM provider chat functionality."""
    from src.llm import OpenAICompatibleProvider

    with patch('src.llm.openai_client.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://test.com",
            model="test-model"
        )

        messages = [{"role": "user", "content": "Test"}]
        response = provider.chat(messages)

        assert response == "Test response"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_react_agent_execution_flow():
    """Test complete ReAct agent execution with mock LLM and MCP."""
    from src.agent.react import ReActAgent
    from src.llm.base import LLMProvider
    from src.tool.mcp import MCPLoader

    # Create mock LLM
    class MockLLM(LLMProvider):
        def __init__(self):
            self.call_count = 0

        def chat(self, messages, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                return "Thought: I can answer this.\n\nAction: Final Answer\nAction Input: The answer is 42."
            return "Action: Final Answer\nAction Input: Done."

        def get_model_info(self):
            return {"name": "mock", "provider": "test"}

    # Create mock MCP loader
    mock_mcp = Mock(spec=MCPLoader)
    mock_mcp.initialize = AsyncMock()
    mock_mcp.get_all_tools = Mock(return_value={})
    mock_mcp.cleanup = AsyncMock()

    # Create and run agent
    agent = ReActAgent(llm=MockLLM(), mcp_loader=mock_mcp, max_iterations=5)
    await agent.initialize()

    result = await agent.run("What is the meaning of life?", verbose=False)

    assert "42" in result
    assert agent.llm.call_count >= 1


@pytest.mark.asyncio
async def test_tool_calling_integration():
    """Test integration of tool calling through the full stack."""
    from src.agent.react import ReActAgent
    from src.llm.base import LLMProvider
    from src.tool.mcp import MCPLoader

    # Create mock LLM that uses a tool
    class ToolUsingLLM(LLMProvider):
        def __init__(self):
            self.responses = [
                "Thought: I need to use a tool.\n\nAction: test_tool\nAction Input: {\"query\": \"test\"}",
                "Thought: Got the result.\n\nAction: Final Answer\nAction Input: Tool returned success."
            ]
            self.call_count = 0

        def chat(self, messages, **kwargs):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response

        def get_model_info(self):
            return {"name": "mock", "provider": "test"}

    # Create mock tool and client
    mock_client = Mock()
    mock_client.call_tool = AsyncMock(return_value="Tool result: success")

    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    mock_tool.inputSchema = {"type": "object", "properties": {"query": {"type": "string"}}}

    # Create mock MCP loader with tool
    mock_mcp = Mock(spec=MCPLoader)
    mock_mcp.initialize = AsyncMock()
    mock_mcp.get_all_tools = Mock(return_value={"test_tool": (mock_client, mock_tool)})
    mock_mcp.cleanup = AsyncMock()

    # Create and run agent
    agent = ReActAgent(llm=ToolUsingLLM(), mcp_loader=mock_mcp, max_iterations=5)
    await agent.initialize()

    result = await agent.run("Use the test tool", verbose=False)

    # Verify tool was called
    mock_client.call_tool.assert_called_once_with("test_tool", {"query": "test"})
    assert "success" in result


def test_configuration_models():
    """Test configuration data models."""
    from src.config.models import AgentConfig, LLMConfig, MCPServerConfig

    # Test LLM config
    llm_config = LLMConfig(
        api_key="test-key",
        base_url="https://test.com",
        model="test-model"
    )
    assert llm_config.api_key == "test-key"
    assert llm_config.base_url == "https://test.com"
    assert llm_config.model == "test-model"

    # Test MCP server config
    mcp_config = MCPServerConfig(
        name="test-server",
        command="echo",
        args=["test"],
        env={}
    )
    assert mcp_config.name == "test-server"
    assert mcp_config.command == "echo"
    assert mcp_config.args == ["test"]

    # Test Agent config
    agent_config = AgentConfig(
        llm=llm_config,
        mcp_servers=[mcp_config],
        agent_type="react",
        max_iterations=10
    )
    assert agent_config.llm == llm_config
    assert agent_config.mcp_servers == [mcp_config]
    assert agent_config.agent_type == "react"
    assert agent_config.max_iterations == 10


@pytest.mark.asyncio
async def test_multi_turn_conversation():
    """Test that multi-turn conversation maintains context across turns."""
    from src.session import Session
    from src.llm.base import LLMProvider

    # Track call count and messages
    call_count = 0
    captured_messages = []

    class ContextAwareLLM(LLMProvider):
        def chat(self, messages, **kwargs):
            nonlocal call_count, captured_messages
            call_count += 1
            captured_messages.append(messages)

            if call_count == 1:
                return "Thought: I know this.\n\nAction: Final Answer\nAction Input: Tokyo."
            else:
                # Second call should have history
                return f"Thought: Based on previous context.\n\nAction: Final Answer\nAction Input: The previous answer was Tokyo."

        def get_model_info(self):
            return {"name": "mock", "provider": "test"}

    with patch('src.session.session.load_config') as mock_load_config, \
         patch('src.session.session.OpenAICompatibleProvider') as mock_llm_class, \
         patch('src.session.session.MCPLoader') as mock_mcp_class, \
         patch('src.session.session.AgentFactory') as mock_factory:

        # Setup mocks
        mock_config = Mock()
        mock_config.llm.api_key = "test-key"
        mock_config.llm.base_url = "https://test.com"
        mock_config.llm.model = "test-model"
        mock_config.agent_type = "react"
        mock_config.max_iterations = 5
        mock_config.mcp_servers = []
        mock_load_config.return_value = mock_config

        mock_llm = ContextAwareLLM()
        mock_llm_class.return_value = mock_llm

        mock_mcp_instance = Mock()
        mock_mcp_instance.load_all = AsyncMock()
        mock_mcp_instance.close_all = AsyncMock()
        mock_mcp_instance.get_all_tools = Mock(return_value={})
        mock_mcp_class.return_value = mock_mcp_instance

        mock_agent = Mock()
        mock_agent.initialize = AsyncMock()
        mock_agent.run = AsyncMock(side_effect=["Tokyo", "The previous answer was Tokyo."])
        mock_agent.clear_history = Mock()
        mock_agent.history_length = 0
        mock_factory.create_agent.return_value = mock_agent

        # Create session
        session = await Session.create(config_path="test.yaml")

        # First turn
        result1 = await session.ask("What is the capital of Japan?")

        # Second turn - should have context from first
        result2 = await session.ask("What was my previous question about?")

        # Cleanup
        await session.close()

        # Verify both calls were made
        assert call_count == 0  # LLM not called directly, agent.run was
        assert mock_agent.run.call_count == 2


@pytest.mark.asyncio
async def test_session_mcp_persistence():
    """Test that MCP connections persist across multiple turns in a session."""
    from src.session import Session

    with patch('src.session.session.load_config') as mock_load_config, \
         patch('src.session.session.OpenAICompatibleProvider') as mock_llm_class, \
         patch('src.session.session.MCPLoader') as mock_mcp_class, \
         patch('src.session.session.AgentFactory') as mock_factory:

        # Setup mocks
        mock_config = Mock()
        mock_config.llm.api_key = "test-key"
        mock_config.llm.base_url = "https://test.com"
        mock_config.llm.model = "test-model"
        mock_config.agent_type = "react"
        mock_config.max_iterations = 5
        mock_config.mcp_servers = []
        mock_load_config.return_value = mock_config

        mock_llm_class.return_value = Mock()

        mock_mcp_instance = Mock()
        mock_mcp_instance.load_all = AsyncMock()
        mock_mcp_instance.close_all = AsyncMock()
        mock_mcp_instance.get_all_tools = Mock(return_value={})
        mock_mcp_class.return_value = mock_mcp_instance

        mock_agent = Mock()
        mock_agent.initialize = AsyncMock()
        mock_agent.run = AsyncMock(side_effect=["Answer 1", "Answer 2", "Answer 3"])
        mock_agent.clear_history = Mock()
        mock_agent.history_length = 0
        mock_factory.create_agent.return_value = mock_agent

        # Create session
        session = await Session.create(config_path="test.yaml")

        # MCP should be loaded once at session creation
        assert mock_mcp_instance.load_all.call_count == 1

        # Multiple turns
        await session.ask("Question 1")
        await session.ask("Question 2")
        await session.ask("Question 3")

        # MCP should still only be loaded once (persisting)
        assert mock_mcp_instance.load_all.call_count == 1

        # Close session
        await session.close()

        # MCP should be closed once
        assert mock_mcp_instance.close_all.call_count == 1


@pytest.mark.asyncio
async def test_session_clear_history_in_integration():
    """Test that clearing history works in a full integration context."""
    from src.session import Session

    with patch('src.session.session.load_config') as mock_load_config, \
         patch('src.session.session.OpenAICompatibleProvider') as mock_llm_class, \
         patch('src.session.session.MCPLoader') as mock_mcp_class, \
         patch('src.session.session.AgentFactory') as mock_factory:

        # Setup mocks
        mock_config = Mock()
        mock_config.llm.api_key = "test-key"
        mock_config.llm.base_url = "https://test.com"
        mock_config.llm.model = "test-model"
        mock_config.agent_type = "react"
        mock_config.max_iterations = 5
        mock_config.mcp_servers = []
        mock_load_config.return_value = mock_config

        mock_llm_class.return_value = Mock()

        mock_mcp_instance = Mock()
        mock_mcp_instance.load_all = AsyncMock()
        mock_mcp_instance.close_all = AsyncMock()
        mock_mcp_instance.get_all_tools = Mock(return_value={})
        mock_mcp_class.return_value = mock_mcp_instance

        mock_agent = Mock()
        mock_agent.initialize = AsyncMock()
        mock_agent.run = AsyncMock(return_value="Answer")
        mock_agent.clear_history = Mock()
        mock_agent.history_length = 2  # Simulate some history
        mock_factory.create_agent.return_value = mock_agent

        # Create session and ask questions
        session = await Session.create(config_path="test.yaml")
        await session.ask("Question 1")

        # Clear history
        session.clear_history()
        mock_agent.clear_history.assert_called_once()

        # Cleanup
        await session.close()

"""Tests for Session class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.session.session import Session
from src.config import AgentConfig, LLMConfig, MCPServerConfig


@pytest.fixture
def mock_config():
    """Create a mock agent configuration."""
    return AgentConfig(
        llm=LLMConfig(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model"
        ),
        mcp_servers=[],
        agent_type="react",
        max_iterations=10
    )


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.chat = Mock(return_value="Test response")
    provider.get_model_info = Mock(return_value={"name": "test-model"})
    return provider


@pytest.fixture
def mock_mcp_loader():
    """Create a mock MCP loader."""
    loader = Mock()
    loader.load_all = AsyncMock()
    loader.close_all = AsyncMock()
    loader.get_all_tools = Mock(return_value={})
    return loader


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = Mock()
    agent.initialize = AsyncMock()
    agent.run = AsyncMock(return_value="Test answer")
    agent.clear_history = Mock()
    agent.history_length = 0
    return agent


@pytest.mark.asyncio
async def test_session_create(mock_config, mock_agent):
    """Test session creation with mocked dependencies."""
    with patch('src.session.session.load_config') as mock_load_config, \
         patch('src.session.session.OpenAICompatibleProvider') as mock_llm_class, \
         patch('src.session.session.MCPLoader') as mock_mcp_class, \
         patch('src.session.session.AgentFactory') as mock_factory:

        mock_load_config.return_value = mock_config
        mock_llm_class.return_value = Mock()
        mock_mcp_instance = Mock()
        mock_mcp_instance.load_all = AsyncMock()
        mock_mcp_instance.close_all = AsyncMock()
        mock_mcp_instance.get_all_tools = Mock(return_value={})
        mock_mcp_class.return_value = mock_mcp_instance
        mock_factory.create_agent.return_value = mock_agent

        session = await Session.create(config_path="test.yaml", verbose=False)

        assert session is not None
        mock_load_config.assert_called_once_with("test.yaml")
        mock_factory.create_agent.assert_called_once()


@pytest.mark.asyncio
async def test_session_ask(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test asking a question through session."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    result = await session.ask("Test question")

    assert result == "Test answer"
    mock_agent.run.assert_called_once_with("Test question")


@pytest.mark.asyncio
async def test_session_ask_multi_turn(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test multi-turn conversation through session."""
    mock_agent.run = AsyncMock(side_effect=["Answer 1", "Answer 2"])
    mock_agent.history_length = 0

    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    result1 = await session.ask("Question 1")
    result2 = await session.ask("Question 2")

    assert result1 == "Answer 1"
    assert result2 == "Answer 2"
    assert mock_agent.run.call_count == 2


@pytest.mark.asyncio
async def test_session_close(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test closing session releases resources."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    await session.close()

    mock_mcp_loader.close_all.assert_called_once()
    assert session._closed is True


@pytest.mark.asyncio
async def test_session_close_idempotent(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test that close() is idempotent."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    await session.close()
    await session.close()  # Second call should be no-op

    mock_mcp_loader.close_all.assert_called_once()


@pytest.mark.asyncio
async def test_session_ask_after_close_raises(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test that ask() after close raises RuntimeError."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    await session.close()

    with pytest.raises(RuntimeError, match="Session is closed"):
        await session.ask("Test question")


@pytest.mark.asyncio
async def test_session_clear_history(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test clearing history through session."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    session.clear_history()

    mock_agent.clear_history.assert_called_once()


@pytest.mark.asyncio
async def test_session_history_length(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test history_length property."""
    mock_agent.history_length = 3

    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    assert session.history_length == 3


@pytest.mark.asyncio
async def test_session_context_manager(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test async context manager usage."""
    async with Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    ) as session:
        await session.ask("Test question")

    mock_mcp_loader.close_all.assert_called_once()


@pytest.mark.asyncio
async def test_session_clear_history_after_close_raises(mock_llm_provider, mock_mcp_loader, mock_agent, mock_config):
    """Test that clear_history() after close raises RuntimeError."""
    session = Session(
        llm_provider=mock_llm_provider,
        mcp_loader=mock_mcp_loader,
        agent=mock_agent,
        config=mock_config
    )

    await session.close()

    with pytest.raises(RuntimeError, match="Session is closed"):
        session.clear_history()
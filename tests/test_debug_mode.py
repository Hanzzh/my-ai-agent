"""Tests for debug mode functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import logging
import sys
from io import StringIO


@pytest.mark.asyncio
async def test_parse_args_with_question():
    """Test parsing args with a question."""
    from main import parse_args

    # Mock sys.argv
    with patch.object(sys, 'argv', ['main.py', 'test question']):
        args = parse_args()
        assert args.question == 'test question'
        assert args.debug is False


@pytest.mark.asyncio
async def test_parse_args_with_debug_flag():
    """Test parsing args with --debug flag."""
    from main import parse_args

    with patch.object(sys, 'argv', ['main.py', '--debug', 'test']):
        args = parse_args()
        assert args.question == 'test'
        assert args.debug is True


@pytest.mark.asyncio
async def test_parse_args_no_question():
    """Test parsing args without question (interactive mode)."""
    from main import parse_args

    with patch.object(sys, 'argv', ['main.py']):
        args = parse_args()
        assert args.question is None
        assert args.debug is False


@pytest.mark.asyncio
async def test_parse_args_debug_without_question():
    """Test parsing args with --debug flag but no question."""
    from main import parse_args

    with patch.object(sys, 'argv', ['main.py', '--debug']):
        args = parse_args()
        assert args.question is None
        assert args.debug is True


@pytest.mark.asyncio
async def test_configure_logging_debug_mode():
    """Test that debug mode sets DEBUG level."""
    from main import configure_logging

    configure_logging(debug_mode=True)
    assert logging.getLogger().level == logging.DEBUG


@pytest.mark.asyncio
async def test_configure_logging_silent_mode():
    """Test that silent mode sets WARNING level."""
    from main import configure_logging

    configure_logging(debug_mode=False)
    assert logging.getLogger().level == logging.WARNING


@pytest.mark.asyncio
async def test_run_agent_verbose_false():
    """Test run_agent with verbose=False."""
    from src.app import run_agent

    with patch('src.app.load_config') as mock_load_config, \
         patch('src.app.OpenAICompatibleProvider') as mock_llm, \
         patch('src.app.create_tool_registry') as mock_create_registry:

        # Setup mocks
        mock_config = MagicMock()
        mock_config.llm.api_key = "test"
        mock_config.llm.base_url = "http://test"
        mock_config.llm.model = "test-model"
        mock_config.mcp_servers = []
        mock_config.agent_type = "react"
        mock_config.max_iterations = 10
        mock_load_config.return_value = mock_config

        mock_llm_instance = MagicMock()
        # chat is synchronous, not async
        mock_llm_instance.chat = MagicMock(return_value="Action: Final Answer\nAction Input: Test answer")
        mock_llm.return_value = mock_llm_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.load_all = AsyncMock()
        mock_registry_instance.get_tools.return_value = []
        mock_registry_instance.close_all = AsyncMock()
        mock_create_registry.return_value = mock_registry_instance

        # Run with verbose=False
        result = await run_agent("test", verbose=False)

        # Verify result
        assert result == "Test answer"


@pytest.mark.asyncio
async def test_run_agent_verbose_true():
    """Test run_agent with verbose=True."""
    from src.app import run_agent

    with patch('src.app.load_config') as mock_load_config, \
         patch('src.app.OpenAICompatibleProvider') as mock_llm, \
         patch('src.app.create_tool_registry') as mock_create_registry:

        # Setup mocks
        mock_config = MagicMock()
        mock_config.llm.api_key = "test"
        mock_config.llm.base_url = "http://test"
        mock_config.llm.model = "test-model"
        mock_config.mcp_servers = []
        mock_config.agent_type = "react"
        mock_config.max_iterations = 10
        mock_load_config.return_value = mock_config

        mock_llm_instance = MagicMock()
        # chat is synchronous, not async
        mock_llm_instance.chat = MagicMock(return_value="Action: Final Answer\nAction Input: Test answer with verbose")
        mock_llm.return_value = mock_llm_instance

        mock_registry_instance = MagicMock()
        mock_registry_instance.load_all = AsyncMock()
        mock_registry_instance.get_tools.return_value = []
        mock_registry_instance.close_all = AsyncMock()
        mock_create_registry.return_value = mock_registry_instance

        # Run with verbose=True
        result = await run_agent("test", verbose=True)

        # Verify result
        assert result == "Test answer with verbose"


@pytest.mark.asyncio
async def test_agent_factory_with_verbose():
    """Test AgentFactory passes verbose to agent."""
    from src.agent.factory import AgentFactory
    from src.llm.base import LLMProvider
    from unittest.mock import MagicMock

    mock_llm = MagicMock(spec=LLMProvider)
    mock_mcp = MagicMock()

    # Create agent with verbose=False
    agent = AgentFactory.create_agent(
        "react",
        mock_llm,
        mock_mcp,
        verbose=False,
        max_iterations=5
    )

    # Verify agent received verbose parameter
    assert agent.verbose is False


@pytest.mark.asyncio
async def test_agent_factory_with_verbose_true():
    """Test AgentFactory passes verbose=True to agent."""
    from src.agent.factory import AgentFactory
    from src.llm.base import LLMProvider
    from unittest.mock import MagicMock

    mock_llm = MagicMock(spec=LLMProvider)
    mock_mcp = MagicMock()

    # Create agent with verbose=True
    agent = AgentFactory.create_agent(
        "react",
        mock_llm,
        mock_mcp,
        verbose=True,
        max_iterations=5
    )

    # Verify agent received verbose parameter
    assert agent.verbose is True


@pytest.mark.asyncio
async def test_react_agent_verbose_parameter():
    """Test ReActAgent accepts and stores verbose parameter."""
    from src.agent.react import ReActAgent
    from unittest.mock import MagicMock
    from src.llm.base import LLMProvider

    mock_llm = MagicMock(spec=LLMProvider)
    mock_mcp = MagicMock()

    # Create agent with verbose=True
    agent = ReActAgent(llm=mock_llm, mcp_loader=mock_mcp, verbose=True)
    assert agent.verbose is True

    # Create agent with verbose=False
    agent2 = ReActAgent(llm=mock_llm, mcp_loader=mock_mcp, verbose=False)
    assert agent2.verbose is False

    # Create agent with default verbose
    agent3 = ReActAgent(llm=mock_llm, mcp_loader=mock_mcp)
    assert agent3.verbose is False


@pytest.mark.asyncio
async def test_run_agent_batch_with_verbose():
    """Test run_agent_batch passes verbose parameter."""
    from src.app import run_agent_batch

    with patch('src.app.run_agent') as mock_run_agent:
        mock_run_agent.return_value = "Test response"

        # Run batch with verbose=True
        results = await run_agent_batch(
            ["question1", "question2"],
            verbose=True
        )

        # Verify run_agent was called with verbose=True
        assert mock_run_agent.call_count == 2
        for call in mock_run_agent.call_args_list:
            assert call.kwargs.get('verbose') is True or call.args[1] == 'config.yaml'


@pytest.mark.asyncio
async def test_logging_level_affects_output():
    """Test that logging level affects what gets logged."""
    from main import configure_logging
    import logging

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger('test_logger')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Test DEBUG mode
    configure_logging(debug_mode=True)
    logger.debug("Debug message")
    assert "Debug message" in log_capture.getvalue()

    # Clean up
    logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_configure_logging_resets_root_logger():
    """Test that configure_logging properly sets root logger level."""
    from main import configure_logging
    import logging

    root_logger = logging.getLogger()

    # Test DEBUG mode
    configure_logging(debug_mode=True)
    assert root_logger.level == logging.DEBUG

    # Test silent mode
    configure_logging(debug_mode=False)
    assert root_logger.level == logging.WARNING

    # Test DEBUG mode again
    configure_logging(debug_mode=True)
    assert root_logger.level == logging.DEBUG
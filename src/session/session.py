"""Session class for managing multi-turn conversations."""

import logging
from dataclasses import asdict
from typing import Optional

from ..config import load_config, AgentConfig
from ..llm import OpenAICompatibleProvider
from ..tool import create_tool_registry
from ..agent import AgentFactory

logger = logging.getLogger(__name__)


class Session:
    """
    Manages a conversation session with persistent resources and history.

    The session owns all resources (LLM provider, tool registry, agent)
    for its lifetime and maintains conversation history across turns.
    """

    def __init__(
        self,
        llm_provider: OpenAICompatibleProvider,
        tool_registry,
        agent,
        config: AgentConfig
    ):
        """
        Initialize a session with existing resources.

        Args:
            llm_provider: LLM provider instance
            tool_registry: Tool registry with all tools loaded
            agent: Initialized agent instance
            config: Agent configuration
        """
        self._llm_provider = llm_provider
        self._tool_registry = tool_registry
        self._agent = agent
        self._config = config
        self._closed = False

    @classmethod
    async def create(
        cls,
        config_path: str = "config.yaml",
        verbose: bool = False
    ) -> "Session":
        """
        Factory method to create and initialize a session.

        Args:
            config_path: Path to configuration file
            verbose: Enable verbose output

        Returns:
            Initialized Session instance

        Raises:
            Exception: If initialization fails
        """
        # Load configuration
        logger.info(f"Loading configuration from {config_path}")
        config: AgentConfig = load_config(config_path)

        # Initialize LLM provider
        logger.info(f"Initializing LLM provider: {config.llm.model}")
        llm_provider = OpenAICompatibleProvider(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            model=config.llm.model
        )

        # Load MCP servers
        mcp_server_dicts = [asdict(server) for server in config.mcp_servers]
        logger.info(f"Loading {len(mcp_server_dicts)} MCP servers")

        # Setup tool registry with all sources
        tool_registry = create_tool_registry(mcp_server_dicts)
        await tool_registry.load_all()

        # Create agent
        logger.info(f"Creating {config.agent_type} agent")
        agent = AgentFactory.create_agent(
            agent_type=config.agent_type,
            llm=llm_provider,
            tool_registry=tool_registry,
            max_iterations=config.max_iterations,
            verbose=verbose
        )

        # Initialize agent
        logger.info("Initializing agent")
        await agent.initialize()

        return cls(llm_provider, tool_registry, agent, config)

    async def ask(self, question: str) -> str:
        """
        Ask a question and get a response.

        Args:
            question: The question to ask

        Returns:
            The agent's response

        Raises:
            RuntimeError: If session is closed
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        logger.info(f"Processing question: {question[:50]}...")
        result = await self._agent.run(question)
        logger.info("Question processed successfully")
        return result

    async def close(self) -> None:
        """
        Close the session and release all resources.

        Safe to call multiple times.
        """
        if self._closed:
            return

        logger.info("Closing session")
        self._closed = True

        if self._tool_registry:
            try:
                await self._tool_registry.close_all()
            except Exception as e:
                logger.warning(f"Error during tool cleanup: {e}")

        logger.info("Session closed")

    def clear_history(self) -> None:
        """
        Clear conversation history while keeping resources alive.
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        logger.info("Clearing conversation history")
        self._agent.clear_history()

    @property
    def history_length(self) -> int:
        """
        Number of message exchanges in the conversation.

        Returns:
            Number of user-assistant exchanges
        """
        return self._agent.history_length

    async def __aenter__(self) -> "Session":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - closes session."""
        await self.close()
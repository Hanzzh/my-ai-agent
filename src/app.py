"""Application layer for orchestrating the agent execution."""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from .config import load_config, AgentConfig
from .llm import OpenAICompatibleProvider
from .mcp import MCPLoader
from .agent import AgentFactory


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_agent(question: str, config_path: str = "config.yaml") -> str:
    """
    Run the agent with a given question.

    This function orchestrates the entire agent execution flow:
    1. Load configuration from file
    2. Initialize LLM provider
    3. Load and initialize MCP servers
    4. Create agent via factory
    5. Run the agent
    6. Cleanup resources

    Args:
        question: The question or task for the agent to process
        config_path: Path to the configuration file (default: "config.yaml")

    Returns:
        The agent's response as a string

    Raises:
        Exception: If any step in the orchestration fails
    """
    llm_provider = None
    mcp_loader = None
    agent = None

    try:
        # Step 1: Load configuration
        logger.info(f"Loading configuration from {config_path}")
        config: AgentConfig = load_config(config_path)

        # Step 2: Initialize LLM provider
        logger.info(f"Initializing LLM provider: {config.llm.model}")
        llm_provider = OpenAICompatibleProvider(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            model=config.llm.model
        )

        # Step 3: Load MCP servers
        # Convert MCPServerConfig objects to dicts for MCPLoader
        mcp_server_dicts = [asdict(server) for server in config.mcp_servers]
        logger.info(f"Loading {len(mcp_server_dicts)} MCP servers")
        mcp_loader = MCPLoader(mcp_server_dicts)
        await mcp_loader.load_all()

        # Step 4: Create agent via factory
        logger.info(f"Creating {config.agent_type} agent")
        agent = AgentFactory.create_agent(
            agent_type=config.agent_type,
            llm=llm_provider,
            mcp_loader=mcp_loader,
            max_iterations=config.max_iterations
        )

        # Step 5: Initialize the agent
        logger.info("Initializing agent")
        await agent.initialize()

        # Step 6: Run the agent
        logger.info(f"Running agent with question: {question[:50]}...")
        result = await agent.run(question)

        logger.info("Agent execution completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        raise

    finally:
        # Step 7: Cleanup resources
        logger.info("Cleaning up resources")
        if mcp_loader:
            try:
                await mcp_loader.close_all()
            except Exception as e:
                logger.warning(f"Error during MCP cleanup: {e}")


async def run_agent_batch(
    questions: list[str],
    config_path: str = "config.yaml"
) -> list[str]:
    """
    Run the agent with multiple questions sequentially.

    Args:
        questions: List of questions to process
        config_path: Path to the configuration file

    Returns:
        List of responses corresponding to each question
    """
    results = []
    for i, question in enumerate(questions, 1):
        logger.info(f"Processing question {i}/{len(questions)}")
        result = await run_agent(question, config_path)
        results.append(result)
    return results


def main():
    """Entry point for synchronous contexts."""
    import sys

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Enter your question: ")

    result = asyncio.run(run_agent(question))
    print("\n=== Agent Response ===")
    print(result)
    print("======================\n")


if __name__ == "__main__":
    main()

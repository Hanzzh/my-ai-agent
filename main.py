#!/usr/bin/env python3
"""Main entry point for the AI Agent application."""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.app import run_agent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════╗
║           AI Agent - MCP-Powered Assistant           ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information."""
    help_text = """
Usage: python main.py [question]

Arguments:
  question    The question or task to process (optional)

Examples:
  python main.py "What is the weather today?"
  python main.py
  echo "Your question here" | python main.py

If no question is provided, you will be prompted to enter one.

Configuration:
  - Edit config.yaml to configure LLM and agent settings
  - Edit mcp_servers.yaml to configure MCP servers
  - Copy .env.example to .env and set your API keys

Environment Variables:
  - GLM_API_KEY: Your API key for the LLM provider
  - GLM_BASE_URL: Base URL for the LLM API

For more information, see README.md
"""
    print(help_text)


async def main_async():
    """Async main function."""
    try:
        # Get question from command line args or prompt
        if len(sys.argv) > 1:
            if sys.argv[1] in ['-h', '--help', 'help']:
                print_help()
                return

            question = " ".join(sys.argv[1:])
            logger.info(f"Question from command line: {question[:50]}...")
        else:
            print_banner()
            try:
                question = input("Enter your question (or 'quit' to exit): ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return

        if not question:
            logger.error("No question provided")
            print("Error: Please provide a question")
            return

        # Run the agent
        print(f"\nProcessing your question...\n")
        result = await run_agent(question)

        # Print result
        print("\n" + "="*60)
        print("RESULT")
        print("="*60)
        print(result)
        print("="*60 + "\n")

        logger.info("Question processed successfully")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        logger.info("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Check the logs for more details.")
        sys.exit(1)


def main():
    """Synchronous entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(130)


if __name__ == "__main__":
    main()

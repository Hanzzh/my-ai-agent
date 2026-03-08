#!/usr/bin/env python3
"""Main entry point for the AI Agent application."""

import asyncio
import sys
import logging
import argparse
from typing import Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.app import run_agent


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Agent - MCP-Powered Assistant"
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question or task to process"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    return parser.parse_args()


# Configure logging - will be reconfigured after args parsing
logging.basicConfig(
    level=logging.INFO,  # Temporary, will be updated
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_logging(debug_mode: bool):
    """Configure logging level based on debug mode."""
    log_level = logging.DEBUG if debug_mode else logging.WARNING
    logging.getLogger().setLevel(log_level)


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
  - OPENAI_API_KEY: Your API key for the LLM provider
  - OPENAI_BASE_URL: Base URL for the LLM API

For more information, see README.md
"""
    print(help_text)


async def main_async():
    """Async main function."""
    try:
        args = parse_args()
        configure_logging(args.debug)

        # Get question from command line args or prompt
        if args.question is None:
            # Interactive mode - show banner only in debug mode
            print_banner() if args.debug else None
            try:
                question = input("Enter your question (or 'quit' to exit): ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return
        else:
            question = args.question
            logger.info(f"Question from command line: {question[:50]}...")

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

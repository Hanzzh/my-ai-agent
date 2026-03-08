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
from src.session import Session


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


# Configure logging with initial level - will be adjusted after args parsing
logging.basicConfig(
    level=logging.INFO,  # Temporary, will be updated
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_logging(debug_mode: bool):
    """
    Configure logging level based on debug mode.

    In debug mode, sets logging level to DEBUG to show all logs.
    In normal mode, sets logging level to WARNING to suppress info/debug logs
    while still showing errors and warnings.

    Args:
        debug_mode: If True, enable verbose DEBUG logging.
                   If False, use WARNING level for silent operation.

    Note:
        This modifies the root logger level and affects all loggers
        throughout the application.
    """
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
Usage: python main.py [question] [options]

Arguments:
  question    The question or task to process (optional)

Options:
  --debug     Enable debug mode with verbose output (logs, iterations)
  -h, --help  Show this help message

Examples:
  python main.py "What is the weather today?"
  python main.py --debug "What is the weather today?"
  python main.py

Interactive Mode:
  When no question is provided, starts an interactive chat session.

  Commands:
    /quit    Exit the session
    /clear   Clear conversation history

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


async def interactive_session(debug: bool = False):
    """
    Run an interactive chat session.

    Args:
        debug: Enable debug mode with verbose output
    """
    print_banner()
    print("Chat started. Type /quit to exit, /clear to reset history.\n")

    session = None
    try:
        # Create session
        session = await Session.create(verbose=debug)

        while True:
            try:
                question = input("You: ").strip()

                # Handle slash commands
                if question.lower() == '/quit':
                    break
                elif question.lower() == '/clear':
                    session.clear_history()
                    print("History cleared.\n")
                    continue
                elif not question:
                    continue

                # Get answer from agent
                answer = await session.ask(question)
                print(f"\nAgent: {answer}\n")

            except (EOFError, KeyboardInterrupt):
                break

    except Exception as e:
        logger.error(f"Session error: {e}", exc_info=True)
        print(f"\nError: {e}")

    finally:
        if session:
            await session.close()
        print("Goodbye!")


async def main_async():
    """Async main function."""
    try:
        args = parse_args()
        configure_logging(args.debug)

        # Single-shot mode: question provided via command line
        if args.question:
            question = args.question
            logger.info(f"Question from command line: {question[:50]}...")

            if args.debug:
                print(f"\nProcessing your question...\n")

            result = await run_agent(question, verbose=args.debug)

            print("\n" + "="*60)
            print("RESULT")
            print("="*60)
            print(result)
            print("="*60 + "\n")

            logger.info("Question processed successfully")
        else:
            # Interactive mode: start chat session
            await interactive_session(debug=args.debug)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        logger.info("Operation cancelled by user")
        sys.exit(130)

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

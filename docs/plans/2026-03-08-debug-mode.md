# Debug Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `--debug` CLI flag to control output verbosity - silent mode by default (only final result), verbose mode with `--debug` flag (all logs and iterations).

**Architecture:** Use argparse for CLI parsing, control logging level (DEBUG vs WARNING), and pass a `verbose` flag through the call chain from main.py → app.py → agent factory → ReActAgent.

**Tech Stack:** Python argparse, logging module, existing async codebase

---

## Task 1: Add CLI Argument Parsing

**Files:**
- Modify: `main.py:1-20`

**Step 1: Add argparse import and function**

Add at top of file after existing imports:

```python
import argparse
from typing import Optional

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
```

**Step 2: Run to verify syntax**

Run: `python main.py --help`
Expected output: Shows help text with --debug option

**Step 3: Update main_async to use args**

Replace the argument parsing section (around line 66-72):

```python
async def main_async():
    """Async main function."""
    try:
        args = parse_args()

        if args.question is None:
            # Interactive mode
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

        if not question:
            print("Error: Please provide a question")
            return
```

**Step 4: Run to verify it works**

Run: `python main.py "test"`
Expected: Works as before

Run: `python main.py --debug "test"`
Expected: Works with banner and debug flag set

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: add argparse for CLI argument parsing

- Add parse_args() function with --debug flag
- Support both positional question and --debug option
- Interactive mode shows banner only in debug mode"
```

---

## Task 2: Configure Logging Based on Debug Flag

**Files:**
- Modify: `main.py:15-20`

**Step 1: Update logging configuration to use debug flag**

Replace the logging.basicConfig call (around line 16-19):

```python
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
```

**Step 2: Call configure_logging in main_async**

Add after `args = parse_args()` (around line 70):

```python
async def main_async():
    """Async main function."""
    try:
        args = parse_args()
        configure_logging(args.debug)
```

**Step 3: Run to verify silent mode**

Run: `python main.py "What's the capital of France?"`
Expected: NO log output (silent until result)

**Step 4: Run to verify debug mode**

Run: `python main.py --debug "What's the capital of France?"`
Expected: See INFO log messages

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: configure logging level based on debug flag

- Add configure_logging() function
- WARNING level by default (silent)
- DEBUG level with --debug flag (verbose)
- Errors always visible at WARNING level"
```

---

## Task 3: Update run_agent Signature

**Files:**
- Modify: `src/app.py:23`
- Modify: `src/app.py:103-122` (run_agent_batch)

**Step 1: Update run_agent function signature**

Replace line 23:

```python
async def run_agent(
    question: str,
    config_path: str = "config.yaml",
    verbose: bool = False
) -> str:
```

**Step 2: Pass verbose to AgentFactory**

Update the agent creation (around line 71-76):

```python
        # Step 4: Create agent via factory
        logger.info(f"Creating {config.agent_type} agent")
        agent = AgentFactory.create_agent(
            agent_type=config.agent_type,
            llm=llm_provider,
            mcp_loader=mcp_loader,
            max_iterations=config.max_iterations,
            verbose=verbose
        )
```

**Step 3: Update run_agent_batch to support verbose**

Update run_agent_batch signature (around line 103):

```python
async def run_agent_batch(
    questions: list[str],
    config_path: str = "config.yaml",
    verbose: bool = False
) -> list[str]:
```

And the call to run_agent within it (around line 120):

```python
        result = await run_agent(question, config_path, verbose)
```

**Step 4: Run tests to verify no breakage**

Run: `pytest tests/ -v -m "not integration"`
Expected: All tests pass

**Step 5: Commit**

```bash
git add src/app.py
git commit -m "feat: add verbose parameter to run_agent

- Update run_agent() signature with verbose parameter
- Update run_agent_batch() to pass verbose through
- Pass verbose to AgentFactory.create_agent()"
```

---

## Task 4: Update AgentFactory to Pass Verbose

**Files:**
- Modify: `src/agent/factory.py:23-38`

**Step 1: Update create_agent signature and pass verbose**

Replace the create_agent method (around line 23-38):

```python
    @staticmethod
    def create_agent(
        agent_type: str,
        llm: LLMProvider,
        mcp_loader: MCPLoader,
        verbose: bool = False,
        **kwargs
    ) -> Agent:
        """Create an agent instance based on type."""
        if agent_type == "react":
            from .react import ReActAgent
            # Combine verbose with any other kwargs
            return ReActAgent(
                llm=llm,
                mcp_loader=mcp_loader,
                verbose=verbose,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

**Step 2: Run tests**

Run: `pytest tests/agent/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add src/agent/factory.py
git commit -m "feat: pass verbose through AgentFactory

- Add verbose parameter to create_agent()
- Pass verbose to ReActAgent constructor
- Combine with existing kwargs pattern"
```

---

## Task 5: Update ReActAgent to Accept Verbose

**Files:**
- Modify: `src/agent/react.py:19-36`
- Modify: `src/agent/react.py:162`

**Step 1: Add verbose to __init__**

Update the __init__ method (around line 19-36):

```python
    def __init__(
        self,
        llm: LLMProvider,
        mcp_loader: MCPLoader,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize ReAct Agent.

        Args:
            llm: LLM provider for generating responses
            mcp_loader: MCP loader for accessing tools
            max_iterations: Maximum number of Thought-Action-Observation cycles
            verbose: Whether to print intermediate steps
        """
        self.llm = llm
        self.mcp_loader = mcp_loader
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools: Dict[str, Tuple] = {}  # tool_name -> (client, tool)
```

**Step 2: Update run() to use self.verbose**

Update the run method signature (around line 162):

```python
    async def run(self, question: str, verbose: Optional[bool] = None) -> str:
        """
        Run the ReAct loop to answer the question.

        Args:
            question: The user's question
            verbose: Whether to print intermediate steps (overrides instance default)

        Returns:
            The final answer
        """
        # Use parameter if provided, otherwise use instance default
        should_verbose = verbose if verbose is not None else self.verbose
```

Then replace all `if verbose:` with `if should_verbose:` throughout the run method.

**Step 3: Run tests**

Run: `pytest tests/agent/test_react.py -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add src/agent/react.py
git add tests/agent/test_react.py
git commit -m "feat: add verbose parameter to ReActAgent

- Add verbose to __init__ with default True (backward compatible)
- Allow run() to override instance verbose
- Replace hardcoded verbose with self.verbose"
```

---

## Task 6: Wire verbose from main.py to run_agent

**Files:**
- Modify: `main.py:89-98`

**Step 1: Pass debug_mode as verbose to run_agent**

Update the run_agent call (around line 91):

```python
        # Run the agent
        if args.debug:
            print(f"\nProcessing your question...\n")

        result = await run_agent(question, verbose=args.debug)
```

**Step 2: Update interactive mode prompt**

Update the interactive section (around line 74-76):

```python
        if args.question is None:
            # Interactive mode
            if args.debug:
                print_banner()
            try:
```

**Step 3: Test silent mode**

Run: `python main.py "What's 2+2?"`
Expected: Only final result box, NO "Processing..." message, NO logs

**Step 4: Test debug mode**

Run: `python main.py --debug "What's 2+2?"`
Expected: Logs, "Processing..." message, iterations, final result

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: wire verbose flag through main.py

- Pass args.debug as verbose to run_agent()
- Show 'Processing...' only in debug mode
- Banner only shows in debug mode"
```

---

## Task 7: Add Tests for Debug Mode

**Files:**
- Create: `tests/test_debug_mode.py`

**Step 1: Create test file**

Create new test file:

```python
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
         patch('src.app.MCPLoader') as mock_mcp:

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
        mock_llm_instance.chat = AsyncMock(return_value="Action: Final Answer\nAction Input: Test answer")
        mock_llm.return_value = mock_llm_instance

        mock_mcp_instance = MagicMock()
        mock_mcp_instance.load_all = AsyncMock()
        mock_mcp_instance.get_all_tools.return_value = {}
        mock_mcp.return_value = mock_mcp_instance

        # Run with verbose=False
        result = await run_agent("test", verbose=False)

        # Verify result
        assert result == "Test answer"


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
```

**Step 2: Run tests**

Run: `pytest tests/test_debug_mode.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_debug_mode.py
git commit -m "test: add debug mode tests

- Test parse_args with various combinations
- Test configure_logging sets correct levels
- Test run_agent with verbose=False
- Test AgentFactory passes verbose through"
```

---

## Task 8: Manual Testing & Verification

**Files:**
- Manual verification only

**Step 1: Test silent mode (no flag)**

Run: `python main.py "What is the capital of France?"`

Expected output:
```
============================================================
RESULT
============================================================
Paris is the capital of France.
============================================================
```

NO logs, NO "Processing..." message, NO iteration details.

**Step 2: Test debug mode (with flag)**

Run: `python main.py --debug "What is the capital of France?"`

Expected output:
- Timestamp logs (INFO level)
- "Processing your question..." message
- Banner (if interactive)
- Iteration details
- Final result box

**Step 3: Test error always shows**

Run: `python main.py ""`

Expected output:
```
Error: Please provide a question
```

(No --debug flag, but error still shows)

**Step 4: Test Ctrl+C message shows**

Run: `python main.py` then press Ctrl+C

Expected output:
```
Operation cancelled by user.
```

**Step 5: Run full test suite**

Run: `pytest tests/ -v`

Expected: All tests pass

**Step 6: Commit if any adjustments needed**

If any small adjustments were made:

```bash
git add -A
git commit -m "fix: minor adjustments from manual testing"
```

---

## Task 9: Update Help Documentation

**Files:**
- Modify: `main.py:33-59`
- Modify: `README.md` (if needed)

**Step 1: Update print_help() function**

Replace the help text (around line 35-58):

```python
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
```

**Step 2: Verify help displays correctly**

Run: `python main.py --help`

Expected output: Shows updated help with --debug option

**Step 3: Commit**

```bash
git add main.py
git commit -m "docs: update help text with --debug option

- Add --debug to usage examples
- Document verbose vs silent mode behavior"
```

---

## Success Criteria Verification

After completing all tasks, verify:

- [ ] `python main.py "question"` shows only final result (silent)
- [ ] `python main.py --debug "question"` shows all output (verbose)
- [ ] Errors always visible (without --debug flag)
- [ ] All existing tests pass
- [ ] New tests pass
- [ ] Help text shows --debug option

---

## Final Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Manual testing completed
- [ ] Code committed with descriptive messages
- [ ] No regressions in existing functionality
- [ ] Documentation updated

**Estimated total time:** 45-60 minutes

**Files modified:**
- `main.py` (argparse, logging, verbose wiring)
- `src/app.py` (run_agent signature)
- `src/agent/factory.py` (create_agent verbose parameter)
- `src/agent/react.py` (verbose in __init__ and run)

**Files created:**
- `tests/test_debug_mode.py` (new tests)

# Tool Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create `src/tool/` module with unified Tool interface that hides MCP implementation from agents. Agents see only tools, not their source.

**Architecture:** Create `src/tool/` module with `base.py` (Tool protocol), `registry.py` (ToolAggregator), and move `src/mcp/` to `src/tool/mcp/`. Agent uses `ToolRegistry` instead of `MCPLoader` directly.

**Tech Stack:** Python 3.8+, async/await, Protocol from typing

---

### Task 1: Create tool module directory structure

**Files:**
- Create: `src/tool/__init__.py`
- Create: `src/tool/base.py`
- Create: `src/tool/registry.py`
- Create: `src/tool/mcp/__init__.py`

**Step 1: Create `src/tool/base.py`**

```python
"""Tool interface definitions."""

from typing import Protocol, Any, Dict
from typing_extensions import TypedDict


class ToolDescription(TypedDict):
    """Description of a tool for LLM consumption."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Tool(Protocol):
    """Protocol for all tools (MCP, embedded, etc.)."""

    name: str
    description: str
    inputSchema: Dict[str, Any]

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given arguments."""
        ...


class ToolResult:
    """Result from tool execution."""

    def __init__(self, name: str, result: str, error: str = None):
        self.name = name
        self.result = result
        self.error = error

    @property
    def is_error(self) -> bool:
        return self.error is not None
```

**Step 2: Create `src/tool/registry.py`**

```python
"""Tool registry for aggregating tools from multiple sources."""

import logging
from typing import List, Dict, Any, Tuple
from .base import Tool, ToolDescription

logger = logging.getLogger(__name__)


class ToolSource(Protocol):
    """Protocol for things that provide tools."""

    async def load(self) -> None:
        """Initialize/load tools from this source."""
        ...

    def get_tools(self) -> List[ToolDescription]:
        """Return list of tools from this source."""
        ...

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name."""
        ...

    async def close(self) -> None:
        """Cleanup resources."""
        ...


class ToolRegistry:
    """
    Registry that aggregates tools from multiple sources (MCP, embedded, etc.).

    Agents use this to get tools without knowing where they come from.
    """

    def __init__(self):
        self._sources: List[ToolSource] = []
        self._tools_cache: List[ToolDescription] = []

    def add_source(self, source: ToolSource) -> None:
        """Add a tool source (MCP server, embedded tool, etc.)"""
        self._sources.append(source)
        logger.info(f"Added tool source: {source.__class__.__name__}")

    async def load_all(self) -> None:
        """Load tools from all sources."""
        for source in self._sources:
            await source.load()
        self._refresh_cache()
        logger.info(f"Loaded {len(self._tools_cache)} tools from {len(self._sources)} sources")

    def get_tools(self) -> List[ToolDescription]:
        """Return all available tools (for LLM consumption)."""
        return self._tools_cache

    def get_tool_names(self) -> List[str]:
        """Return list of all tool names."""
        return [t["name"] for t in self._tools_cache]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name across all sources."""
        for source in self._sources:
            tool_names = [t["name"] for t in source.get_tools()]
            if name in tool_names:
                return await source.execute(name, arguments)

        raise ValueError(f"Tool '{name}' not found. Available: {self.get_tool_names()}")

    async def close_all(self) -> None:
        """Close all sources."""
        for source in self._sources:
            await source.close()
        self._tools_cache = []

    def _refresh_cache(self) -> None:
        """Refresh the cached tool list from all sources."""
        self._tools_cache = []
        for source in self._sources:
            self._tools_cache.extend(source.get_tools())
```

**Step 3: Create `src/tool/__init__.py`**

```python
"""Unified tool module - aggregates tools from MCP and embedded sources."""

from .base import Tool, ToolDescription, ToolResult
from .registry import ToolRegistry, ToolSource

__all__ = ['Tool', 'ToolDescription', 'ToolResult', 'ToolRegistry', 'ToolSource']
```

**Step 4: Commit**

Run:
```bash
git add src/tool/
git commit -m "feat: add tool module with Tool protocol and registry"
```

Expected: Commit created

---

### Task 2: Move MCP files to tool/mcp/

**Files:**
- Move: `src/mcp/client.py` → `src/tool/mcp/client.py`
- Move: `src/mcp/loader.py` → `src/tool/mcp/loader.py`
- Create: `src/tool/mcp/__init__.py`

**Step 1: Move files**

```bash
mkdir -p src/tool/mcp
mv src/mcp/client.py src/tool/mcp/
mv src/mcp/loader.py src/tool/mcp/
```

**Step 2: Update `src/tool/mcp/__init__.py`**

```python
"""MCP client and server integration (internal)."""

from .client import MCPClient
from .loader import MCPLoader

__all__ = ['MCPClient', 'MCPLoader']
```

**Step 3: Commit**

Run:
```bash
git add src/tool/mcp/ src/mcp/
git commit -m "refactor: move mcp to tool/mcp"
```

Expected: Commit created

---

### Task 3: Update MCPLoader to implement ToolSource protocol

**Files:**
- Modify: `src/tool/mcp/loader.py`

**Step 1: Write failing test**

Create `tests/tool/test_mcp_loader.py`:

```python
"""Tests for tool/mcp/loader.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_mcp_client():
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.inputSchema = {"type": "object", "properties": {}}
    client.tools = [tool]
    client.call_tool = AsyncMock(return_value="tool result")
    return client


@pytest.fixture
def mcp_loader(mock_mcp_client):
    with patch('src.tool.mcp.loader.MCPClient', return_value=mock_mcp_client):
        from src.tool.mcp import MCPLoader
        loader = MCPLoader([{"command": "test"}])
        return loader


@pytest.mark.asyncio
async def test_mcp_loader_get_tools(mcp_loader, mock_mcp_client):
    """Test that MCPLoader returns tools in ToolDescription format."""
    await mcp_loader.load_all()
    tools = mcp_loader.get_tools()

    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["description"] == "A test tool"
    assert "inputSchema" in tools[0]
```

**Step 2: Run test**

Run:
```bash
pytest tests/tool/test_mcp_loader.py -v
```

Expected: FAIL - get_tools doesn't return ToolDescription format yet

**Step 3: Implement changes in `src/tool/mcp/loader.py`**

Modify the `get_all_tools` method to return `List[ToolDescription]`:

```python
"""MCP server loader for managing multiple servers."""

from .client import MCPClient
from typing import List, Dict, Tuple
from ...base import ToolDescription


class MCPLoader:
    """Manages multiple MCP server connections and implements ToolSource."""

    def __init__(self, server_configs: List[Dict]):
        """Initialize MCP loader with list of server parameter dicts."""
        self.clients: List[MCPClient] = []
        for config in server_configs:
            self.clients.append(MCPClient(config))

    async def load(self) -> None:
        """Implement ToolSource protocol - connect to all MCP servers."""
        for client in self.clients:
            await client.connect()

    def get_tools(self) -> List[ToolDescription]:
        """Return tools in ToolDescription format."""
        tools = []
        for client in self.clients:
            for tool in client.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
        return tools

    async def execute(self, name: str, arguments: Dict) -> str:
        """Execute a tool by name."""
        for client in self.clients:
            for tool in client.tools:
                if tool.name == name:
                    return await client.call_tool(name, arguments)
        raise ValueError(f"Tool {name} not found")

    async def close(self) -> None:
        """Close all connections."""
        for client in self.clients:
            await client.close()

    # Keep old methods for backward compatibility during transition
    async def load_all(self):
        """Backward compat: use load() instead."""
        await self.load()

    def get_all_tools(self) -> Dict[str, Tuple[MCPClient, object]]:
        """Backward compat: use get_tools() instead."""
        tools = {}
        for client in self.clients:
            for tool in client.tools:
                tools[tool.name] = (client, tool)
        return tools

    async def close_all(self):
        """Backward compat: use close() instead."""
        await self.close()
```

**Step 4: Run test**

Run:
```bash
pytest tests/tool/test_mcp_loader.py -v
```

Expected: PASS

**Step 5: Commit**

Run:
```bash
git add src/tool/mcp/loader.py tests/tool/
git commit -m "refactor: MCPLoader implements ToolSource protocol"
```

Expected: Commit created

---

### Task 4: Update app.py to use ToolRegistry

**Files:**
- Modify: `src/app.py:1-144`

**Step 1: Write failing test**

Create `tests/tool/test_registry.py`:

```python
"""Tests for tool registry."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.tool.registry import ToolRegistry
from src.tool.base import ToolDescription


@pytest.fixture
def mock_source():
    source = MagicMock()
    source.load = AsyncMock()
    source.close = AsyncMock()
    source.get_tools = MagicMock(return_value=[
        {"name": "tool1", "description": "First tool", "inputSchema": {}},
        {"name": "tool2", "description": "Second tool", "inputSchema": {}}
    ])
    source.execute = AsyncMock(return_value="result")
    return source


@pytest.mark.asyncio
async def test_registry_add_source(mock_source):
    """Test adding a source to registry."""
    registry = ToolRegistry()
    registry.add_source(mock_source)

    await registry.load_all()
    tools = registry.get_tools()

    assert len(tools) == 2
    assert "tool1" in [t["name"] for t in tools]


@pytest.mark.asyncio
async def test_registry_execute_tool(mock_source):
    """Test executing a tool through registry."""
    registry = ToolRegistry()
    registry.add_source(mock_source)

    await registry.load_all()
    result = await registry.execute_tool("tool1", {"arg": "value"})

    mock_source.execute.assert_called_once_with("tool1", {"arg": "value"})
    assert result == "result"
```

**Step 2: Run test**

Run:
```bash
pytest tests/tool/test_registry.py -v
```

Expected: PASS (registry already implemented in Task 1)

**Step 3: Update `src/app.py`**

Change imports and usage:

```python
"""Application layer for orchestrating the agent execution."""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from .config import load_config, AgentConfig
from .llm import OpenAICompatibleProvider
from .tool import ToolRegistry
from .tool.mcp import MCPLoader
from .agent import AgentFactory

logger = logging.getLogger(__name__)


async def run_agent(
    question: str,
    config_path: str = "config.yaml",
    verbose: bool = False
) -> str:
    """
    Run the agent with a given question.
    ...
    """
    llm_provider = None
    tool_registry = None

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

        # Step 3: Setup tool registry with MCP
        mcp_server_dicts = [asdict(server) for server in config.mcp_servers]
        logger.info(f"Loading {len(mcp_server_dicts)} MCP servers")

        tool_registry = ToolRegistry()
        mcp_loader = MCPLoader(mcp_server_dicts)
        tool_registry.add_source(mcp_loader)

        await tool_registry.load_all()

        # Step 4: Create agent via factory
        logger.info(f"Creating {config.agent_type} agent")
        agent = AgentFactory.create_agent(
            agent_type=config.agent_type,
            llm=llm_provider,
            tool_registry=tool_registry,
            max_iterations=config.max_iterations,
            verbose=verbose
        )
        # ... rest unchanged
```

**Step 4: Run tests**

Run:
```bash
pytest tests/ -v -m "not integration" --tb=short
```

Expected: FAIL - agent still expects mcp_loader, need to update factory

**Step 5: Commit**

Run:
```bash
git add src/app.py
git commit -m "refactor: app.py uses ToolRegistry instead of MCPLoader"
```

Expected: Commit created

---

### Task 5: Update AgentFactory to use ToolRegistry

**Files:**
- Modify: `src/agent/factory.py`

**Step 1: Read current factory**

```bash
cat src/agent/factory.py
```

**Step 2: Update factory**

```python
"""Agent factory for creating agent instances."""

from .base import Agent
from .react import ReActAgent
from ..llm.base import LLMProvider
from ..tool.registry import ToolRegistry


class AgentFactory:
    """Factory for creating agent instances."""

    @staticmethod
    def create_agent(
        agent_type: str,
        llm: LLMProvider,
        tool_registry: ToolRegistry = None,
        mcp_loader: None = None,  # Deprecated, kept for compatibility
        max_iterations: int = 10,
        verbose: bool = False
    ) -> Agent:
        """
        Create an agent instance based on type.

        Args:
            agent_type: Type of agent to create
            llm: LLM provider
            tool_registry: Tool registry (preferred)
            mcp_loader: Deprecated, use tool_registry
            max_iterations: Max iterations
            verbose: Verbose mode
        """
        # Handle deprecated mcp_loader parameter
        if mcp_loader is not None:
            from ..tool import ToolRegistry
            tool_registry = ToolRegistry()
            tool_registry.add_source(mcp_loader)

        if agent_type == "react":
            return ReActAgent(
                llm=llm,
                tool_registry=tool_registry,
                max_iterations=max_iterations,
                verbose=verbose
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

**Step 3: Commit**

Run:
```bash
git add src/agent/factory.py
git commit -m "refactor: AgentFactory accepts ToolRegistry"
```

Expected: Commit created

---

### Task 6: Update ReActAgent to use ToolRegistry

**Files:**
- Modify: `src/agent/react.py`

**Step 1: Write failing test**

```python
# In tests/agent/test_react.py, add test

@pytest.mark.asyncio
async def test_react_agent_with_tool_registry(mock_llm, mock_tool_registry):
    """Test ReActAgent works with ToolRegistry."""
    from src.agent.react import ReActAgent

    mock_tool_registry.load_all = AsyncMock()
    mock_tool_registry.get_tools = MagicMock(return_value=[
        {"name": "test_tool", "description": "A test tool", "inputSchema": {}}
    ])
    mock_tool_registry.execute_tool = AsyncMock(return_value="result")

    agent = ReActAgent(
        llm=mock_llm,
        tool_registry=mock_tool_registry,
        max_iterations=5
    )

    await agent.initialize()
    tools = agent.tools

    assert "test_tool" in tools
```

**Step 2: Run test**

Run:
```bash
pytest tests/agent/test_react.py::test_react_agent_with_tool_registry -v
```

Expected: FAIL - ReActAgent doesn't accept tool_registry yet

**Step 3: Update ReActAgent**

```python
"""ReAct (Reasoning + Acting) Agent implementation."""

import re
import json
from typing import Dict, Tuple, Optional, Any
from .factory import Agent
from ..llm.base import LLMProvider
from ..tool.registry import ToolRegistry
from ..tool.base import ToolDescription


class ReActAgent(Agent):
    """
    ReAct Agent that implements the Thought-Action-Observation loop.

    The agent reasons about what to do (Thought), takes action (Action),
    and observes the result (Observation) in an iterative loop.
    """

    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry = None,
        mcp_loader: Any = None,  # Deprecated
        max_iterations: int = 10,
        verbose: bool = False
    ):
        """
        Initialize ReAct Agent.

        Args:
            llm: LLM provider for generating responses
            tool_registry: Registry for accessing tools
            mcp_loader: Deprecated, use tool_registry
            max_iterations: Maximum number of Thought-Action-Observation cycles
            verbose: Whether to print intermediate steps during execution
        """
        # Handle deprecated mcp_loader
        if mcp_loader is not None:
            from ..tool import ToolRegistry
            tool_registry = ToolRegistry()
            tool_registry.add_source(mcp_loader)

        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools: Dict[str, ToolDescription] = {}  # tool_name -> tool description

    async def initialize(self):
        """Load tools from registry."""
        await self.tool_registry.load_all()
        tool_list = self.tool_registry.get_tools()
        self.tools = {t["name"]: t for t in tool_list}

    def _format_tools_description(self) -> str:
        """Format available tools as a string."""
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool_name, tool in self.tools.items():
            desc = f"- {tool_name}: {tool['description']}"
            if tool.get("inputSchema"):
                desc += f" (input schema: {json.dumps(tool['inputSchema'])})"
            descriptions.append(desc)

        return "\n".join(descriptions)

    # ... keep other methods, but update tool execution:

    async def run(self, question: str, verbose: Optional[bool] = None) -> str:
        # ... existing code until tool execution ...

        # Execute tool action
        if action in self.tools:
            try:
                result = await self.tool_registry.execute_tool(action, action_input or {})
                # ... rest of execution logic
```

**Step 4: Run tests**

Run:
```bash
pytest tests/agent/test_react.py -v --tb=short
```

Expected: PASS

**Step 5: Commit**

Run:
```bash
git add src/agent/react.py
git commit -m "refactor: ReActAgent uses ToolRegistry"
```

Expected: Commit created

---

### Task 7: Clean up old mcp module

**Files:**
- Delete: `src/mcp/__init__.py`

**Step 1: Remove old mcp init**

```bash
rm src/mcp/__init__.py
```

**Step 2: Run full test suite**

Run:
```bash
pytest tests/ -v -m "not integration" --tb=short
```

Expected: All pass

**Step 3: Commit**

Run:
```bash
git add src/mcp/ src/tool/
git commit -m "refactor: remove old mcp module, complete tool abstraction"
```

Expected: Commit created

---

## Summary

| Task | Files | Key Changes |
|------|-------|-------------|
| 1 | Create tool/ | Tool protocol, ToolRegistry |
| 2 | Move mcp/ | Move to tool/mcp/ |
| 3 | tool/mcp/loader.py | Implements ToolSource |
| 4 | app.py | Uses ToolRegistry |
| 5 | agent/factory.py | Accepts ToolRegistry |
| 6 | agent/react.py | Uses ToolRegistry |
| 7 | Cleanup | Remove old mcp/ |

**Total: 7 commits**
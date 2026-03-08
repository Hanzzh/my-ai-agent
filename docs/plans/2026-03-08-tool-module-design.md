# Tool Module Design

**Date**: 2026-03-08
**Status**: Approved

## Goal

Create a `src/tool/` module that provides a unified tool abstraction, hiding implementation details (MCP, filesystem, command execution) from agents. Agents only see a list of `Tool` objects regardless of source.

## New Structure

```
src/tool/
├── __init__.py           # Exports: ToolRegistry, Tool (protocol)
├── mcp/
│   ├── __init__.py       # Internal exports
│   ├── client.py         # MCPClient (unchanged)
│   └── loader.py         # MCPLoader (returns normalized Tools)
├── base.py               # Tool protocol/interface definition
└── registry.py           # ToolRegistry to aggregate tools from all sources
```

## Components

### 1. `src/tool/base.py` - Tool Protocol

Defines the interface all tools must implement:

```python
class Tool(Protocol):
    name: str
    description: str

    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        ...
```

### 2. `src/tool/registry.py` - ToolRegistry

Central registry that aggregates tools from all sources:

```python
class ToolRegistry:
    def __init__(self):
        self._sources: list[ToolSource] = []

    def add_source(self, source: ToolSource):
        """Add a tool source (MCP, filesystem, etc.)"""
        ...

    async def load_all(self):
        """Load tools from all sources"""
        ...

    def get_tools(self) -> list[Tool]:
        """Return all available tools to agents"""
        ...

    async def close_all(self):
        """Cleanup all sources"""
        ...
```

Where `ToolSource` is an interface for things that provide tools.

### 3. `src/tool/mcp/loader.py` - Modified MCPLoader

- Wraps MCP tools in normalized Tool interface
- Implements `ToolSource` protocol
- Returns `list[Tool]` instead of raw MCP tool objects

### 4. `src/tool/mcp/client.py`

- Move to `src/tool/mcp/client.py`
- No interface changes

## Import Paths

| Usage | Import |
|-------|--------|
| Agent gets tools | `from src.tool.registry import ToolRegistry` |
| MCP Client (internal) | `from src.tool.mcp import MCPClient` |
| MCPLoader (internal) | `from src.tool.mcp import MCPLoader` |
| Tool interface | `from src.tool.base import Tool` |

## Data Flow

```
Agent requests tools
        ↓
ToolRegistry.get_tools()
        ↓
    ┌───┴───┐
    ↓       ↓
MCPLoader  (future: EmbeddedToolSource)
    ↓
List[Tool] → Agent
```

Agent has no knowledge of MCP or other sources.

## Future Embedded Tools

When adding filesystem and command execution tools:

```
src/tool/
├── mcp/                  (existing)
├── filesystem.py         (new)
├── command.py            (new)
└── registry.py           (updated to load these)
```

Each will implement the `Tool` protocol and be added to `ToolRegistry`.

## Files to Update

- `src/app.py` - Use `ToolRegistry` instead of `MCPLoader`
- `src/agent/react.py` - Update tool import
- `src/config/settings.py` - Update MCP import path
- Tests - Update import paths

## Files to Create

- `src/tool/__init__.py`
- `src/tool/base.py`
- `src/tool/registry.py`
- `src/tool/mcp/__init__.py`

## Files to Move

- `src/mcp/client.py` → `src/tool/mcp/client.py`
- `src/mcp/loader.py` → `src/tool/mcp/loader.py`

## Files to Delete

- `src/mcp/__init__.py` (after moving contents)
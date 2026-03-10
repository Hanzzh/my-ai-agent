# Embedded Bash Tool Design

**Date**: 2026-03-10
**Status**: Approved

## Goal

Add an embedded bash tool that allows the agent to execute shell commands with configurable permissions. The tool follows the existing `ToolSource` protocol and integrates seamlessly with `ToolRegistry`.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Permission model | Allowlist + forbidlist | Configurable, explicit control |
| Configuration file | `permissions.yaml` | Separate from main config, like `mcp_servers.yaml` |
| Output format | Raw stdout/stderr combined | Simple, agent sees everything |
| Error handling | Always succeed | Returns error messages, never raises exceptions |
| Default state | Enabled with empty allowlist | Tool exists, no commands allowed until configured |
| Integration pattern | Factory function | `app.py` doesn't know about specific sources |

## Architecture

### Directory Structure

```
src/tool/
├── __init__.py           # Exports create_tool_registry
├── factory.py            # create_tool_registry() function
├── registry.py           # (existing)
├── base.py               # (existing)
├── embedded/
│   ├── __init__.py       # Exports EmbeddedToolSource
│   ├── source.py         # EmbeddedToolSource class
│   └── bash.py           # BashTool class
└── mcp/                  # (existing)
```

### Configuration Format

**permissions.yaml**:
```yaml
allow:
  - Bash(git)
  - Bash(chmod)
  - Bash(ls)
  - Bash(cat)

forbid:
  - Bash(passwd)
  - Bash(rm)
```

**Permission logic:**
1. If command matches `forbid` → denied (takes precedence)
2. If `allow` is empty → no commands allowed
3. If command matches `allow` → allowed
4. Otherwise → denied

**Format rationale:**
- `Bash(command)` format is tool-agnostic
- Supports future embedded tools (e.g., `Filesystem(read)`, `HTTP(get)`)

## Components

### 1. BashTool (`src/tool/embedded/bash.py`)

```python
class BashTool:
    """Embedded tool for executing bash commands."""

    name: str = "bash"
    description: str = "Execute bash commands. Allowed commands are restricted by configuration."
    inputSchema: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            }
        },
        "required": ["command"]
    }

    def __init__(self, allowed_commands: list[str], forbidden_commands: list[str]):
        self.allowed_commands = allowed_commands
        self.forbidden_commands = forbidden_commands

    async def execute(self, command: str) -> str:
        """Execute a bash command if allowed."""
        # Parse command name (first word)
        # Check: forbid takes precedence over allow
        # If not in allow list → denied
        # Execute via asyncio subprocess
        # Return stdout + stderr combined (always succeeds)
```

**Key behaviors:**
- Parses command name from input (first word before space)
- `forbid` list takes precedence over `allow`
- Returns error message if command denied
- Always returns output (never raises exceptions)
- Combines stdout and stderr into single output

### 2. EmbeddedToolSource (`src/tool/embedded/source.py`)

```python
class EmbeddedToolSource:
    """ToolSource implementation for embedded tools."""

    def __init__(self, permissions_path: str = "permissions.yaml"):
        self.permissions_path = permissions_path
        self._tools: list[Tool] = []

    async def load(self) -> None:
        """Load permissions and initialize tools."""
        # Load permissions.yaml (create empty if not exists)
        # Parse allow/forbid lists for Bash commands
        # Create BashTool instance with parsed permissions
        # Store in self._tools

    def get_tools(self) -> list[ToolDescription]:
        """Return list of embedded tools."""
        return self._tools

    async def execute(self, name: str, arguments: dict) -> str:
        """Execute an embedded tool by name."""
        # Find tool by name
        # Call tool.execute(**arguments)

    async def close(self) -> None:
        """No cleanup needed for embedded tools."""
        pass
```

**Key behaviors:**
- Loads `permissions.yaml` on startup
- Creates `BashTool` with parsed allow/forbid lists
- If `permissions.yaml` doesn't exist → creates empty config (empty allowlist)
- Only exposes `bash` tool (future tools added here)

### 3. Factory Function (`src/tool/factory.py`)

```python
def create_tool_registry(mcp_servers: list[dict], permissions_path: str = "permissions.yaml") -> ToolRegistry:
    """Create a ToolRegistry with all sources configured."""
    registry = ToolRegistry()

    # Add MCP source
    mcp_loader = MCPLoader(mcp_servers)
    registry.add_source(mcp_loader)

    # Add embedded tools source
    embedded_source = EmbeddedToolSource(permissions_path)
    registry.add_source(embedded_source)

    return registry
```

### 4. App Integration (`src/app.py`)

```python
from .tool import create_tool_registry

# Step 3: Setup tool registry with all sources
tool_registry = create_tool_registry(mcp_server_dicts)
await tool_registry.load_all()
```

## Files to Create

| File | Description |
|------|-------------|
| `src/tool/embedded/__init__.py` | Exports `EmbeddedToolSource` |
| `src/tool/embedded/source.py` | `EmbeddedToolSource` class |
| `src/tool/embedded/bash.py` | `BashTool` class |
| `src/tool/factory.py` | `create_tool_registry()` factory function |
| `permissions.yaml` | Default empty permissions config |
| `tests/tool/embedded/__init__.py` | Test package |
| `tests/tool/embedded/test_bash.py` | BashTool tests |
| `tests/tool/embedded/test_source.py` | EmbeddedToolSource tests |

## Files to Modify

| File | Change |
|------|--------|
| `src/tool/__init__.py` | Export `create_tool_registry` |
| `src/app.py` | Use `create_tool_registry()` instead of manual setup |

## Testing

```
tests/tool/embedded/
├── __init__.py
├── test_bash.py           # BashTool unit tests
└── test_source.py         # EmbeddedToolSource tests
```

**Test cases:**
1. `BashTool` with empty allowlist → all commands denied
2. `BashTool` with allowlist → allowed commands execute
3. `BashTool` with forbid → forbidden commands denied even if in allowlist
4. `BashTool` execution → returns stdout + stderr combined
5. `EmbeddedToolSource` → loads permissions.yaml correctly
6. `EmbeddedToolSource` → creates empty config if file missing
7. `create_tool_registry()` → returns registry with both MCP and embedded sources

## Future Extensibility

The `Bash(tool)` format supports future embedded tools:

```yaml
allow:
  - Bash(git)
  - Filesystem(read)
  - HTTP(get)

forbid:
  - Bash(rm)
  - Filesystem(write)
```

Adding new tools requires:
1. Create new tool class in `src/tool/embedded/`
2. Update `EmbeddedToolSource.load()` to instantiate it
3. Update permission parsing for the new tool
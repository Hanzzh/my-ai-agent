# Embedded Bash Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an embedded bash tool with configurable allow/forbid permissions that integrates with ToolRegistry via a factory function.

**Architecture:** BashTool class handles command execution with permission checking. EmbeddedToolSource implements ToolSource protocol. Factory function creates configured ToolRegistry, hiding source details from app.py.

**Tech Stack:** Python 3.8+, asyncio subprocess, Pydantic for config validation

---

### Task 1: BashTool Class - Core Structure

**Files:**
- Create: `src/tool/embedded/bash.py`
- Create: `tests/tool/embedded/__init__.py`
- Create: `tests/tool/embedded/test_bash.py`

**Step 1: Create test file with failing test for BashTool structure**

```python
# tests/tool/embedded/test_bash.py
"""Tests for BashTool."""

import pytest
from src.tool.embedded.bash import BashTool


def test_bash_tool_has_required_attributes():
    """BashTool should have name, description, and inputSchema."""
    tool = BashTool(allowed_commands=[], forbidden_commands=[])

    assert tool.name == "bash"
    assert "bash commands" in tool.description.lower()
    assert "command" in tool.inputSchema["properties"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tool/embedded/test_bash.py::test_bash_tool_has_required_attributes -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.tool.embedded.bash'"

**Step 3: Create BashTool class with minimal structure**

```python
# src/tool/embedded/bash.py
"""Embedded bash tool for command execution."""

from typing import List


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

    def __init__(self, allowed_commands: List[str], forbidden_commands: List[str]):
        self.allowed_commands = allowed_commands
        self.forbidden_commands = forbidden_commands

    async def execute(self, command: str) -> str:
        """Execute a bash command if allowed."""
        raise NotImplementedError
```

```python
# tests/tool/embedded/__init__.py
"""Tests for embedded tools."""
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tool/embedded/test_bash.py::test_bash_tool_has_required_attributes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/bash.py tests/tool/embedded/__init__.py tests/tool/embedded/test_bash.py
git commit -m "feat(tool): add BashTool class structure"
```

---

### Task 2: BashTool - Permission Checking

**Files:**
- Modify: `src/tool/embedded/bash.py`
- Modify: `tests/tool/embedded/test_bash.py`

**Step 1: Write failing tests for permission checking**

```python
# Add to tests/tool/embedded/test_bash.py

@pytest.mark.asyncio
async def test_bash_tool_denies_command_not_in_allowlist():
    """Commands not in allowlist should be denied."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])
    result = await tool.execute("pwd")

    assert "not allowed" in result.lower()
    assert "pwd" in result


@pytest.mark.asyncio
async def test_bash_tool_denies_forbidden_command():
    """Forbidden commands should be denied even if in allowlist."""
    tool = BashTool(allowed_commands=["rm"], forbidden_commands=["rm"])
    result = await tool.execute("rm file.txt")

    assert "forbidden" in result.lower()
    assert "rm" in result


@pytest.mark.asyncio
async def test_bash_tool_allows_command_in_allowlist():
    """Commands in allowlist (not forbidden) should be allowed."""
    tool = BashTool(allowed_commands=["echo"], forbidden_commands=[])
    # This will test actual execution in next task
    # For now, just check it doesn't return permission error
    result = await tool.execute("echo hello")
    # Should not contain permission denial message
    assert "not allowed" not in result.lower()
    assert "forbidden" not in result.lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/tool/embedded/test_bash.py -v -k "permission or allow or deny or forbid"`
Expected: FAIL (NotImplementedError or no permission logic)

**Step 3: Implement permission checking in BashTool**

```python
# Modify src/tool/embedded/bash.py - replace execute method

    def _parse_command_name(self, command: str) -> str:
        """Extract command name from command string."""
        return command.strip().split()[0] if command.strip() else ""

    def _check_permission(self, command: str) -> tuple[bool, str]:
        """Check if command is allowed.

        Returns:
            Tuple of (is_allowed, error_message)
        """
        cmd_name = self._parse_command_name(command)

        # Forbid takes precedence
        if cmd_name in self.forbidden_commands:
            return False, f"Error: Command '{cmd_name}' is forbidden."

        # Check allowlist
        if cmd_name not in self.allowed_commands:
            allowed = ", ".join(self.allowed_commands) if self.allowed_commands else "none"
            return False, f"Error: Command '{cmd_name}' is not allowed. Allowed commands: {allowed}"

        return True, ""

    async def execute(self, command: str) -> str:
        """Execute a bash command if allowed."""
        is_allowed, error_msg = self._check_permission(command)
        if not is_allowed:
            return error_msg

        # Actual execution in next task
        return "Command allowed but execution not implemented"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/tool/embedded/test_bash.py -v -k "permission or allow or deny or forbid"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/bash.py tests/tool/embedded/test_bash.py
git commit -m "feat(tool): add permission checking to BashTool"
```

---

### Task 3: BashTool - Command Execution

**Files:**
- Modify: `src/tool/embedded/bash.py`
- Modify: `tests/tool/embedded/test_bash.py`

**Step 1: Write failing tests for command execution**

```python
# Add to tests/tool/embedded/test_bash.py

@pytest.mark.asyncio
async def test_bash_tool_executes_allowed_command():
    """BashTool should execute allowed commands and return output."""
    tool = BashTool(allowed_commands=["echo"], forbidden_commands=[])
    result = await tool.execute("echo hello")

    assert "hello" in result


@pytest.mark.asyncio
async def test_bash_tool_returns_stdout_and_stderr():
    """BashTool should return both stdout and stderr combined."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])
    result = await tool.execute("ls /nonexistent_dir_12345")

    # ls should output error to stderr for nonexistent directory
    assert result  # Should have some output
    # The exit code and error message should be in output


@pytest.mark.asyncio
async def test_bash_tool_never_raises_exception():
    """BashTool should always return a string, never raise."""
    tool = BashTool(allowed_commands=["ls"], forbidden_commands=[])

    # Even for failing commands
    result = await tool.execute("ls /nonexistent_dir_12345")
    assert isinstance(result, str)

    # Even for invalid commands
    result2 = await tool.execute("nonexistent_command_xyz")
    assert isinstance(result2, str)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/tool/embedded/test_bash.py -v -k "execute or stdout or stderr or exception"`
Expected: FAIL (execution not implemented)

**Step 3: Implement command execution using asyncio subprocess**

```python
# Modify src/tool/embedded/bash.py - add import and update execute method

import asyncio


    async def execute(self, command: str) -> str:
        """Execute a bash command if allowed."""
        is_allowed, error_msg = self._check_permission(command)
        if not is_allowed:
            return error_msg

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Combine stdout and stderr
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            result = output
            if error:
                result += error

            return result.strip() if result.strip() else "(no output)"

        except Exception as e:
            return f"Error executing command: {str(e)}"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/tool/embedded/test_bash.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/bash.py tests/tool/embedded/test_bash.py
git commit -m "feat(tool): implement command execution in BashTool"
```

---

### Task 4: EmbeddedToolSource - Core Structure

**Files:**
- Create: `src/tool/embedded/source.py`
- Create: `tests/tool/embedded/test_source.py`

**Step 1: Write failing test for EmbeddedToolSource structure**

```python
# tests/tool/embedded/test_source.py
"""Tests for EmbeddedToolSource."""

import pytest
from src.tool.embedded.source import EmbeddedToolSource


@pytest.mark.asyncio
async def test_embedded_source_has_toolsource_methods():
    """EmbeddedToolSource should implement ToolSource protocol."""
    source = EmbeddedToolSource("/tmp/test_permissions.yaml")

    # Should have required methods
    assert hasattr(source, 'load')
    assert hasattr(source, 'get_tools')
    assert hasattr(source, 'execute')
    assert hasattr(source, 'close')

    # Should be callable
    assert callable(source.load)
    assert callable(source.get_tools)
    assert callable(source.execute)
    assert callable(source.close)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tool/embedded/test_source.py::test_embedded_source_has_toolsource_methods -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create EmbeddedToolSource with minimal structure**

```python
# src/tool/embedded/source.py
"""Embedded tool source for ToolRegistry integration."""

from typing import List, Dict, Any
from ..base import ToolDescription
from .bash import BashTool


class EmbeddedToolSource:
    """ToolSource implementation for embedded tools."""

    def __init__(self, permissions_path: str = "permissions.yaml"):
        self.permissions_path = permissions_path
        self._tools: List[BashTool] = []
        self._allowed_commands: List[str] = []
        self._forbidden_commands: List[str] = []

    async def load(self) -> None:
        """Load permissions and initialize tools."""
        raise NotImplementedError

    def get_tools(self) -> List[ToolDescription]:
        """Return list of embedded tools."""
        raise NotImplementedError

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute an embedded tool by name."""
        raise NotImplementedError

    async def close(self) -> None:
        """No cleanup needed for embedded tools."""
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tool/embedded/test_source.py::test_embedded_source_has_toolsource_methods -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/source.py tests/tool/embedded/test_source.py
git commit -m "feat(tool): add EmbeddedToolSource class structure"
```

---

### Task 5: EmbeddedToolSource - Permission Loading

**Files:**
- Modify: `src/tool/embedded/source.py`
- Modify: `tests/tool/embedded/test_source.py`

**Step 1: Write failing tests for permission loading**

```python
# Add to tests/tool/embedded/test_source.py

import tempfile
import os


@pytest.mark.asyncio
async def test_embedded_source_loads_permissions():
    """EmbeddedToolSource should load permissions from YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
allow:
  - Bash(ls)
  - Bash(cat)
forbid:
  - Bash(rm)
""")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        assert "ls" in source._allowed_commands
        assert "cat" in source._allowed_commands
        assert "rm" in source._forbidden_commands
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_creates_empty_config_if_missing():
    """EmbeddedToolSource should create empty permissions if file missing."""
    temp_path = "/tmp/nonexistent_permissions_12345.yaml"

    # Make sure file doesn't exist
    if os.path.exists(temp_path):
        os.unlink(temp_path)

    source = EmbeddedToolSource(temp_path)
    await source.load()

    assert source._allowed_commands == []
    assert source._forbidden_commands == []

    # Should create the file
    assert os.path.exists(temp_path)

    # Cleanup
    os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_parses_bash_tool_format():
    """EmbeddedToolSource should parse Bash(command) format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
allow:
  - Bash(git)
  - Bash(ls)
forbid:
  - Bash(passwd)
""")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        assert "git" in source._allowed_commands
        assert "ls" in source._allowed_commands
        assert "passwd" in source._forbidden_commands
        assert "Bash" not in source._allowed_commands  # Should extract just the command
    finally:
        os.unlink(temp_path)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/tool/embedded/test_source.py -v -k "permission or load or parse"`
Expected: FAIL (NotImplementedError)

**Step 3: Implement permission loading**

```python
# Modify src/tool/embedded/source.py - add imports and implement load

import os
import yaml
import re


    def _parse_tool_permission(self, permission: str) -> tuple[str, str]:
        """Parse 'Tool(command)' format into (tool_name, command).

        Returns:
            Tuple of (tool_name, command) or (tool_name, "") if invalid format.
        """
        match = re.match(r"(\w+)\((\w+)\)", permission.strip())
        if match:
            return match.group(1), match.group(2)
        return permission.strip(), ""

    async def load(self) -> None:
        """Load permissions and initialize tools."""
        # Create empty permissions file if not exists
        if not os.path.exists(self.permissions_path):
            with open(self.permissions_path, 'w') as f:
                yaml.dump({"allow": [], "forbid": []}, f)

        # Load permissions
        with open(self.permissions_path, 'r') as f:
            permissions = yaml.safe_load(f) or {}

        # Parse allow list
        for permission in permissions.get("allow", []):
            tool_name, command = self._parse_tool_permission(permission)
            if tool_name == "Bash" and command:
                self._allowed_commands.append(command)

        # Parse forbid list
        for permission in permissions.get("forbid", []):
            tool_name, command = self._parse_tool_permission(permission)
            if tool_name == "Bash" and command:
                self._forbidden_commands.append(command)

        # Create BashTool with parsed permissions
        bash_tool = BashTool(
            allowed_commands=self._allowed_commands,
            forbidden_commands=self._forbidden_commands
        )
        self._tools = [bash_tool]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/tool/embedded/test_source.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/source.py tests/tool/embedded/test_source.py
git commit -m "feat(tool): implement permission loading in EmbeddedToolSource"
```

---

### Task 6: EmbeddedToolSource - Tool Registration and Execution

**Files:**
- Modify: `src/tool/embedded/source.py`
- Modify: `tests/tool/embedded/test_source.py`

**Step 1: Write failing tests for tool registration and execution**

```python
# Add to tests/tool/embedded/test_source.py

from src.tool.base import ToolDescription


@pytest.mark.asyncio
async def test_embedded_source_returns_tool_descriptions():
    """EmbeddedToolSource should return ToolDescription list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("allow:\n  - Bash(echo)\nforbid: []\n")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()
        tools = source.get_tools()

        assert len(tools) == 1
        assert isinstance(tools[0], dict)
        assert tools[0]["name"] == "bash"
        assert "description" in tools[0]
        assert "inputSchema" in tools[0]
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_executes_tool():
    """EmbeddedToolSource should execute tools by name."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("allow:\n  - Bash(echo)\nforbid: []\n")
        temp_path = f.name

    try:
        source = EmbeddedToolSource(temp_path)
        await source.load()

        result = await source.execute("bash", {"command": "echo test"})
        assert "test" in result
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_embedded_source_raises_for_unknown_tool():
    """EmbeddedToolSource should raise for unknown tool name."""
    source = EmbeddedToolSource()
    await source.load()

    with pytest.raises(ValueError, match="Unknown tool"):
        await source.execute("unknown_tool", {})
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/tool/embedded/test_source.py -v -k "description or execute or unknown"`
Expected: FAIL (NotImplementedError)

**Step 3: Implement get_tools and execute methods**

```python
# Modify src/tool/embedded/source.py - implement remaining methods

    def get_tools(self) -> List[ToolDescription]:
        """Return list of embedded tools."""
        return [
            ToolDescription(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.inputSchema
            )
            for tool in self._tools
        ]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute an embedded tool by name."""
        for tool in self._tools:
            if tool.name == name:
                return await tool.execute(**arguments)

        raise ValueError(f"Unknown tool: {name}. Available: {[t.name for t in self._tools]}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/tool/embedded/test_source.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/embedded/source.py tests/tool/embedded/test_source.py
git commit -m "feat(tool): implement tool registration and execution in EmbeddedToolSource"
```

---

### Task 7: Embedded Module Package

**Files:**
- Create: `src/tool/embedded/__init__.py`

**Step 1: Create embedded module __init__.py**

```python
# src/tool/embedded/__init__.py
"""Embedded tools - bash, filesystem, etc."""

from .source import EmbeddedToolSource
from .bash import BashTool

__all__ = ['EmbeddedToolSource', 'BashTool']
```

**Step 2: Verify imports work**

Run: `python -c "from src.tool.embedded import EmbeddedToolSource, BashTool; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add src/tool/embedded/__init__.py
git commit -m "feat(tool): add embedded module package"
```

---

### Task 8: Tool Factory Function

**Files:**
- Create: `src/tool/factory.py`
- Create: `tests/tool/test_factory.py`

**Step 1: Write failing test for factory function**

```python
# tests/tool/test_factory.py
"""Tests for tool factory."""

import pytest
from src.tool.factory import create_tool_registry
from src.tool.registry import ToolRegistry


def test_create_tool_registry_returns_registry():
    """Factory should return a ToolRegistry instance."""
    registry = create_tool_registry(mcp_servers=[])

    assert isinstance(registry, ToolRegistry)


def test_create_tool_registry_has_mcp_source():
    """Registry should have MCP source when servers provided."""
    registry = create_tool_registry(mcp_servers=[
        {"name": "test", "command": "echo", "args": [], "env": {}}
    ])

    assert len(registry._sources) >= 1


def test_create_tool_registry_has_embedded_source():
    """Registry should have embedded source."""
    registry = create_tool_registry(mcp_servers=[])

    source_types = [type(s).__name__ for s in registry._sources]
    assert "EmbeddedToolSource" in source_types
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/tool/test_factory.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create factory function**

```python
# src/tool/factory.py
"""Factory for creating configured tool registries."""

from typing import List, Dict
from .registry import ToolRegistry
from .mcp import MCPLoader
from .embedded import EmbeddedToolSource


def create_tool_registry(
    mcp_servers: List[Dict],
    permissions_path: str = "permissions.yaml"
) -> ToolRegistry:
    """Create a ToolRegistry with all sources configured.

    Args:
        mcp_servers: List of MCP server configurations
        permissions_path: Path to permissions.yaml file

    Returns:
        Configured ToolRegistry ready to be loaded
    """
    registry = ToolRegistry()

    # Add MCP source
    mcp_loader = MCPLoader(mcp_servers)
    registry.add_source(mcp_loader)

    # Add embedded tools source
    embedded_source = EmbeddedToolSource(permissions_path)
    registry.add_source(embedded_source)

    return registry
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/tool/test_factory.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tool/factory.py tests/tool/test_factory.py
git commit -m "feat(tool): add create_tool_registry factory function"
```

---

### Task 9: Update Tool Module Exports

**Files:**
- Modify: `src/tool/__init__.py`

**Step 1: Update tool module exports**

```python
# Modify src/tool/__init__.py

"""Unified tool module - aggregates tools from MCP and embedded sources."""

from .base import Tool, ToolDescription, ToolResult
from .registry import ToolRegistry, ToolSource
from .factory import create_tool_registry

__all__ = [
    'Tool', 'ToolDescription', 'ToolResult',
    'ToolRegistry', 'ToolSource',
    'create_tool_registry'
]
```

**Step 2: Verify imports work**

Run: `python -c "from src.tool import create_tool_registry; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add src/tool/__init__.py
git commit -m "feat(tool): export create_tool_registry from tool module"
```

---

### Task 10: Update App Integration

**Files:**
- Modify: `src/app.py`

**Step 1: Read current app.py to understand structure**

Run: Read `src/app.py` - focus on tool registry setup section

**Step 2: Update app.py to use factory function**

```python
# Modify src/app.py - update imports and tool registry setup

# Change this import:
# from .tool import ToolRegistry
# To:
from .tool import create_tool_registry

# Replace this section:
#         tool_registry = ToolRegistry()
#         mcp_loader = MCPLoader(mcp_server_dicts)
#         tool_registry.add_source(mcp_loader)
#         await tool_registry.load_all()

# With:
        tool_registry = create_tool_registry(mcp_server_dicts)
        await tool_registry.load_all()
```

**Step 3: Run existing tests to verify no regression**

Run: `pytest tests/ -v -m "not integration"`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/app.py
git commit -m "refactor: use create_tool_registry in app.py"
```

---

### Task 11: Create Default Permissions File

**Files:**
- Create: `permissions.yaml`

**Step 1: Create empty permissions.yaml**

```yaml
# permissions.yaml
# Configure which embedded tool commands are allowed
#
# Format:
#   allow:
#     - Bash(ls)      # Allow ls command
#     - Bash(cat)     # Allow cat command
#   forbid:
#     - Bash(rm)      # Forbid rm command (takes precedence over allow)
#
# By default, no commands are allowed

allow: []
forbid: []
```

**Step 2: Commit**

```bash
git add permissions.yaml
git commit -m "feat: add default empty permissions.yaml"
```

---

### Task 12: Run All Tests

**Step 1: Run all unit tests**

Run: `pytest tests/ -v -m "not integration"`
Expected: All tests PASS

**Step 2: Run integration tests**

Run: `pytest tests/ -v -m integration`
Expected: All tests PASS (if environment configured)

**Step 3: Run with coverage**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: Coverage report shows new files covered

---

## Summary

**Files Created:**
- `src/tool/embedded/__init__.py`
- `src/tool/embedded/bash.py`
- `src/tool/embedded/source.py`
- `src/tool/factory.py`
- `tests/tool/embedded/__init__.py`
- `tests/tool/embedded/test_bash.py`
- `tests/tool/embedded/test_source.py`
- `tests/tool/test_factory.py`
- `permissions.yaml`

**Files Modified:**
- `src/tool/__init__.py` - Export `create_tool_registry`
- `src/app.py` - Use factory function

**Commits:**
1. BashTool class structure
2. Permission checking in BashTool
3. Command execution in BashTool
4. EmbeddedToolSource class structure
5. Permission loading in EmbeddedToolSource
6. Tool registration and execution in EmbeddedToolSource
7. Embedded module package
8. Factory function
9. Tool module exports
10. App integration
11. Default permissions file
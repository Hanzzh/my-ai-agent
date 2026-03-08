# Embedded Filesystem Tools Design

**Date:** 2026-03-08
**Status:** Approved
**Approach:** A - Internal Tool Provider

---

## Overview

Add embedded filesystem tools to the ReAct agent, allowing direct file operations without external MCP servers. Tools are sandboxed to a configurable root directory and coexist with existing MCP tools.

## Architecture

```
ReActAgent
    │
    ├── MCPLoader (external)
    │
    └── ToolRegistry (new)
          │
          └── FilesystemToolProvider (new)
```

---

## Components

### 1. Tool Data Structures (src/tools/base.py)

```python
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., Awaitable[str]]

class ToolProvider(ABC):
    @abstractmethod
    def get_tools(self) -> Dict[str, Tool]:
        pass
```

### 2. Filesystem Tools (src/tools/filesystem.py)

**Class:** FilesystemToolProvider

| Tool | Description | Input Schema |
|------|-------------|--------------|
| read_file | Read file contents | {"path": "string"} |
| write_file | Write content to file | {"path": "string", "content": "string"} |
| delete_file | Delete a file | {"path": "string"} |
| list_directory | List files in directory | {"path": "string"} |
| create_directory | Create directory | {"path": "string"} |
| delete_directory | Remove directory | {"path": "string"} |

### 3. Tool Registry (src/tools/registry.py)

**Class:** ToolRegistry
- register_provider(provider: ToolProvider)
- get_all_tools() -> Dict[str, Tool]

---

## Configuration

```yaml
tools:
  filesystem:
    enabled: true
    root_dir: "/path/to/sandbox"
    allow_write: true
    allow_delete: true
```

---

## Security

- Path validation: Every path must resolve within root_dir
- Path traversal prevention: Reject ../ sequences that escape sandbox
- Configurable permissions: Can disable write/delete operations

---

## Files to Create

- src/tools/__init__.py
- src/tools/base.py
- src/tools/filesystem.py
- src/tools/registry.py

## Files to Modify

- src/agent/react.py
- src/app.py
- config.yaml
- src/config/models.py

---

## Acceptance Criteria

1. Agent can read files from sandboxed directory
2. Agent can write files to sandboxed directory
3. Agent can delete files in sandboxed directory
4. Agent can list directories in sandboxed directory
5. Agent can create/remove directories in sandboxed directory
6. Path traversal attempts are rejected
7. Embedded tools work alongside MCP tools
8. Configuration controls which operations are allowed

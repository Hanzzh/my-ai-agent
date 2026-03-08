# ReAct Agent with MCP Server Support - Design Document

**Date:** 2026-03-08
**Author:** Claude (Sonnet 4.6)
**Status:** Approved

## Overview

A modular ReAct (Reasoning + Acting) pattern AI agent that integrates with MCP (Model Context Protocol) servers. The agent supports pluggable LLM backends (OpenAI-compatible APIs) and dynamically loads MCP server configurations.

**Key Design Principles:**
- Simple initial implementation with room to grow
- Modular architecture for easy testing and maintenance
- Configuration-driven for flexibility
- Stable entry point that never needs modification

## Architecture

### Project Structure

```
my-ai-agent/
├── config.yaml                    # Main configuration (LLM + agent settings)
├── mcp_servers.yaml               # MCP server configurations
├── main.py                        # Stable CLI entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── docs/
│   └── plans/
│       └── 2026-03-08-react-mcp-agent-design.md
└── src/
    ├── __init__.py
    ├── app.py                     # Application orchestration layer
    ├── exceptions.py              # Custom exceptions
    ├── config/
    │   ├── __init__.py
    │   ├── models.py              # Configuration data models
    │   ├── llm_config.py          # LLM config processing
    │   ├── mcp_config.py          # MCP config file loading
    │   ├── env_substitution.py    # Environment variable substitution
    │   └── settings.py            # Main configuration loader
    ├── llm/
    │   ├── __init__.py
    │   ├── base.py                # LLMProvider abstract base
    │   └── openai_client.py       # OpenAI-compatible implementation
    ├── mcp/
    │   ├── __init__.py
    │   ├── client.py              # MCP client wrapper
    │   └── loader.py              # Dynamic MCP server loading
    └── agent/
        ├── __init__.py
        ├── factory.py             # Agent factory pattern
        └── react.py               # ReAct engine implementation
```

## Component Design

### 1. LLM Module (`src/llm/`)

Provides abstraction for any OpenAI-compatible LLM API.

**`base.py` - Abstract Interface:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat messages and return response text"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """Return model name and capabilities"""
        pass
```

**`openai_client.py` - Implementation:**
- Uses `openai` library with `httpx.Client(trust_env=False)`
- Configurable: `api_key`, `base_url`, `model`
- Returns plain text from LLM responses

### 2. MCP Module (`src/mcp/`)

Handles MCP server connections and tool execution.

**`client.py` - MCP Client Wrapper:**
- Wraps `mcp.ClientSession` and `stdio_client`
- Methods: `connect()`, `call_tool()`, `close()`
- Manages server lifecycle (stdio transport)

**`loader.py` - Dynamic Server Loading:**
- Manages multiple `MCPClient` instances
- Methods: `load_all()`, `get_all_tools()`, `close_all()`
- Returns unified tool mapping: `tool_name -> (client, tool)`

### 3. Agent Module (`src/agent/`)

Core ReAct loop implementation.

**`factory.py` - Agent Factory:**
```python
class Agent(ABC):
    @abstractmethod
    async def initialize(self): pass

    @abstractmethod
    async def run(self, question: str, **kwargs) -> str: pass

class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str, llm, mcp_loader, **kwargs) -> Agent:
        # Returns appropriate agent based on config
```

**`react.py` - ReAct Engine:**
- Implements Thought → Action → Observation cycle
- Regex parsing for Action/Answer extraction
- Conversation history management
- Max iterations safety limit
- Verbose mode for debugging

**ReAct Prompt Format:**
```
Thought: <reasoning>
Action: tool_name[json_args]

OR

Thought: <reasoning>
Answer: <final answer>
```

### 4. Configuration Module (`src/config/`)

Split configuration with environment variable substitution.

**`models.py` - Data Models:**
```python
@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str

@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]]

@dataclass
class AgentConfig:
    llm: LLMConfig
    mcp_servers: List[MCPServerConfig]
    agent_type: str = "react"
    max_iterations: int = 10
```

**`llm_config.py` - LLM Config Processing:**
- Parses LLM config from raw dict
- Applies environment variable substitution

**`mcp_config.py` - MCP Config File Loading:**
- Loads MCP servers from separate YAML file
- Parses and validates each server config

**`env_substitution.py` - Environment Variables:**
- Recursively substitutes `${VAR_NAME}` patterns
- Raises clear error if env var not found

**`settings.py` - Main Loader:**
- Orchestrates loading from both YAML files
- Resolves relative paths for MCP config
- Returns complete `AgentConfig` object

### 5. Application Layer (`src/app.py`)

Orchestrates all components without depending on specific agent type.

```python
async def run_agent(question: str):
    config = load_config()
    llm = OpenAICompatibleProvider(...)
    mcp_loader = MCPLoader(...)
    agent = AgentFactory.create_agent(
        agent_type=config.agent_type,
        llm=llm,
        mcp_loader=mcp_loader
    )
    await agent.initialize()
    return await agent.run(question)
```

### 6. Entry Point (`main.py`)

Stable CLI interface that never needs modification.

```python
async def main():
    question = get_question_from_args_or_prompt()
    answer = await run_agent(question)
    print(f"\n✓ Task completed")
```

## Configuration Files

### `config.yaml` - Main Configuration

```yaml
llm:
  api_key: "${GLM_API_KEY}"
  base_url: "${GLM_BASE_URL}"
  model: "glm-4-flash"

agent:
  type: "react"
  max_iterations: 10

mcp_config_file: "mcp_servers.yaml"
```

### `mcp_servers.yaml` - MCP Server Configurations

```yaml
servers:
  - name: weather
    command: python
    args:
      - "/path/to/weather_server.py"

  - name: filesystem
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/home/han/Project"
```

## Data Flow

```
User Input (Question)
       ↓
   main.py (stable)
       ↓
   app.py (orchestration)
       ↓
   load_config()
       ├─→ config.yaml (LLM + agent settings)
       └─→ mcp_servers.yaml (MCP servers)
       ↓
   OpenAICompatibleProvider (LLM)
   MCPLoader (connects to MCP servers)
       ↓
   AgentFactory.create_agent(agent_type from config)
       ↓
   ReActAgent.initialize()
       ↓
   ┌─────────────────────────────────────┐
   │         ReAct Loop                   │
   │  1. LLM.chat() → Thought + Action    │
   │  2. Parse Action → tool_name + args  │
   │  3. MCPClient.call_tool() → Observ.  │
   │  4. Update history + repeat          │
   │         ↓                             │
   │    Final Answer                      │
   └─────────────────────────────────────┘
       ↓
   Output to User
```

## Error Handling

**Custom Exceptions (`src/exceptions.py`):**
- `AgentError` - Base exception
- `LLMError` - LLM provider errors
- `MCPConnectionError` - MCP server connection errors
- `MCPExecutionError` - Tool execution errors
- `ConfigError` - Configuration loading errors

**Error Handling Strategy:**
- Tool errors: Return as observation, continue loop
- LLM errors: Retry with warning message
- Config errors: Fail fast at startup
- MCP connection errors: Fail at initialization

## Dependencies

**`requirements.txt`:**
```
openai>=1.0.0        # LLM API client
mcp>=0.9.0           # MCP protocol support
httpx>=0.27.0        # Async HTTP client
pyyaml>=6.0          # YAML configuration
```

**Development (optional):**
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

## Usage Examples

```bash
# Set environment variables
export GLM_API_KEY="your_key"
export GLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# Run with command line question
python main.py "What's the weather in Shanghai?"

# Run interactively
python main.py

# Switch to different agent pattern (future)
# Just edit config.yaml: agent.type = "planning"
```

## Future Extensibility

**Adding New LLM Providers:**
1. Create new class in `src/llm/` inheriting from `LLMProvider`
2. Add to `AgentFactory` if needed

**Adding New Agent Patterns:**
1. Create new file in `src/agent/` (e.g., `planning.py`)
2. Inherit from `Agent` base class
3. Add to `AgentFactory.create_agent()`
4. Update `agent.type` in `config.yaml`

**Adding New Features:**
- Parallel tool execution: Extend ReAct loop
- Conversation memory: Add persistence layer
- User clarification mode: Add interaction layer

## Success Criteria

- ✅ Agent can successfully connect to MCP servers
- ✅ Agent can execute tools and return observations
- ✅ ReAct loop produces correct final answers
- ✅ Configuration split works (main + MCP files)
- ✅ Environment variable substitution works
- ✅ Switching agent types only requires config change
- ✅ All MCP connections properly cleaned up

## Implementation Notes

- Use `asyncio` throughout (MCP protocol requires async)
- Use regex for parsing (simple and effective for ReAct format)
- Keep tool descriptions concise in prompts
- Max iterations prevents infinite loops
- Verbose mode helps with debugging

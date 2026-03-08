# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular, production-ready ReAct (Reasoning + Acting) pattern AI agent that integrates with MCP (Model Context Protocol) servers for extensible tool capabilities. The project uses Python 3.8+ with async/await throughout.

## Common Commands

### Running the Agent

```bash
# Run with a question directly
python main.py "What is the capital of France?"

# Run interactively
python main.py

# Show help
python main.py --help
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run only unit tests (exclude integration)
pytest tests/ -v -m "not integration"

# Run only integration tests
pytest tests/ -v -m integration

# Run specific test file
pytest tests/test_integration.py -v

# Run specific test
pytest tests/agent/test_react.py::test_react_agent_direct_answer -v
```

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys
```

## Architecture Overview

The project follows a **layered architecture** with clear separation of concerns:

```
CLI Layer (main.py)
    ↓
Application Layer (src/app.py)
    ↓
Agent Layer (src/agent/) ← LLM Layer (src/llm/) ← MCP Layer (src/mcp/)
    ↓
Configuration Layer (src/config/)
```

### Key Flow

1. **main.py** handles CLI interaction → calls `src.app.run_agent()`
2. **app.py** orchestrates: load config → init LLM → init MCP → create agent → run → cleanup
3. **AgentFactory** creates agent instances based on `config.yaml` agent type
4. **ReActAgent** runs the Thought-Action-Observation loop using LLM and MCP tools
5. **MCPLoader** manages subprocess-based MCP servers and aggregates their tools

### Entry Points

- `main.py`: CLI entry point with banner, help, and interactive mode
- `src/app.run_agent()`: Main async orchestration function (use this programmatically)
- `src/app.run_agent_batch()`: Process multiple questions sequentially

## Configuration

### Main Configuration Files

- **config.yaml**: LLM settings (api_key, base_url, model), agent type, max_iterations
- **mcp_servers.yaml**: MCP server definitions (name, command, args, env)
- **.env**: Environment variables (API keys, base URLs) - use `${VAR}` syntax in YAML for substitution

### Environment Variables

The project uses `OPENAI_API_KEY` and `OPENAI_BASE_URL` environment variables. These can be set for:
- OpenAI API: `OPENAI_API_KEY=sk-...`, `OPENAI_BASE_URL=https://api.openai.com/v1`
- GLM API (智谱AI): `OPENAI_API_KEY=...`, `OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/`

## Component Details

### Agent Layer (`src/agent/`)

- **base.py**: Abstract `Agent` class with `initialize()` and `run()` methods
- **factory.py**: `AgentFactory.create_agent()` - register new agent types here
- **react.py**: `ReActAgent` - Thought-Action-Observation loop implementation

**To add a new agent type**: Create class inheriting `Agent`, register in `AgentFactory.create_agent()`

### LLM Layer (`src/llm/`)

- **base.py**: Abstract `LLMProvider` with `chat(messages)` and `get_model_info()`
- **openai_client.py**: `OpenAICompatibleProvider` - works with OpenAI and compatible APIs

**To add a new LLM provider**: Inherit from `LLMProvider`, update `src/app.py` initialization

### MCP Layer (`src/mcp/`)

- **client.py**: `MCPClient` wrapper for individual MCP server connections
- **loader.py**: `MCPLoader` manages multiple MCP servers, aggregates tools from all

### Configuration Layer (`src/config/`)

- **models.py**: Pydantic models (`LLMConfig`, `MCPServerConfig`, `AgentConfig`)
- **settings.py**: `load_config()` - loads main config, delegates to specialized loaders
- **llm_config.py**: `load_llm_config()` - LLM config with env var substitution
- **mcp_config.py**: `load_mcp_configs_from_file()` - MCP server configs
- **env_substitution.py**: `_substitute_env_vars()` - expands `${VAR}` syntax

## Code Patterns

### Async/Await

All I/O operations use async/await:
- MCP server communication
- LLM calls
- Tool execution

### Lifecycle Management

Resources are managed in try-except-finally blocks with cleanup in `finally`:
```python
try:
    await mcp_loader.load_all()
    # ... work ...
finally:
    await mcp_loader.close_all()
```

### Error Handling

- **CLI Layer**: KeyboardInterrupt for graceful exit, helpful error messages
- **Application Layer**: Configuration errors logged, resources cleaned up in finally
- **Component Layers**: LLM errors may retry, MCP errors degrade gracefully

## Test Organization

```
tests/
├── agent/          # Agent unit tests
├── llm/            # LLM unit tests
├── mcp/            # MCP unit tests
└── test_integration.py  # Integration tests (marked with @pytest.mark.integration)
```

Integration tests are marked with `@pytest.mark.integration` for selective running. Unit tests mock all dependencies (LLM, MCP, subprocess).

## Adding New Features

### New Agent Type

1. Create `src/agent/my_agent.py` with class inheriting `Agent`
2. Implement `async def initialize(self)` and `async def run(self, question: str) -> str`
3. Add case in `AgentFactory.create_agent()`
4. Update `config.yaml` agent.type

### New MCP Tool

No code changes needed - just add to `mcp_servers.yaml`:
```yaml
servers:
  - name: my_tool
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
```

### New LLM Provider

1. Create `src/llm/my_provider.py` inheriting `LLMProvider`
2. Implement `chat(messages, **kwargs) -> str` and `get_model_info() -> dict`
3. Update `src/app.py` to instantiate your provider based on config

## File Locations

- **Entry point**: `main.py`
- **Orchestration**: `src/app.py`
- **Agent logic**: `src/agent/react.py`
- **Configuration loading**: `src/config/settings.py`
- **Test config**: `pytest.ini` (defines asyncio_mode, markers)
- **Dependencies**: `requirements.txt`
- **Documentation**: `docs/ARCHITECTURE.md` (comprehensive architecture docs)

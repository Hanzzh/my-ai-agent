# Architecture Documentation

This document provides a comprehensive overview of the AI Agent system architecture, design patterns, and component interactions.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [System Architecture](#system-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Error Handling](#error-handling)
- [Testing Strategy](#testing-strategy)
- [Extension Points](#extension-points)

## Overview

The AI Agent system is a modular, extensible framework for building intelligent agents that can reason and act using external tools. The system follows the ReAct (Reasoning + Acting) pattern and integrates with MCP (Model Context Protocol) servers for tool capabilities.

### Key Goals

1. **Modularity**: Each component has a single, well-defined responsibility
2. **Extensibility**: Easy to add new agent types, LLM providers, and tools
3. **Testability**: Comprehensive testing with mocked dependencies
4. **Production Ready**: Proper error handling, logging, and resource management
5. **Flexibility**: Configuration-driven behavior with environment variable support

## Design Principles

### Separation of Concerns

Each layer has a specific responsibility:
- **CLI Layer**: User interaction and argument parsing
- **Application Layer**: Orchestration and lifecycle management
- **Agent Layer**: Reasoning and action execution
- **LLM Layer**: Language model abstraction
- **MCP Layer**: Tool integration
- **Config Layer**: Configuration management

### Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions:
- Agents depend on `LLMProvider` interface, not concrete implementations
- System depends on `Agent` base class, not specific agent types

### Factory Pattern

Centralized agent creation via `AgentFactory` for:
- Consistent initialization
- Easy addition of new agent types
- Configuration-driven instantiation

## System Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│                         main.py                             │
│  • Argument parsing                                         │
│  • User interaction                                         │
│  • Entry point                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Application Layer                         │
│                      src/app.py                             │
│  • Component orchestration                                  │
│  • Lifecycle management (init/cleanup)                      │
│  • Error handling and logging                               │
└─────────────┬─────────────────────────────┬─────────────────┘
              │                             │
    ┌─────────▼─────────┐       ┌──────────▼──────────┐
    │   Config Loader   │       │   Agent Factory     │
    │   (settings.py)   │       │   (factory.py)      │
    └───────────────────┘       └──────────┬──────────┘
                                             │
    ┌────────────────────────────────────────┼────────────────┐
    │                                        │                │
┌───▼────┐  ┌────────────────┐  ┌──────────▼──────────┐
│  LLM   │  │  MCP Layer     │  │   Agent Layer       │
│ src/   │  │  src/mcp/      │  │   src/agent/        │
│ llm/   │  │  • Client      │  │  • ReAct Engine     │
│        │  │  • Loader      │  │  • Base Class       │
│  OpenAI│  │  • Servers     │  │  • Factory          │
│ Client │  │                │  │                    │
└────────┘  └────────────────┘  └─────────────────────┘
```

### Component Interaction Diagram

```
User Input
    │
    ▼
┌─────────┐
│ main.py │  (CLI Entry Point)
└────┬────┘
     │
     ▼
┌─────────────┐
│  run_agent  │  (Application Orchestration)
└──────┬──────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌──────────┐  ┌──────────┐
│load_config│  │Initialize│
└─────┬─────┘  │   LLM    │
      │       └────┬─────┘
      ▼            │
┌──────────┐       │
│Initialize │       │
│   MCP    │       │
└─────┬────┘       │
      │            │
      ▼            │
┌──────────┐       │
│Create    │       │
│Agent     │◄──────┘
│via       │
│Factory   │
└─────┬────┘
      │
      ▼
┌──────────┐
│  Agent   │  (ReAct Loop)
│  run()   │
└─────┬────┘
      │
      ├─────────────┐
      │             │
      ▼             ▼
┌──────────┐  ┌──────────┐
│   LLM    │  │   MCP    │
│  chat()  │  │  Tools   │
└──────────┘  └──────────┘
      │             │
      └──────┬──────┘
             ▼
      ┌──────────┐
      │ Response │
      └──────────┘
```

## Component Details

### 1. CLI Layer (`main.py`)

**Responsibility**: User interaction and program entry point

**Key Functions**:
- `main()`: Synchronous entry point
- `main_async()`: Async main logic
- `print_banner()`: Display branding
- `print_help()`: Show usage information

**Features**:
- Command-line argument parsing
- Interactive mode
- Help system
- KeyboardInterrupt handling
- Clean error messages

**Dependencies**:
- `src.app.run_agent`

### 2. Application Layer (`src/app.py`)

**Responsibility**: Orchestrate all components and manage lifecycle

**Key Functions**:
- `run_agent()`: Main orchestration function
- `run_agent_batch()`: Batch processing
- `main()`: Synchronous entry point

**Responsibilities**:
1. Load configuration
2. Initialize LLM provider
3. Load MCP servers
4. Create agent via factory
5. Run agent
6. Cleanup resources

**Error Handling**:
- Try-except-finally pattern
- Comprehensive logging
- Resource cleanup in finally block

**Lifecycle**:
```
Init → Load Config → Init LLM → Init MCP → Create Agent → Run → Cleanup
```

### 3. Configuration Layer (`src/config/`)

#### `models.py`

**Data Models**:
- `LLMConfig`: LLM connection settings
- `MCPServerConfig`: MCP server configuration
- `AgentConfig`: Main configuration container

**Features**:
- Pydantic validation
- Type safety
- Default values
- Environment variable expansion

#### `settings.py`

**Functions**:
- `load_config()`: Load and parse YAML config
- `_substitute_env_vars()`: Expand ${VAR} syntax

**Features**:
- YAML parsing
- Environment variable substitution
- Path resolution
- Error handling

### 4. LLM Layer (`src/llm/`)

#### `base.py`

**Interface**: `LLMProvider` (Abstract Base Class)

**Methods**:
- `chat(messages, **kwargs) -> str`: Send chat messages
- `get_model_info() -> dict`: Get model metadata

**Purpose**: Abstraction for different LLM providers

#### `openai_client.py`

**Implementation**: `OpenAICompatibleProvider`

**Features**:
- OpenAI API compatibility
- Chat completions
- Model info retrieval
- Error handling

**Supported Providers**:
- OpenAI
- GLM (智谱AI)
- Any OpenAI-compatible API

### 5. MCP Layer (`src/mcp/`)

#### `client.py`

**Class**: `MCPClient`

**Responsibilities**:
- Wrap MCP client library
- Provide simplified interface
- Error handling

**Key Methods**:
- `call_tool(name, arguments)`: Execute tool
- `list_tools()`: Get available tools
- `initialize()`: Connect to server
- `cleanup()`: Close connection

#### `loader.py`

**Class**: `MCPLoader`

**Responsibilities**:
- Load MCP server configurations
- Spawn subprocess for each server
- Manage client connections
- Aggregate tools from all servers

**Key Methods**:
- `initialize()`: Start all servers
- `get_all_tools()`: Get tools from all servers
- `cleanup()`: Shutdown all servers
- `_spawn_server()`: Start individual server

**Tool Format**:
```python
{
    "tool_name": (MCPClient, Tool),
    ...
}
```

### 6. Agent Layer (`src/agent/`)

#### `base.py`

**Interface**: `Agent` (Abstract Base Class)

**Methods**:
- `initialize()`: Setup agent
- `run(question, **kwargs) -> str`: Execute agent

**Purpose**: Common interface for all agent types

#### `react.py`

**Implementation**: `ReActAgent`

**ReAct Loop**:
```
Observation → Thought → Action → Observation → ...
                                            ↓
                                      Final Answer
```

**Key Methods**:
- `initialize()`: Load tools from MCP
- `run()`: Execute ReAct loop
- `_get_system_prompt()`: Build prompt with tools
- `_format_tools_description()`: Format tools for LLM
- `_parse_action()`: Extract action from LLM response
- `_parse_answer()`: Extract final answer
- `_execute_action()`: Run tool or finalize

**Prompt Template**:
```
You are a helpful assistant with access to tools.

Available tools:
- tool1: description
- tool2: description

Use the following format:

Thought: your reasoning
Action: tool name (or Final Answer)
Action Input: JSON input for tool

Observation: tool result
... (repeat)

Thought: I know the answer
Action: Final Answer
Action Input: your answer
```

#### `factory.py`

**Class**: `AgentFactory`

**Method**:
- `create_agent(type, llm, mcp_loader, **kwargs) -> Agent`

**Purpose**: Centralized agent creation

## Data Flow

### Request Flow

```
1. User Input (main.py)
   ↓
2. run_agent() (app.py)
   ↓
3. Load Configuration (config/settings.py)
   ↓
4. Initialize LLM Provider (llm/openai_client.py)
   ↓
5. Initialize MCP Loader (mcp/loader.py)
   ↓
6. Create Agent (agent/factory.py)
   ↓
7. Agent.run() (agent/react.py)
   ↓
8. ReAct Loop:
   - LLM.chat() → Get thought/action
   - Parse action
   - If tool: MCPClient.call_tool()
   - If final answer: Return result
   - Repeat until final answer or max iterations
   ↓
9. Return to user (main.py)
```

### ReAct Loop Detail

```
┌─────────────────────────────────────────────────────┐
│              Start ReAct Loop                       │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │ Format Prompt   │
            │ (Question +     │
            │  Tools +        │
            │  History)       │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ LLM.chat()      │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Parse Response  │
            └────────┬────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐         ┌─────────────────┐
│ Final Answer │         │ Tool Action     │
└──────┬───────┘         └────────┬────────┘
       │                         │
       │                         ▼
       │               ┌─────────────────┐
       │               │ Execute Tool    │
       │               │ (MCP)           │
       │               └────────┬────────┘
       │                         │
       │                         ▼
       │               ┌─────────────────┐
       │               │ Add Observation │
       │               │ to History      │
       │               └────────┬────────┘
       │                         │
       └─────────────────────────┤
                                 │
                                 ▼
                       ┌─────────────────┐
                       │ Max Iterations? │
                       └────────┬────────┘
                                │
                    ┌───────────┴───────────┐
                    │ No                   │ Yes
                    ▼                       ▼
              ┌─────────┐           ┌──────────────┐
              │Continue │           │ Return Error │
              └────┬────┘           └──────────────┘
                   │
                   └─────────────────┘
```

## Design Patterns

### 1. Factory Pattern

**Location**: `src/agent/factory.py`

**Purpose**: Create agents based on configuration

**Benefits**:
- Decouples agent creation from usage
- Easy to add new agent types
- Centralized instantiation logic

### 2. Abstract Factory

**Location**: `src/llm/base.py`, `src/agent/base.py`

**Purpose**: Define interfaces for families of related objects

**Benefits**:
- Interchangeable implementations
- Loose coupling
- Easy testing with mocks

### 3. Strategy Pattern

**Location**: Agent selection via configuration

**Purpose**: Different agent strategies (ReAct, future types)

**Benefits**:
- Runtime selection
- Easy to add new strategies
- Configuration-driven

### 4. Facade Pattern

**Location**: `src/app.py`

**Purpose**: Simplified interface to complex subsystem

**Benefits**:
- Single entry point
- Hides complexity
- Easier to use

### 5. Dependency Injection

**Location**: Throughout the codebase

**Purpose**: Inject dependencies rather than create them

**Benefits**:
- Easier testing
- Loose coupling
- Flexibility

## Error Handling

### Layers of Error Handling

1. **CLI Layer**
   - KeyboardInterrupt: Graceful exit
   - User input errors: Helpful messages

2. **Application Layer**
   - Configuration errors: Clear error messages
   - Initialization failures: Cleanup resources
   - Execution errors: Log and propagate

3. **Component Layers**
   - LLM errors: Retry or fallback
   - MCP errors: Graceful degradation
   - Agent errors: Max iteration protection

### Error Handling Pattern

```python
try:
    # Initialize resources
    ...
except Exception as e:
    logger.error(f"Initialization failed: {e}")
    raise
finally:
    # Always cleanup
    await cleanup()
```

### Logging Strategy

- **INFO**: Normal operations, progress
- **WARNING**: Recoverable issues
- **ERROR**: Failures requiring attention
- **DEBUG**: Detailed debugging info

## Testing Strategy

### Test Pyramid

```
        ┌────────────┐
        │  E2E Tests │  (Few, Integration)
        └────────────┘
       ┌────────────────┐
       │  Integration   │  (Some, test_integration.py)
       └────────────────┘
      ┌──────────────────────┐
      │    Unit Tests        │  (Many, component tests)
      └──────────────────────┘
```

### Testing Approaches

1. **Unit Tests**
   - Test individual components
   - Mock all dependencies
   - Fast execution
   - High coverage

2. **Integration Tests**
   - Test component interactions
   - Mock external services (LLM, MCP)
   - Verify end-to-end flows
   - Marked with `@pytest.mark.integration`

3. **Test Structure**
   ```
   tests/
   ├── agent/          # Agent unit tests
   ├── llm/            # LLM unit tests
   ├── mcp/            # MCP unit tests
   └── test_integration.py  # Integration tests
   ```

### Mocking Strategy

- **LLM**: Mock `LLMProvider` with predefined responses
- **MCP**: Mock `MCPLoader` and `MCPClient`
- **Subprocess**: Mock `asyncio.create_subprocess_exec`
- **File System**: Use `tempfile` for temp files

### Coverage Goals

- Unit tests: >90% coverage
- Integration tests: Critical paths covered
- Edge cases: Error conditions tested

## Extension Points

### Adding New Agent Types

1. Create agent class in `src/agent/`
2. Inherit from `Agent` base class
3. Implement `initialize()` and `run()`
4. Register in `AgentFactory.create_agent()`
5. Update `config.yaml` to use new type

### Adding New LLM Providers

1. Create provider in `src/llm/`
2. Inherit from `LLMProvider` base class
3. Implement `chat()` and `get_model_info()`
4. Update `src/app.py` to use new provider
5. Update configuration schema if needed

### Adding New MCP Tools

1. Configure MCP server in `mcp_servers.yaml`
2. Server will be auto-loaded by `MCPLoader`
3. Tools auto-appear in agent's tool list
4. No code changes needed!

### Custom Configuration

1. Extend models in `src/config/models.py`
2. Update `settings.py` loading logic
3. Update `config.yaml` schema
4. Update `src/app.py` to use new config

## Performance Considerations

### Async/Await Usage

- All I/O operations are async
- MCP communication: async
- LLM calls: Can be made async
- Tool execution: async

### Resource Management

- MCP subprocesses properly cleaned up
- LLM connections closed
- Memory: History management in loops

### Optimization Opportunities

1. **Batch Processing**: `run_agent_batch()` for multiple questions
2. **Caching**: Cache LLM responses for repeated queries
3. **Parallel Tool Calls**: Execute independent tools concurrently
4. **Streaming**: Stream LLM responses for long answers

## Security Considerations

### API Key Management

- Use environment variables
- Never commit `.env` file
- Use `.env.example` as template
- Rotate keys regularly

### MCP Server Safety

- Validate server configurations
- Sandbox tool execution
- Limit file system access
- Monitor for malicious tools

### Input Validation

- Sanitize user input
- Validate tool arguments
- Limit iteration count
- Protect against prompt injection

## Future Enhancements

### Potential Features

1. **Multi-Agent Systems**: Multiple specialized agents
2. **Memory**: Persistent conversation history
3. **Streaming**: Real-time response streaming
4. **Tool Chaining**: Complex multi-step workflows
5. **Parallel Execution**: Concurrent tool use
6. **Monitoring**: Performance metrics and logging
7. **Web UI**: Browser-based interface
8. **API Server**: RESTful API endpoint
9. **Plugins**: Dynamic plugin loading
10. **Agent Templates**: Pre-built agent configurations

### Architectural Improvements

1. **Event Bus**: Pub/sub for agent events
2. **Middleware**: Pre/post processing hooks
3. **Circuit Breaker**: Fault tolerance for external services
4. **Rate Limiting**: Control API usage
5. **Distributed Execution**: Run across multiple machines

## Conclusion

This architecture provides a solid foundation for building intelligent, extensible AI agents. The modular design ensures easy maintenance and enhancement, while the comprehensive testing ensures reliability.

For questions or contributions, please refer to the main README.md file.

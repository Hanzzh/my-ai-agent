# ReAct Agent with MCP Server Support

A modular, production-ready ReAct (Reasoning + Acting) pattern AI agent that integrates with MCP (Model Context Protocol) servers for extensible tool capabilities.

## Features

- **ReAct Agent Pattern**: Combines reasoning and acting for intelligent task execution
- **MCP Server Integration**: Extensible tool support via Model Context Protocol servers
- **Modular Architecture**: Clean separation of concerns with pluggable components
- **Multiple LLM Support**: Works with OpenAI-compatible APIs (OpenAI, GLM, etc.)
- **Flexible Configuration**: YAML-based configuration with environment variable substitution
- **Comprehensive Testing**: Unit and integration tests with high coverage
- **Production Ready**: Proper error handling, logging, and resource cleanup

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd my-ai-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Configure MCP servers:
   - Edit `config.yaml` for LLM settings
   - Edit `mcp_servers.yaml` for MCP server configurations

## Quick Start

### Using GLM API

```bash
# Set environment variables
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# Run with command line question
python main.py "What's the weather in Shanghai?"

# Run interactively
python main.py
```

### Using OpenAI API

Update `config.yaml`:
```yaml
llm:
  api_key: "${OPENAI_API_KEY}"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
```

Then run:
```bash
export OPENAI_API_KEY="your_openai_key"
python main.py "Explain quantum computing"
```

## Configuration

### Main Configuration (`config.yaml`)

```yaml
# LLM Configuration
llm:
  api_key: "${OPENAI_API_KEY}"      # Use environment variables
  base_url: "${OPENAI_BASE_URL}"
  model: "glm-4-flash"

# Agent Settings
agent:
  type: "react"                  # Agent type (currently only "react")
  max_iterations: 10             # Maximum reasoning iterations

# MCP Servers Configuration File
mcp_config_file: "mcp_servers.yaml"
```

### MCP Servers Configuration (`mcp_servers.yaml`)

```yaml
servers:
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    env:
      PATH: "${PATH}"

  - name: fetch
    command: uvx
    args: ["mcp-server-fetch"]
```

### Environment Variables (`.env`)

```bash
# LLM API Configuration
OPENAI_API_KEY=your_glm_api_key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# Or for OpenAI
OPENAI_API_KEY=your_openai_key
```

## Usage

### Command Line Interface

```bash
# Ask a question directly
python main.py "What is the capital of France?"

# Interactive mode
python main.py

# Get help
python main.py --help
```

### Python API

```python
import asyncio
from src.app import run_agent

async def main():
    result = await run_agent("Explain machine learning")
    print(result)

asyncio.run(main())
```

### Batch Processing

```python
import asyncio
from src.app import run_agent_batch

async def main():
    questions = [
        "What is Python?",
        "Explain async/await",
        "What are decorators?"
    ]
    results = await run_agent_batch(questions)
    for q, r in zip(questions, results):
        print(f"Q: {q}\nA: {r}\n")

asyncio.run(main())
```

## Architecture

The project follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Layer                          │
│                      main.py                            │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  Application Layer                      │
│                    src/app.py                           │
│  - Orchestrates all components                          │
│  - Manages lifecycle and cleanup                        │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────┐ ┌───────▼─────────┐
│   Agent Layer   │ │  LLM   │ │   MCP Layer     │
│  src/agent/     │ │ src/   │ │   src/mcp/      │
│  - ReAct Engine │ │ llm/   │ │  - Client       │
│  - Factory      │ │  -     │ │  - Loader       │
│                 │ │  OpenAI│ │  - Servers      │
└─────────────────┘ └────────┘ └─────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               Configuration Layer                        │
│                   src/config/                           │
│  - Models, Settings, Environment Substitution           │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Agent Layer** (`src/agent/`)
   - `factory.py`: Creates agents based on configuration
   - `react.py`: ReAct pattern implementation
   - `base.py`: Abstract agent interface

2. **LLM Layer** (`src/llm/`)
   - `base.py`: LLM provider abstraction
   - `openai_client.py`: OpenAI-compatible implementation

3. **MCP Layer** (`src/mcp/`)
   - `client.py`: MCP client wrapper
   - `loader.py`: Dynamic MCP server loader

4. **Configuration** (`src/config/`)
   - `models.py`: Pydantic data models
   - `settings.py`: Configuration loading with env var substitution

5. **Application** (`src/app.py`)
   - Orchestrates all components
   - Manages lifecycle and error handling

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Development

### Project Structure

```
my-ai-agent/
├── src/
│   ├── agent/          # Agent implementations
│   ├── llm/            # LLM provider abstractions
│   ├── mcp/            # MCP client and loader
│   ├── config/         # Configuration management
│   └── app.py          # Application orchestration
├── tests/              # Test suite
│   ├── agent/          # Agent tests
│   ├── llm/            # LLM tests
│   ├── mcp/            # MCP tests
│   └── test_integration.py  # Integration tests
├── docs/               # Documentation
├── main.py             # CLI entry point
├── config.yaml         # Main configuration
├── mcp_servers.yaml    # MCP server configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### Adding New Agent Types

1. Create a new agent class in `src/agent/`:

```python
from .base import Agent

class MyAgent(Agent):
    async def initialize(self):
        # Initialize your agent
        pass

    async def run(self, question: str, **kwargs) -> str:
        # Implement your agent logic
        return "result"
```

2. Register in `src/agent/factory.py`:

```python
@staticmethod
def create_agent(agent_type: str, llm, mcp_loader, **kwargs) -> Agent:
    if agent_type == "react":
        from .react import ReActAgent
        return ReActAgent(llm=llm, mcp_loader=mcp_loader, **kwargs)
    elif agent_type == "my_agent":
        from .my_agent import MyAgent
        return MyAgent(llm=llm, mcp_loader=mcp_loader, **kwargs)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
```

3. Update `config.yaml`:

```yaml
agent:
  type: "my_agent"
  max_iterations: 10
```

### Adding New LLM Providers

1. Create a new provider in `src/llm/`:

```python
from .base import LLMProvider

class MyProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def chat(self, messages: list, **kwargs) -> str:
        # Implement chat logic
        return response

    def get_model_info(self) -> dict:
        return {"name": self.model, "provider": "my_provider"}
```

2. Update `src/app.py` to use your provider.

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and modular
- Write tests for new features

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run only unit tests
pytest tests/ -v -m "not integration"

# Run only integration tests
pytest tests/ -v -m integration

# Run specific test file
pytest tests/test_integration.py -v

# Run specific test
pytest tests/agent/test_react.py::test_react_agent_direct_answer -v
```

### Test Coverage

The project maintains high test coverage:

- Unit tests for individual components
- Integration tests for end-to-end flows
- Mocked external dependencies (LLM, MCP servers)
- Async test support with pytest-asyncio

### Writing Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_my_feature():
    # Arrange
    mock_obj = Mock()
    mock_obj.method = AsyncMock(return_value="result")

    # Act
    result = await my_function(mock_obj)

    # Assert
    assert result == "result"
    mock_obj.method.assert_called_once()
```

## Project Structure

```
my-ai-agent/
├── src/
│   ├── __init__.py
│   ├── app.py                  # Application orchestration layer
│   ├── agent/                  # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract agent base class
│   │   ├── factory.py          # Agent factory pattern
│   │   └── react.py            # ReAct agent implementation
│   ├── llm/                    # LLM provider layer
│   │   ├── __init__.py
│   │   ├── base.py             # LLM provider abstraction
│   │   └── openai_client.py    # OpenAI-compatible client
│   ├── mcp/                    # MCP integration layer
│   │   ├── __init__.py
│   │   ├── client.py           # MCP client wrapper
│   │   └── loader.py           # Dynamic MCP server loader
│   └── config/                 # Configuration layer
│       ├── __init__.py
│       ├── models.py           # Pydantic data models
│       └── settings.py         # Configuration loader
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── agent/                  # Agent tests
│   │   ├── __init__.py
│   │   └── test_react.py
│   ├── llm/                    # LLM tests
│   │   ├── __init__.py
│   │   └── test_openai_client.py
│   ├── mcp/                    # MCP tests
│   │   ├── __init__.py
│   │   ├── test_client.py
│   │   └── test_loader.py
│   └── test_integration.py     # Integration tests
├── docs/                       # Documentation
│   └── ARCHITECTURE.md         # Architecture documentation
├── main.py                     # CLI entry point
├── config.yaml                 # Main configuration file
├── mcp_servers.yaml            # MCP server configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/ -v --cov=src`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest tests/ -v --cov=src

# Check coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## License

This project is licensed under the MIT License.

## Acknowledgments

- ReAct paper: "ReAct: Synergizing Reasoning and Acting in Language Models"
- Model Context Protocol (MCP) by Anthropic
- OpenAI for the API standard

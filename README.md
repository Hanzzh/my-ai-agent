# ReAct Agent with MCP Server Support

A modular ReAct (Reasoning + Acting) pattern AI agent that integrates with MCP (Model Context Protocol) servers.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Configure MCP servers:
   - Edit `config.yaml` for LLM settings
   - Edit `mcp_servers.yaml` for MCP server configurations

## Usage

```bash
# Set environment variables
export GLM_API_KEY="your_key"
export GLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# Run with command line question
python main.py "What's the weather in Shanghai?"

# Run interactively
python main.py
```

## Architecture

- `src/llm/` - LLM provider abstraction
- `src/mcp/` - MCP client and loader
- `src/agent/` - ReAct engine and factory
- `src/config/` - Configuration management
- `src/app.py` - Application orchestration
- `main.py` - CLI entry point

"""Configuration data models."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    api_key: str
    base_url: str
    model: str


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None


@dataclass
class AgentConfig:
    """Complete agent configuration."""
    llm: LLMConfig
    mcp_servers: List[MCPServerConfig]
    agent_type: str = "react"
    max_iterations: int = 10

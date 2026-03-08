"""Main configuration loader."""

import yaml
from pathlib import Path
from .models import AgentConfig
from .llm_config import load_llm_config
from .mcp_config import load_mcp_configs_from_file


def load_config(config_path: str = "config.yaml") -> AgentConfig:
    """
    Load agent configuration from main config file.

    Args:
        config_path: Path to main configuration file

    Returns:
        Parsed AgentConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)

    # Load MCP config from separate file
    mcp_config_file = raw_config.get('mcp_config_file', 'mcp_servers.yaml')
    # Resolve relative to main config file directory
    config_dir = config_file.parent
    mcp_config_path = config_dir / mcp_config_file

    return AgentConfig(
        llm=load_llm_config(raw_config),
        mcp_servers=load_mcp_configs_from_file(str(mcp_config_path)),
        agent_type=raw_config.get('agent', {}).get('type', 'react'),
        max_iterations=raw_config.get('agent', {}).get('max_iterations', 10)
    )

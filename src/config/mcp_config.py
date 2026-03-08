"""MCP server configuration loading."""

import yaml
from pathlib import Path
from .models import MCPServerConfig
from .env_substitution import substitute_env_vars


def load_mcp_configs_from_file(config_path: str) -> list:
    """
    Load MCP server configurations from a separate YAML file.

    Args:
        config_path: Path to MCP servers configuration file

    Returns:
        List of MCPServerConfig objects

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    mcp_config_file = Path(config_path)
    if not mcp_config_file.exists():
        raise FileNotFoundError(f"MCP config file not found: {config_path}")

    with open(mcp_config_file, 'r') as f:
        raw_config = yaml.safe_load(f)

    mcp_servers = []

    for server in raw_config.get('servers', []):
        server_data = substitute_env_vars(server)

        mcp_servers.append(MCPServerConfig(
            name=server_data['name'],
            command=server_data['command'],
            args=server_data.get('args', []),
            env=server_data.get('env')
        ))

    return mcp_servers

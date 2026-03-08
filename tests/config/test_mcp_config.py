"""Tests for MCP configuration loading."""

import pytest
import yaml
from pathlib import Path
from src.config.mcp_config import load_mcp_configs_from_file


@pytest.fixture
def temp_mcp_config(tmp_path):
    """Create a temporary MCP config file."""
    config_file = tmp_path / "test_mcp.yaml"
    config_data = {
        "servers": [
            {
                "name": "weather",
                "command": "python",
                "args": ["server.py"]
            },
            {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
            }
        ]
    }
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    return config_file


def test_load_mcp_configs_from_file(temp_mcp_config):
    configs = load_mcp_configs_from_file(str(temp_mcp_config))

    assert len(configs) == 2
    assert configs[0].name == "weather"
    assert configs[0].command == "python"
    assert configs[0].args == ["server.py"]

    assert configs[1].name == "filesystem"
    assert configs[1].command == "npx"
    assert len(configs[1].args) == 3


def test_load_mcp_configs_file_not_found():
    with pytest.raises(FileNotFoundError, match="MCP config file not found"):
        load_mcp_configs_from_file("/nonexistent/path.yaml")


def test_load_mcp_configs_empty_servers(tmp_path):
    config_file = tmp_path / "empty_mcp.yaml"
    with open(config_file, 'w') as f:
        yaml.dump({"servers": []}, f)

    configs = load_mcp_configs_from_file(str(config_file))
    assert configs == []


def test_load_mcp_configs_with_env_vars(monkeypatch, tmp_path):
    """Test environment variable substitution in MCP configs."""
    monkeypatch.setenv("TEST_CMD", "python3")
    monkeypatch.setenv("TEST_API_KEY", "secret123")

    config_file = tmp_path / "env_mcp.yaml"
    config_data = {
        "servers": [
            {
                "name": "test-server",
                "command": "${TEST_CMD}",
                "args": ["server.py"],
                "env": {
                    "API_KEY": "${TEST_API_KEY}",
                    "PORT": "8080"
                }
            }
        ]
    }
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    configs = load_mcp_configs_from_file(str(config_file))

    assert len(configs) == 1
    assert configs[0].name == "test-server"
    assert configs[0].command == "python3"
    assert configs[0].env == {"API_KEY": "secret123", "PORT": "8080"}


def test_load_mcp_configs_missing_required_field(tmp_path):
    """Test handling of missing required 'name' or 'command' fields."""
    config_file = tmp_path / "invalid_mcp.yaml"
    config_data = {
        "servers": [
            {
                "name": "incomplete-server",
                # Missing 'command' field
                "args": ["server.py"]
            }
        ]
    }
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    # Should raise KeyError when accessing missing 'command' field
    with pytest.raises(KeyError, match="'command'"):
        load_mcp_configs_from_file(str(config_file))


def test_load_mcp_configs_none_yaml(tmp_path):
    """Test handling of None/empty YAML file."""
    config_file = tmp_path / "none_mcp.yaml"
    with open(config_file, 'w') as f:
        f.write("")  # Empty file, yaml.safe_load returns None

    configs = load_mcp_configs_from_file(str(config_file))
    assert configs == []

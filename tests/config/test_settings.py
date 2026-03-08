"""Tests for main settings loader."""

import pytest
import yaml
from pathlib import Path
from src.config.settings import load_config


@pytest.fixture
def temp_configs(tmp_path, monkeypatch):
    """Create temporary config files."""
    # Setup env vars
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.test.com")

    # Create main config
    main_config = tmp_path / "config.yaml"
    main_data = {
        "llm": {
            "api_key": "${OPENAI_API_KEY}",
            "base_url": "${OPENAI_BASE_URL}",
            "model": "glm-4-flash"
        },
        "agent": {
            "type": "react",
            "max_iterations": 15
        },
        "mcp_config_file": "mcp_servers.yaml"
    }
    with open(main_config, 'w') as f:
        yaml.dump(main_data, f)

    # Create MCP config
    mcp_config = tmp_path / "mcp_servers.yaml"
    mcp_data = {
        "servers": [
            {
                "name": "test",
                "command": "python",
                "args": ["test.py"]
            }
        ]
    }
    with open(mcp_config, 'w') as f:
        yaml.dump(mcp_data, f)

    return main_config


def test_load_config_full(temp_configs):
    config = load_config(str(temp_configs))

    assert config.llm.api_key == "test_key"
    assert config.llm.base_url == "https://api.test.com"
    assert config.llm.model == "glm-4-flash"
    assert config.agent_type == "react"
    assert config.max_iterations == 15
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "test"


def test_load_config_defaults(tmp_path, monkeypatch):
    """Test default values when agent section is missing."""
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://url")

    main_config = tmp_path / "config.yaml"
    main_data = {
        "llm": {
            "api_key": "${OPENAI_API_KEY}",
            "base_url": "${OPENAI_BASE_URL}",
            "model": "model"
        },
        "mcp_config_file": "mcp.yaml"
    }
    with open(main_config, 'w') as f:
        yaml.dump(main_data, f)

    mcp_config = tmp_path / "mcp.yaml"
    with open(mcp_config, 'w') as f:
        yaml.dump({"servers": []}, f)

    config = load_config(str(main_config))
    assert config.agent_type == "react"
    assert config.max_iterations == 10


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("/nonexistent/config.yaml")

"""Tests for configuration models."""

import pytest
from src.config.models import LLMConfig, MCPServerConfig, AgentConfig


def test_llm_config_creation():
    config = LLMConfig(
        api_key="test_key",
        base_url="https://api.test.com",
        model="test-model"
    )
    assert config.api_key == "test_key"
    assert config.base_url == "https://api.test.com"
    assert config.model == "test-model"


def test_mcp_server_config_defaults():
    config = MCPServerConfig(
        name="test-server",
        command="python"
    )
    assert config.name == "test-server"
    assert config.command == "python"
    assert config.args == []
    assert config.env is None


def test_mcp_server_config_with_args():
    config = MCPServerConfig(
        name="test-server",
        command="python",
        args=["server.py", "--port", "8080"],
        env={"TEST_VAR": "value"}
    )
    assert len(config.args) == 3
    assert config.env == {"TEST_VAR": "value"}


def test_agent_config_defaults():
    llm_config = LLMConfig(
        api_key="test_key",
        base_url="https://api.test.com",
        model="test-model"
    )
    agent_config = AgentConfig(
        llm=llm_config,
        mcp_servers=[]
    )
    assert agent_config.agent_type == "react"
    assert agent_config.max_iterations == 10

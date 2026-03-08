"""Tests for LLM configuration loading."""

import os
import pytest
from src.config.llm_config import load_llm_config


def test_load_llm_config_with_env_vars(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.test.com")

    raw_config = {
        "llm": {
            "api_key": "${OPENAI_API_KEY}",
            "base_url": "${OPENAI_BASE_URL}",
            "model": "glm-4-flash"
        }
    }

    config = load_llm_config(raw_config)
    assert config.api_key == "test_key"
    assert config.base_url == "https://api.test.com"
    assert config.model == "glm-4-flash"


def test_load_llm_config_missing_key():
    raw_config = {
        "llm": {
            "api_key": "test_key",
            "model": "test-model"
        }
    }

    with pytest.raises(KeyError):
        load_llm_config(raw_config)


def test_load_llm_config_plain_values():
    raw_config = {
        "llm": {
            "api_key": "plain_key",
            "base_url": "https://api.plain.com",
            "model": "plain-model"
        }
    }

    config = load_llm_config(raw_config)
    assert config.api_key == "plain_key"
    assert config.base_url == "https://api.plain.com"
    assert config.model == "plain-model"

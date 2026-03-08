"""Tests for environment variable substitution."""

import os
import pytest
from src.config.env_substitution import substitute_env_vars


def test_substitute_single_env_var(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    result = substitute_env_vars("${TEST_VAR}")
    assert result == "test_value"


def test_substitute_missing_env_var_raises_error(monkeypatch):
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
    with pytest.raises(ValueError, match="Environment variable 'NONEXISTENT_VAR' not found"):
        substitute_env_vars("${NONEXISTENT_VAR}")


def test_substitute_in_dict(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    config = {
        "api_key": "${API_KEY}",
        "model": "test-model",
        "timeout": 30
    }
    result = substitute_env_vars(config)
    assert result["api_key"] == "secret123"
    assert result["model"] == "test-model"
    assert result["timeout"] == 30


def test_substitute_in_list(monkeypatch):
    monkeypatch.setenv("VAR1", "value1")
    monkeypatch.setenv("VAR2", "value2")
    config = ["${VAR1}", "${VAR2}", "static"]
    result = substitute_env_vars(config)
    assert result == ["value1", "value2", "static"]


def test_no_substitution_for_plain_string():
    result = substitute_env_vars("plain_string")
    assert result == "plain_string"


def test_no_substitution_for_non_string_types():
    assert substitute_env_vars(123) == 123
    assert substitute_env_vars(True) is True
    assert substitute_env_vars(None) is None

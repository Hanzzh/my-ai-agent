"""Tests for LLM base class."""

import pytest
from src.llm.base import LLMProvider


def test_llm_provider_cannot_be_instantiated():
    """Abstract base class should not be directly instantiable."""
    with pytest.raises(TypeError):
        LLMProvider()


def test_concrete_implementation():
    """Test that concrete implementation works."""

    class ConcreteProvider(LLMProvider):
        def chat(self, messages, **kwargs):
            return "response"

        def get_model_info(self):
            return {"name": "test"}

    provider = ConcreteProvider()
    assert provider.chat([{"role": "user", "content": "test"}]) == "response"
    assert provider.get_model_info() == {"name": "test"}

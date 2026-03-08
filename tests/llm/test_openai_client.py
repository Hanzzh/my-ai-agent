"""Tests for OpenAI-compatible client."""

import pytest
from unittest.mock import Mock, patch
from src.llm.openai_client import OpenAICompatibleProvider


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    return mock_response


def test_openai_provider_initialization():
    """Test OpenAI-compatible provider initialization."""
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://api.test.com",
        model="test-model"
    )

    assert provider.model == "test-model"
    assert provider._api_key == "test-key"
    assert provider._base_url == "https://api.test.com"
    assert provider.client is not None


@patch('src.llm.openai_client.OpenAI')
def test_chat_success(mock_openai_class, mock_openai_response):
    """Test successful chat completion."""
    # Setup mock
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client

    # Create provider and test
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://api.test.com",
        model="test-model"
    )

    messages = [{"role": "user", "content": "Hello"}]
    response = provider.chat(messages, temperature=0.5)

    assert response == "Test response"
    mock_client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=messages,
        temperature=0.5
    )


def test_get_model_info():
    """Test get_model_info returns correct information."""
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://api.test.com",
        model="test-model"
    )

    info = provider.get_model_info()

    assert info == {
        "name": "test-model",
        "base_url": "https://api.test.com"
    }

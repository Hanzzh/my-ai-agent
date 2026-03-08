"""OpenAI-compatible LLM client implementation."""

from typing import List, Dict
import httpx
from openai import OpenAI
from .base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible API client for LLM providers."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """Initialize OpenAI-compatible client."""
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(trust_env=False)
        )
        self.model = model
        self._api_key = api_key
        self._base_url = base_url

    def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Send chat completion request."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    def get_model_info(self) -> Dict:
        """Return model information."""
        return {
            "name": self.model,
            "base_url": self._base_url
        }

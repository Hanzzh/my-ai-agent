"""LLM provider abstract base class."""

from abc import ABC, abstractmethod
from typing import List, Dict


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """
        Send chat messages and return response text.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, etc.)

        Returns:
            Response text from LLM
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """
        Return model information.

        Returns:
            Dict with model name and capabilities
        """
        pass

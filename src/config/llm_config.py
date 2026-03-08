"""LLM configuration processing."""

from .models import LLMConfig
from .env_substitution import substitute_env_vars


def load_llm_config(raw_config: dict) -> LLMConfig:
    """
    Parse and validate LLM configuration from raw dict.

    Args:
        raw_config: Raw configuration dictionary

    Returns:
        Parsed LLMConfig object

    Raises:
        KeyError: If required fields are missing
    """
    llm_data = substitute_env_vars(raw_config['llm'])

    return LLMConfig(
        api_key=llm_data['api_key'],
        base_url=llm_data['base_url'],
        model=llm_data['model']
    )

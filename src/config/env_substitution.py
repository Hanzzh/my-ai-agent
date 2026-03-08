"""Environment variable substitution for configuration."""

import os
import re
from typing import Any


def substitute_env_vars(config: Any) -> Any:
    """
    Recursively substitute ${VAR_NAME} patterns with environment variables.

    Args:
        config: Configuration object (str, dict, list, or primitive)

    Returns:
        Configuration with environment variables substituted

    Raises:
        ValueError: If required environment variable is not found
    """
    if isinstance(config, str):
        # Match ${VAR_NAME} pattern (entire string must be the pattern)
        match = re.match(r'^\$\{(\w+)\}$', config.strip())
        if match:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(f"Environment variable '{var_name}' not found")
            return env_value
        return config
    elif isinstance(config, dict):
        return {k: substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars(item) for item in config]
    return config

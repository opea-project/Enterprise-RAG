# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional


def get_boolean_env_var(var_name, default_value=False):
    """Retrieve the boolean value of an environment variable.

    Args:
    var_name (str): The name of the environment variable to retrieve.
    default_value (bool): The default value to return if the variable
    is not found.

    Returns:
    bool: The value of the environment variable, interpreted as a boolean.
    """
    true_values = {"true", "1", "t", "y", "yes"}
    false_values = {"false", "0", "f", "n", "no"}

    # Retrieve the environment variable's value
    value = os.getenv(var_name, "").lower()

    # Decide the boolean value based on the content of the string
    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        return default_value

def sanitize_env(value: Optional[str]) -> Optional[str]:
    """Remove quotes from a configuration value if present.
    Args:
        value (str): The configuration value to sanitize.
    Returns:
        str: The sanitized configuration value.
    """
    if value is None:
        return None
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    elif value.startswith('\'') and value.endswith('\''):
        value = value[1:-1]
    return value

# ruff: noqa: F401
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from llm_guard.vault import Vault
from llm_guard.input_scanners import (
    Anonymize,
    BanCode,
    BanCompetitors,
    BanSubstrings,
    BanTopics,
    Code,
    Gibberish,
    InvisibleText,
    Language,
    PromptInjection,
    Regex,
    Secrets,
    Sentiment,
    TokenLimit,
    Toxicity
    )

from comps import get_opea_logger
logger = get_opea_logger("opea_llm_guard_input_guardrail_microservice")


class InputScannersConfig:

    def __init__(self, config_dict):
        self._input_scanners_config = {
            **self._get_anonymize_config_from_env(config_dict),
            **self._get_ban_code_config_from_env(config_dict),
            **self._get_ban_competitors_config_from_env(config_dict),
            **self._get_ban_substrings_config_from_env(config_dict),
            **self._get_ban_topics_config_from_env(config_dict),
            **self._get_code_config_from_env(config_dict),
            **self._get_gibberish_config_from_env(config_dict),
            **self._get_invisible_text_config_from_env(config_dict),
            **self._get_language_config_from_env(config_dict),
            **self._get_prompt_injection_config_from_env(config_dict),
            **self._get_regex_config_from_env(config_dict),
            **self._get_secrets_config_from_env(config_dict),
            **self._get_sentiment_config_from_env(config_dict),
            **self._get_token_limit_config_from_env(config_dict),
            **self._get_toxicity_config_from_env(config_dict)
        }

    def _validate_value(self, value): # TODO: add validate per scanner
        """
        Validate and convert the input value.

        Args:
            value (str): The value to be validated and converted.

        Returns:
            bool | int | str: The validated and converted value.
        """
        if value is None:
            return None
        elif value.isdigit():
            return int(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        return value

    def _get_anonymize_config_from_env(self, config_dict):
        """
        Get the Anonymize scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The anonymize scanner configuration.
        """
        return {
            "Anonymize": {
                k.replace("ANONYMIZE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("ANONYMIZE_")
            }
        }

    def _get_ban_code_config_from_env(self, config_dict):
        """
        Get the BanCode scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The BanCode scanner configuration.
        """
        return {
            "BanCode": {
                k.replace("BANCODE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BANCODE_")
            }
        }

    def _get_ban_competitors_config_from_env(self, config_dict):
        """
        Get the BanCompetitors scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The BanCompetitors scanner configuration.
        """
        return {
            "BanCompetitors": {
                k.replace("BANCOMPETITORS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BANCOMPETITORS_")
            }
        }

    def _get_ban_substrings_config_from_env(self, config_dict):
        """
        Get the BanSubstrings scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The BanSubstrings scanner configuration.
        """
        return {
            "BanSubstrings": {
                k.replace("BANSUBSTRINGS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BANSUBSTRINGS_")
            }
        }

    def _get_ban_topics_config_from_env(self, config_dict):
        """
        Get the BanTopics scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The BanTopics scanner configuration.
        """
        return {
            "BanTopics": {
                k.replace("BANTOPICS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BANTOPICS_")
            }
        }

    def _get_code_config_from_env(self, config_dict):
        """
        Get the Code scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Code scanner configuration.
        """
        return {
            "Code": {
                k.replace("CODE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("CODE_")
            }
        }

    def _get_gibberish_config_from_env(self, config_dict):
        """
        Get the Gibberish scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Gibberish scanner configuration.
        """
        return {
            "Gibberish": {
                k.replace("GIBBERISH_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("GIBBERISH_")
            }
        }
    def _get_invisible_text_config_from_env(self, config_dict):
        """
        Get the InvisibleText scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The InvisibleText scanner configuration.
        """
        return {
            "InvisibleText": {
                k.replace("INVISIBLE_TEXT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("INVISIBLE_TEXT_")
            }
        }

    def _get_language_config_from_env(self, config_dict):
        """
        Get the Language scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Language scanner configuration.
        """
        return {
            "Language": {
                k.replace("LANGUAGE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("LANGUAGE_")
            }
        }

    def _get_prompt_injection_config_from_env(self, config_dict):
        """
        Get the PromptInjection scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The PromptInjection scanner configuration.
        """
        return {
            "PromptInjection": {
                k.replace("PROMPTINJECTION_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("PROMPTINJECTION_")
            }
        }

    def _get_regex_config_from_env(self, config_dict):
        """
        Get the Regex scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Regex scanner configuration.
        """
        return {
            "Regex": {
                k.replace("REGEX_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("REGEX_")
            }
        }

    def _get_secrets_config_from_env(self, config_dict):
        """
        Get the Secrets scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Secrets scanner configuration.
        """
        return {
            "Secrets": {
                k.replace("SECRETS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("SECRETS_")
            }
        }

    def _get_sentiment_config_from_env(self, config_dict):
        """
        Get the Secrets scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Sentiment scanner configuration.
        """
        return {
            "Sentiment": {
                k.replace("SENTIMENT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("SENTIMENT_")
            }
        }

    def _get_token_limit_config_from_env(self, config_dict):
        """
        Get the TokenLimit scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The TokenLimit scanner configuration.
        """
        return {
            "TokenLimit": {
                k.replace("TOKENLIMIT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("TOKENLIMIT_")
            }
        }

    def _get_toxicity_config_from_env(self, config_dict):
        """
        Get the Toxicity scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Toxicity scanner configuration.
        """
        return {
            "Toxicity": {
                k.replace("TOXICITY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("TOXICITY_")
                }
        }

    def create_enabled_input_scanners(self):
        """
        Create and return a list of enabled scanners based on the global configuration.

        Returns:
            list: A list of enabled scanner instances.
        """
        enabled_scanners = {k: v for k, v in self._input_scanners_config.items() if v.get("enabled")}
        scanners = []
        for scanner in enabled_scanners:
            try:
                logger.info(f"Creating scanner: {scanner}")
                params = {k: v for k, v in enabled_scanners[scanner].items() if k != "enabled" and k != 'id' and v is not None}
                scanners.append(globals()[scanner](**params)) # TODO: do differently, vulnerable to not validated env
            except Exception as e:
                logger.exception(
                    f"An unexpected error occured during creating output scanner {scanner}: {e}"
                )
                continue
        return scanners

    def changed(self, current_scanners):
        """
        Check if the scanners configuration has changed.

        Args:
            current_scanners (dict): The current scanners configuration.

        Returns:
            bool: True if the configuration has changed, False otherwise.
        """
        del current_scanners['id']
        capitalized_current_scanners = {key.capitalize(): value for key, value in current_scanners.items()}
        if current_scanners != self._input_scanners_config: # TODO: add better comparison, to be tested
            logger.info("Scanners configuration has been changed, re-creating scanners")
            self._input_scanners_config.clear()
            self._input_scanners_config.update(capitalized_current_scanners)
            return True
        return False

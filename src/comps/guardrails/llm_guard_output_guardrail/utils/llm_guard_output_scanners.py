# ruff: noqa: F401
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from llm_guard.vault import Vault
from llm_guard.output_scanners import (
    BanCompetitors,
    BanSubstrings,
    BanTopics,
    Bias,
    Code,
    Deanonymize,
    JSON,
    Language,
    LanguageSame,
    MaliciousURLs,
    NoRefusal,
    NoRefusalLight,
    ReadingTime,
    FactualConsistency,
    Relevance,
    Sensitive,
    URLReachability
    )

from comps import get_opea_logger
logger = get_opea_logger("opea_llm_guard_output_guardrail_microservice")

class OutputScannersConfig:
    def __init__(self, config_dict):
        self._output_scanners_config = {
            **self._get_ban_competitors_config_from_env(config_dict),
            **self._get_ban_substrings_config_from_env(config_dict),
            **self._get_ban_topics_config_from_env(config_dict),
            **self._get_bias_topics_config_from_env(config_dict),
            **self._get_code_config_from_env(config_dict),
            **self._get_deanonymize_config_from_env(config_dict),
            **self._get_json_config_from_env(config_dict),
            **self._get_language_config_from_env(config_dict),
            **self._get_language_same_config_from_env(config_dict),
            **self._get_malicious_urls_config_from_env(config_dict),
            **self._get_no_refusal_config_from_env(config_dict),
            **self._get_no_refusal_light_config_from_env(config_dict),
            **self._get_reading_time_config_from_env(config_dict),
            **self._get_factual_consistency_config_from_env(config_dict),
            **self._get_relevance_config_from_env(config_dict),
            **self._get_sensitive_config_from_env(config_dict),
            **self._get_url_reachability_config_from_env(config_dict)
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

    def _get_bias_topics_config_from_env(self, config_dict):
        """
        Get the Bias scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Bias scanner configuration.
        """
        return {
            "Bias": {
                k.replace("BIAS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BIAS_")
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

    def _get_deanonymize_config_from_env(self, config_dict):
        """
        Get the Deanonymize scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The deanonymize scanner configuration.
        """
        return {
            "Anonymize": {
                k.replace("DEANONYMIZE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("DEANONYMIZE_")
            }
        }

    def _get_json_config_from_env(self, config_dict):
        """
        Get the JSON scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The JSON scanner configuration.
        """
        return {
            "JSON": {
                k.replace("JSON", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("JSON_")
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

    def _get_language_same_config_from_env(self, config_dict):
        """
        Get the LanguageSame scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The LanguageSame scanner configuration.
        """
        return {
            "LanguageSame": {
                k.replace("LANGUAGESAME_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("LANGUAGESAME_")
            }
        }

    def _get_malicious_urls_config_from_env(self, config_dict):
        """
        Get the MaliciousURLs scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The MaliciousURLs scanner configuration.
        """
        return {
            "MaliciousURLs": {
                k.replace("MALICIOUSURLS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("MALICIOUSURLS_")
            }
        }

    def _get_no_refusal_config_from_env(self, config_dict):
        """
        Get the NoRefusal scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The NoRefusal scanner configuration.
        """
        return {
            "NoRefusal": {
                k.replace("NOREFUSAL_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("NOREFUSAL_")
            }
        }

    def _get_no_refusal_light_config_from_env(self, config_dict):
        """
        Get the NoRefusalLight scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The NoRefusalLight scanner configuration.
        """
        return {
            "NoRefusalLight": {
                k.replace("NOREFUSALLIGHT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("NOREFUSALLIGHT_")
            }
        }

    def _get_reading_time_config_from_env(self, config_dict):
        """
        Get the ReadingTime scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The ReadingTime scanner configuration.
        """
        return {
            "ReadingTime": {
                k.replace("READINGTIME_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("READINGTIME_")
            }
        }

    def _get_factual_consistency_config_from_env(self, config_dict):
        """
        Get the FactualConsitency scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The FactualConsitency scanner configuration.
        """
        return {
            "FactualConsitency": {
                k.replace("FACTUALCONSISTENCY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("FACTUALCONSISTENCY_")
            }
        }

    def _get_relevance_config_from_env(self, config_dict):
        """
        Get the Relevance scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Relevance scanner configuration.
        """
        return {
            "Relevance": {
                k.replace("RELEVANCE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("RELEVANCE_")
            }
        }

    def _get_sensitive_config_from_env(self, config_dict):
        """
        Get the Sensitive scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Sensitive scanner configuration.
        """
        return {
            "Sensitive": {
                k.replace("SENSITIVE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("SENSITIVE_")
            }
        }

    def _get_url_reachability_config_from_env(self, config_dict):
        """
        Get the URLReachability scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The URLReachability scanner configuration.
        """
        return {
            "URLReachability": {
                k.replace("URLREACHABILITY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("URLREACHABILITY_")
            }
        }

    def create_enabled_output_scanners(self):
        """
        Create and return a list of enabled scanners based on the global configuration.

        Returns:
            list: A list of enabled scanner instances.
        """
        enabled_scanners = {k: v for k, v in self._output_scanners_config.items() if v.get("enabled")}
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
        Check if the output scanners configuration has changed.

        Args:
            current_scanners (dict): The current scanners configuration.

        Returns:
            bool: True if the configuration has changed, False otherwise.
        """
        del current_scanners['id']
        capitalized_current_scanners = {key.capitalize(): value for key, value in current_scanners.items()}
        if current_scanners != self._output_scanners_config: # TODO: add better comparison, to be tested
            logger.info("Scanners configuration has been changed, re-creating scanners")
            self._output_scanners_config.clear()
            self._output_scanners_config.update(capitalized_current_scanners)
            return True
        return False

# ruff: noqa: F401
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from llm_guard.vault import Vault
from llm_guard.output_scanners import (
    BanTopics,
    Bias,
    Code,
    Deanonymize,
    JSON,
    MaliciousURLs,
    NoRefusal,
    NoRefusalLight,
    ReadingTime,
    FactualConsistency,
    Relevance,
    Sensitive,
    Sentiment,
    Toxicity,
    URLReachability
)

# import models definition
from llm_guard.input_scanners.ban_topics import (  #input, becasue the same scanner to input and output
    MODEL_DEBERTA_LARGE_V2 as BANTOPICS_MODEL_DEBERTA_LARGE_V2,
    MODEL_DEBERTA_BASE_V2 as BANTOPICS_MODEL_DEBERTA_BASE_V2,
    MODEL_BGE_M3_V2 as BANTOPICS_MODEL_BGE_M3_V2,
    MODEL_ROBERTA_LARGE_C_V2 as BANTOPICS_MODEL_ROBERTA_LARGE_C_V2,
    MODEL_ROBERTA_BASE_C_V2 as BANTOPICS_MODEL_ROBERTA_BASE_C_V2
)

from llm_guard.output_scanners.bias import (
    DEFAULT_MODEL as BIAS_DEFAULT_MODEL
)

from llm_guard.input_scanners.code import (
    DEFAULT_MODEL as CODE_DEFAULT_MODEL
)

from llm_guard.output_scanners.malicious_urls import (
    DEFAULT_MODEL as MALICIOUS_URLS_DEFAULT_MODEL
)

from llm_guard.output_scanners.no_refusal import (
    DEFAULT_MODEL as NO_REFUSAL_DEFAULT_MODEL
)

from llm_guard.output_scanners.relevance import (
    MODEL_EN_BGE_BASE as RELEVANCE_MODEL_EN_BGE_BASE,
    MODEL_EN_BGE_LARGE as RELEVANCE_MODEL_EN_BGE_LARGE,
    MODEL_EN_BGE_SMALL as RELEVANCE_MODEL_EN_BGE_SMALL
)

from llm_guard.input_scanners.toxicity import (
    DEFAULT_MODEL as TOXICITY_DEFAULT_MODEL
)

ENABLED_SCANNERS = [
    'ban_substrings',
    'ban_topics',
    'bias',
    'code',
    'deanonymize',
    'json_scanner',
    'malicious_urls',
    'no_refusal',
    'no_refusal_light',
    'reading_time',
    'factual_consistency',
    'regex',
    'relevance',
    'sensitive',
    'sentiment',
    'toxicity',
    'url_reachability'
]

from comps.guardrails.utils.scanners import OPEABanSubstrings, OPEARegexScanner
from comps import get_opea_logger, sanitize_env
logger = get_opea_logger("opea_llm_guard_output_guardrail_microservice")

class OutputScannersConfig:
    def __init__(self, config_dict):
        self._output_scanners_config = {
            **self._get_ban_substrings_config_from_env(config_dict),
            **self._get_ban_topics_config_from_env(config_dict),
            **self._get_bias_config_from_env(config_dict),
            **self._get_code_config_from_env(config_dict),
            **self._get_deanonymize_config_from_env(config_dict),
            **self._get_json_scanner_config_from_env(config_dict),
            **self._get_malicious_urls_config_from_env(config_dict),
            **self._get_no_refusal_config_from_env(config_dict),
            **self._get_no_refusal_light_config_from_env(config_dict),
            **self._get_reading_time_config_from_env(config_dict),
            **self._get_factual_consistency_config_from_env(config_dict),
            **self._get_regex_config_from_env(config_dict),
            **self._get_relevance_config_from_env(config_dict),
            **self._get_sensitive_config_from_env(config_dict),
            **self._get_sentiment_config_from_env(config_dict),
            **self._get_toxicity_config_from_env(config_dict),
            **self._get_url_reachability_config_from_env(config_dict)
        }
        self.vault = None

#### METHODS FOR VALIDATING CONFIGS

    def _validate_value(self, value):
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
            return float(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        return value

    def _get_ban_substrings_config_from_env(self, config_dict):
        """
        Get the BanSubstrings scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The BanSubstrings scanner configuration.
        """
        return {
            "ban_substrings": {
                k.replace("BAN_SUBSTRINGS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BAN_SUBSTRINGS_")
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
            "ban_topics": {
                k.replace("BAN_TOPICS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BAN_TOPICS_")
            }
        }

    def _get_bias_config_from_env(self, config_dict):
        """
        Get the Bias scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Bias scanner configuration.
        """
        return {
            "bias": {
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
            "code": {
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
            "deanonymize": {
                k.replace("DEANONYMIZE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("DEANONYMIZE_")
            }
        }

    def _get_json_scanner_config_from_env(self, config_dict):
        """
        Get the JSON scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The JSON scanner configuration.
        """
        return {
            "json_scanner": {
                k.replace("JSON_SCANNER_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("JSON_SCANNER_")
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
            "malicious_urls": {
                k.replace("MALICIOUS_URLS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("MALICIOUS_URLS_")
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
            "no_refusal": {
                k.replace("NO_REFUSAL_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("NO_REFUSAL_")
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
            "no_refusal_light": {
                k.replace("NO_REFUSAL_LIGHT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("NO_REFUSAL_LIGHT_")
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
            "reading_time": {
                k.replace("READING_TIME_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("READING_TIME_")
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
            "factual_consistency": {
                k.replace("FACTUAL_CONSISTENCY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("FACTUAL_CONSISTENCY_")
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
            "regex": {
                k.replace("REGEX_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("REGEX_")
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
            "relevance": {
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
            "sensitive": {
                k.replace("SENSITIVE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("SENSITIVE_")
            }
        }

    def _get_sentiment_config_from_env(self, config_dict):
        """
        Get the Sentiment scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Sentiment scanner configuration.
        """
        return {
            "sentiment": {
                k.replace("SENTIMENT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("SENTIMENT_")
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
            "toxicity": {
                k.replace("TOXICITY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("TOXICITY_")
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
            "url_reachability": {
                k.replace("URL_REACHABILITY_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("URL_REACHABILITY_")
            }
        }

#### METHODS FOR CREATING SCANNERS
    def _create_ban_substrings_scanner(self, scanner_config):
        available_match_types = ['str', 'word']
        ban_substrings_params = {}

        substrings = scanner_config.get('substrings', None)
        match_type = scanner_config.get('match_type', None)
        case_sensitive = scanner_config.get('case_sensitive', None)
        redact = scanner_config.get('redact', None)
        contains_all = scanner_config.get('contains_all', None)

        if isinstance(substrings, str):
            substrings = sanitize_env(substrings)

        if substrings:
            if isinstance(substrings, str):
                artifacts = set([',', '', '.'])
                ban_substrings_params['substrings'] = list(set(substrings.split(',')) - artifacts)
            elif substrings and isinstance(substrings, list):
                ban_substrings_params['substrings'] = substrings
            else:
                logger.error("Provided type is not valid for BanSubstrings scanner")
                raise ValueError("Provided type is not valid for BanSubstrings scanner")
        elif isinstance(substrings, str) and substrings.strip() == "":
            ban_substrings_params['substrings'] = []
        else:
            logger.error("Substrings list is required for BanSubstrings scanner")
            raise TypeError("Substrings list is required for BanSubstrings scanner")
        if match_type is not None and match_type in available_match_types:
            ban_substrings_params['match_type'] = match_type
        if case_sensitive is not None:
            ban_substrings_params['case_sensitive'] = case_sensitive
        if redact is not None:
            ban_substrings_params['redact'] = redact
        if contains_all is not None:
            ban_substrings_params['contains_all'] = contains_all
        logger.info(f"Creating BanSubstrings scanner with params: {ban_substrings_params}")
        return OPEABanSubstrings(**ban_substrings_params)

    def _create_ban_topics_scanner(self, scanner_config):
        enabled_models = {
            'MODEL_DEBERTA_LARGE_V2': BANTOPICS_MODEL_DEBERTA_LARGE_V2,
            'MODEL_DEBERTA_BASE_V2': BANTOPICS_MODEL_DEBERTA_BASE_V2,
            'MODEL_BGE_M3_V2': BANTOPICS_MODEL_BGE_M3_V2,
            'MODEL_ROBERTA_LARGE_C_V2': BANTOPICS_MODEL_ROBERTA_LARGE_C_V2,
            'MODEL_ROBERTA_BASE_C_V2': BANTOPICS_MODEL_ROBERTA_BASE_C_V2
        }
        ban_topics_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        topics = scanner_config.get('topics', None)
        threshold = scanner_config.get('threshold', None)
        model_name = scanner_config.get('model', None)

        if isinstance(topics, str):
            topics = sanitize_env(topics)

        if topics:
            if isinstance(topics, str):
                artifacts = set([',', '', '.'])
                ban_topics_params['topics'] = list(set(topics.split(',')) - artifacts)
            elif isinstance(topics, list):
                ban_topics_params['topics'] = topics
            else:
                logger.error("Provided type is not valid for BanTopics scanner")
                raise ValueError("Provided type is not valid for BanTopics scanner")
        else:
            logger.error("Topics list is required for BanTopics scanner")
            raise TypeError("Topics list is required for BanTopics scanner")
        if threshold is not None:
            try:
                ban_topics_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for BanTopics scanner. Please provide a float value. Provided threshold: {threshold}") from e
        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for BanTopics scanner: {model_name}")
                ban_topics_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for BanTopics scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        logger.info(f"Creating BanTopics scanner with params: {ban_topics_params}")
        return BanTopics(**ban_topics_params)

    def _create_bias_scanner(self, scanner_config):
        available_match_types = ['str', 'word']
        enabled_models = {'DEFAULT_MODEL': BIAS_DEFAULT_MODEL}
        bias_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)
        model_name = scanner_config.get('model', None)

        if threshold is not None:
            try:
                bias_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Bias scanner. Please provide a float value. Provided threshold: {threshold}") from e
        if match_type is not None and match_type in available_match_types:
            bias_params['match_type'] = match_type
        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for Bias scanner: {model_name}")
                bias_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for Bias scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)

        logger.info(f"Creating Bias scanner with params: {bias_params}")
        return Bias(**bias_params)

    def _create_code_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': CODE_DEFAULT_MODEL}
        code_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        languages = scanner_config.get('languages', None)
        model_name = scanner_config.get('model', None)
        is_blocked = scanner_config.get('is_blocked', None)
        threshold = scanner_config.get('threshold', None)

        if isinstance(languages, str):
            languages = sanitize_env(languages)

        if languages:
            if isinstance(languages, str):
                artifacts = set([',', '', '.'])
                code_params['languages'] = list(set(languages.split(',')) - artifacts)
            elif isinstance(languages, list):
                code_params['languages'] = languages
            else:
                logger.error("Provided type is not valid for Code scanner")
                raise ValueError("Provided type is not valid for Code scanner")
        else:
            logger.error("Languages list is required for Code scanner")
            raise TypeError("Languages list is required for Code scanner")
        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for Code scanner: {model_name}")
                code_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for Code scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if is_blocked is not None:
            code_params['is_blocked'] = is_blocked
        if threshold is not None:
            try:
                code_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Code scanner. Please provide a float value. Provided threshold: {threshold}") from e
        logger.info(f"Creating Code scanner with params: {code_params}")
        return Code(**code_params)

    def _create_deanonymize_scanner(self, scanner_config, vault):
        if not vault:
            raise Exception("Vault is required for Deanonymize scanner")
        deanonymize_params = {'vault': vault}

        matching_strategy = scanner_config.get('matching_strategy', None)
        if matching_strategy is not None:
            deanonymize_params['matching_strategy'] = matching_strategy

        logger.info(f"Creating Deanonymize scanner with params: {deanonymize_params}")
        return Deanonymize(**deanonymize_params)

    def _create_json_scanner(self, scanner_config):
        json_scanner_params = {}

        required_elements = scanner_config.get('required_elements', None)
        repair = scanner_config.get('repair', None)

        if required_elements is not None:
            try:
                json_scanner_params['required_elements'] = int(required_elements)
            except ValueError as e:
                raise ValueError(f"Required elements value is not valid for JSON scanner. Please provide an integer value. Provided required elements: {required_elements}") from e
        if repair is not None:
            json_scanner_params['repair'] = repair

        logger.info(f"Creating JSON scanner with params: {json_scanner_params}")
        return JSON(**json_scanner_params)

    def _create_malicious_urls_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': MALICIOUS_URLS_DEFAULT_MODEL}
        malicious_urls_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        threshold = scanner_config.get('threshold', None)
        model_name = scanner_config.get('model', None)

        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for MaliciousURLs scanner: {model_name}")
                malicious_urls_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for MaliciousURLs scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if threshold is not None:
            try:
                malicious_urls_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for MaliciousURLs scanner. Please provide a float value. Provided threshold: {threshold}") from e

        logger.info(f"Creating MaliciousURLs scanner with params: {malicious_urls_params}")
        return MaliciousURLs(**malicious_urls_params)

    def _create_no_refusal_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': NO_REFUSAL_DEFAULT_MODEL}
        enabled_match_types = ['sentence', 'full']
        no_refusal_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        threshold = scanner_config.get('threshold', None)
        model_name = scanner_config.get('model', None)
        match_type = scanner_config.get('match_type', None)

        if threshold is not None:
            try:
                no_refusal_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for NoRefusal scanner. Please provide a float value. Provided threshold: {threshold}") from e
        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for NoRefusal scanner: {model_name}")
                no_refusal_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for NoRefusal scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if match_type is not None and match_type in enabled_match_types:
            no_refusal_params['match_type'] = match_type

        logger.info(f"Creating NoRefusal scanner with params: {no_refusal_params}")
        return NoRefusal(**no_refusal_params)

    def _create_no_refusal_light_scanner(self):
        logger.info("Creating NoRefusalLight scanner.")
        return NoRefusalLight()

    def _create_reading_time_scanner(self, scanner_config):
        reading_time_params = {}

        max_time = scanner_config.get('max_time', None)
        truncate = scanner_config.get('truncate', None)

        if max_time is not None:
            try:
                reading_time_params['max_time'] = float(max_time)
            except ValueError as e:
                raise ValueError(f"Max time value is not valid for ReadingTime scanner. Please provide a float value. Provided max time: {max_time}") from e
        else:
            logger.error("Max time is required for ReadingTime scanner")
            raise TypeError("Max time is required for ReadingTime scanner")
        if truncate is not None:
            reading_time_params['truncate'] = truncate

        logger.info(f"Creating ReadingTime scanner with params: {reading_time_params}")
        return ReadingTime(**reading_time_params)

    def _create_factual_consistency_scanner(self, scanner_config):
        enabled_models = {"DEFAULT_MODEL": BANTOPICS_MODEL_DEBERTA_BASE_V2} # BanTopics model is used as deault in FactualConsistency
        factual_consistency_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        model_name = scanner_config.get('model_name', None)
        minimum_score = scanner_config.get('minimum_score', None)

        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for NoRefusal scanner: {model_name}")
                factual_consistency_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for NoRefusal scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if minimum_score is not None:
            try:
                factual_consistency_params['minimum_score'] = float(minimum_score)
            except ValueError as e:
                raise ValueError(f"Minimum score value is not valid for FactualConsistency scanner. Please provide a float value. Provided minimum score: {minimum_score}") from e

        logger.info(f"Creating FactualConsistency scanner with params: {factual_consistency_params}")
        return FactualConsistency(**factual_consistency_params)

    def _create_regex_scanner(self, scanner_config):
        enabled_match_types = ['search', 'fullmatch']
        regex_params = {}

        patterns = scanner_config.get('patterns', None)
        is_blocked = scanner_config.get('is_blocked', None)
        match_type = scanner_config.get('match_type', None)
        redact = scanner_config.get('redact', None)

        if isinstance(patterns, str):
            patterns = sanitize_env(patterns)

        if patterns:
            if isinstance(patterns, str):
                artifacts = set([',', '', '.'])
                regex_params['patterns'] = list(set(patterns.split(',')) - artifacts)
            elif isinstance(patterns, list):
                regex_params['patterns'] = patterns
            else:
                logger.error("Provided type is not valid for Regex scanner")
                raise ValueError("Provided type is not valid for Regex scanner")
        else:
            logger.error("Patterns list is required for Regex scanner")
            raise TypeError("Patterns list is required for Regex scanner")
        if is_blocked is not None:
            regex_params['is_blocked'] = is_blocked
        if match_type is not None and match_type in enabled_match_types:
            regex_params['match_type'] = match_type
        if redact is not None:
            regex_params['redact'] = redact

        logger.info(f"Creating Regex scanner with params: {regex_params}")
        return OPEARegexScanner(**regex_params)

    def _create_relevance_scanner(self, scanner_config):
        enabled_models = {'MODEL_EN_BGE_BASE': RELEVANCE_MODEL_EN_BGE_BASE,
                          'MODEL_EN_BGE_LARGE': RELEVANCE_MODEL_EN_BGE_LARGE,
                          'MODEL_EN_BGE_SMALL': RELEVANCE_MODEL_EN_BGE_SMALL}
        relevance_params = {'use_onnx': scanner_config.get('use_onnx', False)} # TODO: onnx off, because of bug on LLM Guard side

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)

        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for Relevance scanner: {model_name}")
                relevance_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for Relevance scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if threshold is not None:
            try:
                relevance_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Relevance scanner. Please provide a float value. Provided threshold: {threshold}") from e

        logger.info(f"Creating Relevance scanner with params: {relevance_params}")
        return Relevance(**relevance_params)

    def _create_sensitive_scanner(self, scanner_config):
        sensitive_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        entity_types = scanner_config.get('entity_types', None)
        regex_patterns = scanner_config.get('regex_patterns', None)
        redact = scanner_config.get('redact', None)
        recognizer_conf = scanner_config.get('recognizer_conf', None)
        threshold = scanner_config.get('threshold', None)

        if entity_types is not None:
            if isinstance(entity_types, str):
                entity_types = sanitize_env(entity_types)

            if entity_types:
                if isinstance(entity_types, str):
                    artifacts = set([',', '', '.'])
                    sensitive_params['entity_types'] = list(set(entity_types.split(',')) - artifacts)
                elif isinstance(entity_types, list):
                    sensitive_params['entity_types'] = entity_types
                else:
                    logger.error("Provided type is not valid for Sensitive scanner")
                    raise ValueError("Provided type is not valid for Sensitive scanner")

        if regex_patterns is not None:
            sensitive_params['regex_patterns'] = regex_patterns
        if redact is not None:
            sensitive_params['redact'] = redact
        if recognizer_conf is not None:
            sensitive_params['recognizer_conf'] = recognizer_conf
        if threshold is not None:
            try:
                sensitive_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Sensitive scanner. Please provide a float value. Provided threshold: {threshold}") from e

        logger.info(f"Creating Sensitive scanner with params: {sensitive_params}")
        return Sensitive(**sensitive_params)

    def _create_sentiment_scanner(self, scanner_config):
        enabled_lexicons = ["vader_lexicon"]
        sentiment_params = {}

        threshold = scanner_config.get('threshold', None)
        lexicon = scanner_config.get('lexicon', None)

        if threshold is not None:
            try:
                sentiment_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Sentiment scanner. Please provide a float value. Provided threshold: {threshold}") from e
        if lexicon is not None and lexicon in enabled_lexicons:
            sentiment_params['lexicon'] = lexicon

        logger.info(f"Creating Sentiment scanner with params: {sentiment_params}")
        return Sentiment(**sentiment_params)

    def _create_toxicity_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': TOXICITY_DEFAULT_MODEL}
        enabled_match_types = ['sentence', 'full']
        toxicity_params = {'use_onnx': scanner_config.get('use_onnx', False)}

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)

        if match_type == "sentence":
            import nltk
            nltk.download('punkt_tab')


        if model_name is not None:
            if model_name in enabled_models:
                logger.info(f"Using selected model for Toxicity scanner: {model_name}")
                toxicity_params['model'] = enabled_models[model_name]
            else:
                err_msg = f"Model name is not valid for Toxicity scanner. Please provide a valid model name. Provided model: {model_name}. Enabled models: {list(enabled_models.keys())}"
                logger.error(err_msg)
                raise ValueError(err_msg)
        if threshold is not None:
            try:
                toxicity_params['threshold'] = float(threshold)
            except ValueError as e:
                raise ValueError(f"Threshold value is not valid for Toxicity scanner. Please provide a float value. Provided threshold: {threshold}") from e
        if match_type is not None and match_type in enabled_match_types:
            toxicity_params['match_type'] = match_type

        logger.info(f"Creating Toxicity scanner with params: {toxicity_params}")
        return Toxicity(**toxicity_params)

    def _create_url_reachability_scanner(self, scanner_config):
        url_reachability_params = {}

        success_status_codes = scanner_config.get('success_status_codes', None)
        timeout = scanner_config.get('timeout', None)

        if success_status_codes is not None:
            if isinstance(success_status_codes, str):
                artifacts = set([',', '', '.'])
                url_reachability_params['success_status_codes'] = list(set(success_status_codes.split(',')) - artifacts)
            elif isinstance(success_status_codes, list):
                url_reachability_params['success_status_codes'] = success_status_codes
            else:
                logger.error("Provided type is not valid for Url Reachability scanner")
                raise ValueError("Provided type is not valid for Url Reachability scanner")
        if timeout is not None:
            try:
                url_reachability_params['timeout'] = int(timeout)
            except ValueError as e:
                raise ValueError(f"Timeout value is not valid for URL Reachability scanner. Please provide an integer value. Provided timeout: {timeout}") from e

        logger.info(f"Creating URLReachability scanner with params: {url_reachability_params}")
        return URLReachability(**url_reachability_params)

    def _create_output_scanner(self, scanner_name, scanner_config, vault=None):
        if scanner_name not in ENABLED_SCANNERS:
            logger.error(f"Scanner {scanner_name} is not supported")
            raise Exception(f"Scanner {scanner_name} is not supported. Enabled scanners are: {ENABLED_SCANNERS}")
        if scanner_name == "ban_substrings":
            return self._create_ban_substrings_scanner(scanner_config)
        elif scanner_name == "ban_topics":
            return self._create_ban_topics_scanner(scanner_config)
        elif scanner_name == "bias":
            return self._create_bias_scanner(scanner_config)
        elif scanner_name == "code":
            return self._create_code_scanner(scanner_config)
        elif scanner_name == "deanonymize":
            return self._create_deanonymize_scanner(scanner_config, vault)
        elif scanner_name == "json_scanner":
            return self._create_json_scanner(scanner_config)
        elif scanner_name == "malicious_urls":
            return self._create_malicious_urls_scanner(scanner_config)
        elif scanner_name == "no_refusal":
            return self._create_no_refusal_scanner(scanner_config)
        elif scanner_name == "no_refusal_light":
            return self._create_no_refusal_light_scanner()
        elif scanner_name == "reading_time":
            return self._create_reading_time_scanner(scanner_config)
        elif scanner_name == "factual_consistency":
            return self._create_factual_consistency_scanner(scanner_config)
        elif scanner_name == "regex":
            return self._create_regex_scanner(scanner_config)
        elif scanner_name == "relevance":
            return self._create_relevance_scanner(scanner_config)
        elif scanner_name == "sensitive":
            return self._create_sensitive_scanner(scanner_config)
        elif scanner_name == "sentiment":
            return self._create_sentiment_scanner(scanner_config)
        elif scanner_name == "toxicity":
            return self._create_toxicity_scanner(scanner_config)
        elif scanner_name == "url_reachability":
            return self._create_url_reachability_scanner(scanner_config)
        return None

    def create_enabled_output_scanners(self):
        """
        Create and return a list of enabled scanners based on the global configuration.

        Returns:
            list: A list of enabled scanner instances.
        """
        enabled_scanners_names_and_configs = {k: v for k, v in self._output_scanners_config.items() if isinstance(v, dict) and v.get("enabled")}
        enabled_scanners_objects = []

        err_msgs = {} # list for all erronous scanners
        only_validation_errors = True
        for scanner_name, scanner_config in enabled_scanners_names_and_configs.items():
            try:
                logger.info(f"Attempting to create scanner: {scanner_name}")
                scanner_object = self._create_output_scanner(scanner_name, scanner_config, vault=self.vault)
                enabled_scanners_objects.append(scanner_object)
            except ValueError as e:
                err_msg = f"A ValueError occured during creating output scanner {scanner_name}: {e}"
                logger.error(err_msg)
                err_msgs[scanner_name] = err_msg
                self._output_scanners_config[scanner_name]["enabled"] = False
                continue
            except TypeError as e:
                err_msg = f"A TypeError occured during creating output scanner {scanner_name}: {e}"
                logger.error(err_msg)
                err_msgs[scanner_name] = err_msg
                self._output_scanners_config[scanner_name]["enabled"] = False
                continue
            except Exception as e:
                err_msg = f"An unexpected error occured during creating output scanner {scanner_name}: {e}"
                logger.error(err_msg)
                err_msgs[scanner_name] = err_msg
                self._output_scanners_config[scanner_name]["enabled"] = False
                only_validation_errors = False
                continue

        if err_msgs:
            if only_validation_errors:
                raise ValueError(f"Some scanners failed to be created due to validation errors. The details: {err_msgs}")
            else:
                raise Exception(f"Some scanners failed to be created due to validation or unexpected errors. The details: {err_msgs}")

        return [s for s in enabled_scanners_objects if s is not None]

    def changed(self, new_scanners_config):
        """
        Check if the scanners configuration has changed.

        Args:
            new_scanners_config (dict): The current scanners configuration.

        Returns:
            bool: True if the configuration has changed, False otherwise.
        """
        del new_scanners_config['id']
        newly_enabled_scanners = {k: {in_k: in_v for in_k, in_v in v.items() if in_k != 'id'} for k, v in new_scanners_config.items() if isinstance(v, dict) and v.get("enabled")}
        previously_enabled_scanners = {k: v for k, v in self._output_scanners_config.items() if isinstance(v, dict) and v.get("enabled")}
        if newly_enabled_scanners == previously_enabled_scanners: # if the enabled scanners are the same we do nothing
            logger.info("No changes in list for enabled scanners. Checking configuration changes...")
            return False
        else:
            logger.warning("Sanners configuration has been changed, re-creating scanners")
            self._output_scanners_config.clear()
            stripped_new_scanners_config = {k: {in_k: in_v for in_k, in_v in v.items() if in_k != 'id'} for k, v in new_scanners_config.items() if isinstance(v, dict)}
            self._output_scanners_config.update(stripped_new_scanners_config)
            return True

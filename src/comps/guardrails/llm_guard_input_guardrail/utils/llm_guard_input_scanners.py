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

# import models definition
from llm_guard.input_scanners.ban_code import (
    MODEL_SM as BANCODE_MODEL_SM,
    MODEL_TINY as BANCODE_MODEL_TINY
)

from llm_guard.input_scanners.ban_competitors import (
    MODEL_V1 as BANCOMPETITORS_MODEL_V1
)

from llm_guard.input_scanners.ban_topics import (
    MODEL_DEBERTA_LARGE_V2 as BANTOPICS_MODEL_DEBERTA_LARGE_V2,
    MODEL_DEBERTA_BASE_V2 as BANTOPICS_MODEL_DEBERTA_BASE_V2,
    MODEL_BGE_M3_V2 as BANTOPICS_MODEL_BGE_M3_V2,
    MODEL_ROBERTA_LARGE_C_V2 as BANTOPICS_MODEL_ROBERTA_LARGE_C_V2,
    MODEL_ROBERTA_BASE_C_V2 as BANTOPICS_MODEL_ROBERTA_BASE_C_V2
)

from llm_guard.input_scanners.code import (
    DEFAULT_MODEL as CODE_DEFAULT_MODEL
)

from llm_guard.input_scanners.gibberish import (
    DEFAULT_MODEL as GIBBERISH_DEFAULT_MODEL,
) 

from llm_guard.input_scanners.language import (
    DEFAULT_MODEL as LANGUAGE_DEFAULT_MODEL,
)

from llm_guard.input_scanners.prompt_injection import (
    V1_MODEL as PROMPTINJECTION_V1_MODEL,
    V2_MODEL as PROMPTINJECTION_V2_MODEL,
    V2_SMALL_MODEL as PROMPTINJECTION_V2_SMALL_MODEL,
)

from llm_guard.input_scanners.toxicity import (
    DEFAULT_MODEL as TOXICITY_DEFAULT_MODEL
)

ENABLED_SCANNERS = [
    'anonymize',
    'ban_code',
    'ban_competitors',
    'ban_substrings',
    'ban_topics',
    'code',
    'gibberish',
    'invisible_text',
    'language',
    'prompt_injection',
    'regex',
    'secrets',
    'sentiment',
    'token_limit',
    'toxicity'
]

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

    def _get_anonymize_config_from_env(self, config_dict):
        """
        Get the Anonymize scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The anonymize scanner configuration.
        """
        return {
            "anonymize": {
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
            "ban_code": {
                k.replace("BAN_CODE_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BAN_CODE_")
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
            "ban_competitors": {
                k.replace("BAN_COMPETITORS_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("BAN_COMPETITORS_")
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

    def _get_gibberish_config_from_env(self, config_dict):
        """
        Get the Gibberish scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Gibberish scanner configuration.
        """
        return {
            "gibberish": {
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
            "invisible_text": {
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
            "language": {
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
            "prompt_injection": {
                k.replace("PROMPT_INJECTION_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("PROMPT_INJECTION_")
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

    def _get_secrets_config_from_env(self, config_dict):
        """
        Get the Secrets scanner configuration from the environment.

        Args:
            config_dict (dict): The configuration dictionary.

        Returns:
            dict: The Secrets scanner configuration.
        """
        return {
            "secrets": {
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
            "sentiment": {
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
            "token_limit": {
                k.replace("TOKEN_LIMIT_", "").lower(): self._validate_value(v)
                for k, v in config_dict.items() if k.startswith("TOKEN_LIMIT_")
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

#### METHODS FOR CREATING SCANNERS

    def _create_anonymize_scanner(self, scanner_config):
        vault = Vault()
        anonymize_params = {'vault': vault, 'use_onnx': scanner_config.get('use_onnx', True)}
        hidden_names = scanner_config.get('hidden_names', None)
        allowed_names = scanner_config.get('allowed_names', None)
        entity_types = scanner_config.get('entity_types', None)
        preamble = scanner_config.get('preamble', None)
        regex_patters = scanner_config.get('regex_patterns', None)
        use_faker = scanner_config.get('use_faker', None)
        recognizer_conf = scanner_config.get('recognizer_conf', None)
        threshold = scanner_config.get('threshold', None)
        language = scanner_config.get('language', None)

        if hidden_names is not None:
            if isinstance(hidden_names, str):
                artifacts = set([',', '', '.'])
                anonymize_params['hidden_names'] = list(set(hidden_names.split(',')) - artifacts)
            elif isinstance(hidden_names, list):
                anonymize_params['hidden_names'] = hidden_names
            else:
                logger.error("Provided type is not valid for Anonymize scanner")
                raise ValueError("Provided type is not valid for Anonymize scanner")
        if allowed_names is not None:
            if isinstance(allowed_names, str):
                artifacts = set([',', '', '.'])
                anonymize_params['allowed_names'] = list(set(allowed_names.split(',')) - artifacts)
            elif isinstance(hidden_names, list):
                anonymize_params['allowed_names'] = allowed_names
            else:
                logger.error("Provided type is not valid for Anonymize scanner")
                raise ValueError("Provided type is not valid for Anonymize scanner")
        if entity_types is not None:
            if isinstance(entity_types, str):
                artifacts = set([',', '', '.'])
                anonymize_params['entity_types'] = list(set(entity_types.split(',')) - artifacts)
            elif isinstance(hidden_names, list):
                anonymize_params['entity_types'] = entity_types
            else:
                logger.error("Provided type is not valid for Anonymize scanner")
                raise ValueError("Provided type is not valid for Anonymize scanner")
        if preamble is not None:
            anonymize_params['preamble'] = preamble
        if regex_patters is not None:
            if isinstance(regex_patters, str):
                artifacts = set([',', '', '.'])
                anonymize_params['regex_patterns'] = list(set(regex_patters.split(',')) - artifacts)
            elif isinstance(hidden_names, list):
                anonymize_params['regex_patterns'] = regex_patters
            else:
                logger.error("Provided type is not valid for Anonymize scanner")
                raise ValueError("Provided type is not valid for Anonymize scanner")
        if use_faker is not None:
            anonymize_params['use_faker'] = use_faker
        if recognizer_conf is not None:
            anonymize_params['recognizer_conf'] = recognizer_conf
        if threshold is not None:
            anonymize_params['threshold'] = threshold
        if language is not None:
            anonymize_params['language'] = language
        logger.info(f"Creating Anonymize scanner with params: {anonymize_params}")
        return Anonymize(**anonymize_params)

    def _create_ban_code_scanner(self, scanner_config):
        enabled_models = {'MODEL_SM': BANCODE_MODEL_SM, 'MODEL_TINY': BANCODE_MODEL_TINY}
        bancode_params = {'use_onnx': scanner_config.get('use_onnx', True)} # by default we want to use onnx

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)

        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for BanCode scanner: {model_name}")
                bancode_params['model'] = enabled_models[model_name] # Model class from LLM Guard
            else:
                logger.error("Model name is not valid for BanCode scanner")
        if threshold is not None:
            bancode_params['threshold'] = threshold # float
        logger.info(f"Creating BanCode scanner with params: {bancode_params}")
        return BanCode(**bancode_params)
    
    def _create_ban_competitors_scanner(self, scanner_config):
        enabled_models = {'MODEL_V1': BANCOMPETITORS_MODEL_V1}
        ban_competitors_params = {'use_onnx': scanner_config.get('use_onnx', True)} # by default we want to use onnx

        competitors = scanner_config.get('competitors', None)
        threshold = scanner_config.get('threshold', None)
        redact = scanner_config.get('redact', None)
        model_name = scanner_config.get('model', None)

        if competitors:
            if isinstance(competitors, str):
                artifacts = set([',', '', '.'])
                ban_competitors_params['competitors'] = list(set(competitors.split(',')) - artifacts) # list
            elif isinstance(competitors, list):
                ban_competitors_params['competitors'] = competitors
            else:
                logger.error("Provided type is not valid for BanCompetitors scanner")
                raise ValueError("Provided type is not valid for BanCompetitors scanner")
        else:
            logger.error("Competitors list is required for BanCompetitors scanner")
            raise Exception("Competitors list is required for BanCompetitors scanner")
        if threshold is not None:
            ban_competitors_params['threshold'] = threshold # float
        if redact is not None:
            ban_competitors_params['redact'] = redact
        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for BanCompetitors scanner: {model_name}")
                ban_competitors_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for BanCompetitors scanner")
        logger.info(f"Creating BanCompetitors scanner with params: {ban_competitors_params}")
        return BanCompetitors(**ban_competitors_params)
    
    def _create_ban_substrings_scanner(self, scanner_config):
        available_match_types = ['str', 'word']
        ban_substrings_params = {}

        substrings = scanner_config.get('substrings', None)
        match_type = scanner_config.get('match_type', None)
        case_sensitive = scanner_config.get('case_sensitive', None)
        redact = scanner_config.get('redact', None)
        contains_all = scanner_config.get('contains_all', None)

        if substrings:
            if isinstance(substrings, str):
                artifacts = set([',', '', '.'])
                ban_substrings_params['substrings'] = list(set(substrings.split(',')) - artifacts)# list
            elif substrings and isinstance(substrings, list):
                ban_substrings_params['substrings'] = substrings
            else:
                logger.error("Provided type is not valid for BanSubstrings scanner")
                raise ValueError("Provided type is not valid for BanSubstrings scanner")
        else:
            logger.error("Substrings list is required for BanSubstrings scanner")
            raise Exception("Substrings list is required for BanSubstrings scanner")
        if match_type is not None and match_type in available_match_types:
            ban_substrings_params['match_type'] = match_type # MatchType
        if case_sensitive is not None:
            ban_substrings_params['case_sensitive'] = case_sensitive # bool
        if redact is not None:
            ban_substrings_params['redact'] = redact # bool
        if contains_all is not None:
            ban_substrings_params['contains_all'] = contains_all # bool
        logger.info(f"Creating BanSubstrings scanner with params: {ban_substrings_params}")
        return BanSubstrings(**ban_substrings_params)
    
    def _create_ban_topics_scanner(self, scanner_config):
        enabled_models = {
            'MODEL_DEBERTA_LARGE_V2': BANTOPICS_MODEL_DEBERTA_LARGE_V2,
            'MODEL_DEBERTA_BASE_V2': BANTOPICS_MODEL_DEBERTA_BASE_V2,
            'MODEL_BGE_M3_V2': BANTOPICS_MODEL_BGE_M3_V2,
            'MODEL_ROBERTA_LARGE_C_V2': BANTOPICS_MODEL_ROBERTA_LARGE_C_V2,
            'MODEL_ROBERTA_BASE_C_V2': BANTOPICS_MODEL_ROBERTA_BASE_C_V2
        }
        ban_topics_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        topics = scanner_config.get('topics', None)
        threshold = scanner_config.get('threshold', None)
        model_name = scanner_config.get('model', None)

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
            raise Exception("Topics list is required for BanTopics scanner")
        if threshold is not None:
            ban_topics_params['threshold'] = threshold
        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for BanTopics scanner: {model_name}")
                ban_topics_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for BanTopics scanner")
        logger.info(f"Creating BanTopics scanner with params: {ban_topics_params}")
        return BanTopics(**ban_topics_params)
    
    def _create_code_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': CODE_DEFAULT_MODEL}
        code_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        languages = scanner_config.get('languages', None)
        model_name = scanner_config.get('model', None)
        is_blocked = scanner_config.get('is_blocked', None)
        threshold = scanner_config.get('threshold', None)

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
            raise Exception("Languages list is required for Code scanner")
        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for Code scanner: {model_name}")
                code_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for Code scanner")
        if is_blocked is not None:
            code_params['is_blocked'] = is_blocked
        if threshold is not None:
            code_params['threshold'] = threshold
        logger.info(f"Creating Code scanner with params: {code_params}")
        return Code(**code_params)
    
    def _create_gibberish_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': GIBBERISH_DEFAULT_MODEL}
        enabled_match_types = ['sentence', 'full']
        gibberish_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)

        if threshold is not None:
            gibberish_params['threshold'] = threshold
        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for Gibberish scanner: {model_name}")
                gibberish_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for Gibberish scanner")
        if match_type is not None and match_type in enabled_match_types:
            gibberish_params['match_type'] = match_type

        logger.info(f"Creating Gibberish scanner with params: {gibberish_params}")
        return Gibberish(**gibberish_params)

    def _create_invisible_text_scanner(self):
        return InvisibleText()
    
    def _create_language_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': LANGUAGE_DEFAULT_MODEL}
        enabled_match_types = ['sentence', 'full']
        language_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        valid_languages = scanner_config.get('valid_languages', None)
        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)

        if valid_languages:
            if isinstance(valid_languages, str):
                artifacts = set([',', '', '.'])
                language_params['valid_languages'] = list(set(valid_languages.split(',')) - artifacts)
            elif isinstance(valid_languages, list):
                language_params['valid_languages'] = valid_languages
            else:
                logger.error("Provided type is not valid for Language scanner")
                raise ValueError("Provided type is not valid for Language scanner")
        else:
            logger.error("Valid languages list is required for Langudage scanner")
            raise Exception("Valid languages list is required for Language scanner")
        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for Language scanner: {model_name}")
                language_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for Language scanner")
        if threshold is not None:
            language_params['threshold'] = threshold
        if match_type is not None and match_type in enabled_match_types:
            language_params['match_type'] = match_type
        logger.info(f"Creating Language scanner with params: {language_params}")
        return Language(**language_params)
    
    def _create_prompt_injection_scanner(self, scanner_config):
        enabled_models = {
            'V1_MODEL': PROMPTINJECTION_V1_MODEL,
            'V2_MODEL': PROMPTINJECTION_V2_MODEL,
            'V2_SMALL_MODEL': PROMPTINJECTION_V2_SMALL_MODEL
        }
        enabled_match_types = ['sentence', 'full', "truncate_token_head_tail", "truncate_head_tail", "chunks"]
        prompt_injection_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)

        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for PromptInjection scanner: {model_name}")
                prompt_injection_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for PromptInjection scanner")
        if threshold is not None:
            prompt_injection_params['threshold'] = threshold
        if match_type is not None and match_type in enabled_match_types:
            prompt_injection_params['match_type'] = match_type
        logger.info(f"Creating PromptInjection scanner with params: {prompt_injection_params}")
        return PromptInjection(**prompt_injection_params)
    
    def _create_regex_scanner(self, scanner_config):
        enabled_match_types = ['search', 'fullmatch']
        regex_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        patterns = scanner_config.get('patterns', None)
        is_blocked = scanner_config.get('is_blocked', None)
        match_type = scanner_config.get('match_type', None)
        redact = scanner_config.get('redact', None)

        if patterns:
            if isinstance(patterns, str):
                artifacts = set([',', '', '.'])
                regex_params['valid_languages'] = list(set(patterns.split(',')) - artifacts)
            elif isinstance(patterns, list):
                regex_params['valid_languages'] = patterns
            else:
                logger.error("Provided type is not valid for Regex scanner")
                raise ValueError("Provided type is not valid for Regex scanner")
        else:
            logger.error("Patterns list is required for Regex scanner")
            raise Exception("Patterns list is required for Regex scanner")
        if is_blocked is not None:
            regex_params['is_blocked'] = is_blocked
        if match_type is not None and match_type in enabled_match_types:
            regex_params['match_type'] = match_type
        if redact is not None:
            regex_params['redact'] = redact

        logger.info(f"Creating Regex scanner with params: {regex_params}")
        return Regex(**regex_params)
    
    def _create_secrets_scanner(self, scanner_config):
        enabled_redact_types = ['partial', 'all', 'hash']
        secrets_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        redact = scanner_config.get('redact', None)

        if redact is not None and redact in enabled_redact_types:
            secrets_params['redact'] = redact

        logger.info(f"Creating Secrets scanner with params: {secrets_params}")
        return Secrets(**secrets_params)
    
    def _create_sentiment_scanner(self, scanner_config):
        enabled_lexicons = ["vader_lexicon"]
        sentiment_params = {}

        threshold = scanner_config.get('threshold', None)
        lexicon = scanner_config.get('lexicon', None)

        if threshold is not None:
            sentiment_params['threshold'] = threshold
        if lexicon is not None and lexicon in enabled_lexicons:
            sentiment_params['lexicon'] = lexicon

        logger.info(f"Creating Sentiment scanner with params: {sentiment_params}")
        return Sentiment(**sentiment_params)
    
    def _create_token_limit_scanner(self, scanner_config):
        enabled_encodings = ['cl100k_base'] # TODO: test more encoding from tiktoken
        token_limit_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        limit = scanner_config.get('limit', None)
        encoding_name = scanner_config.get('encoding', None)

        if limit is not None:
            token_limit_params['limit'] = limit
        if encoding_name is not None and encoding_name in enabled_encodings:
            token_limit_params['encoding_name'] = encoding_name

        logger.info(f"Creating TokenLimit scanner with params: {token_limit_params}")
        return TokenLimit(**token_limit_params)
    
    def _create_toxicity_scanner(self, scanner_config):
        enabled_models = {'DEFAULT_MODEL': TOXICITY_DEFAULT_MODEL}
        enabled_match_types = ['sentence', 'full']
        toxicity_params = {'use_onnx': scanner_config.get('use_onnx', True)}

        model_name = scanner_config.get('model', None)
        threshold = scanner_config.get('threshold', None)
        match_type = scanner_config.get('match_type', None)


        if model_name is not None:
            if model_name in enabled_models:
                logger.info("Using selected model for Toxicity scanner: {model_name}")
                toxicity_params['model'] = enabled_models[model_name]
            else:
                logger.error("Model name is not valid for Toxicity scanner")
        if threshold is not None:
            toxicity_params['threshold'] = threshold
        if match_type is not None and match_type in enabled_match_types:
            toxicity_params['match_type'] = match_type

        logger.info(f"Creating Toxicity scanner with params: {toxicity_params}")
        return Toxicity(**toxicity_params)

    def _create_input_scanner(self, scanner_name, scanner_config):
        if scanner_name not in ENABLED_SCANNERS:
            logger.error(f"Scanner {scanner_name} is not supported. Enabled scanners are: {ENABLED_SCANNERS}")
            raise Exception(f"Scanner {scanner_name} is not supported")
        if scanner_name == 'anonymize':
            return self._create_anonymize_scanner(scanner_config)
        elif scanner_name == 'ban_code':
            return self._create_ban_code_scanner(scanner_config)
        elif scanner_name == 'ban_competitors':
            return self._create_ban_competitors_scanner(scanner_config)
        elif scanner_name == 'ban_substrings':
            return self._create_ban_substrings_scanner(scanner_config)
        elif scanner_name == 'ban_topics':
            return self._create_ban_topics_scanner(scanner_config)
        elif scanner_name == 'code':
            return self._create_code_scanner(scanner_config)
        elif scanner_name == 'gibberish':
            return self._create_gibberish_scanner(scanner_config)
        elif scanner_name == 'invisible_text':
            return self._create_invisible_text_scanner()
        elif scanner_name == 'language':
            return self._create_language_scanner(scanner_config)
        elif scanner_name == 'prompt_injection':
            return self._create_prompt_injection_scanner(scanner_config)
        elif scanner_name == 'regex':
            return self._create_regex_scanner(scanner_config)
        elif scanner_name == 'secrets':
            return self._create_secrets_scanner(scanner_config)
        elif scanner_name == 'sentiment':
            return self._create_sentiment_scanner(scanner_config)
        elif scanner_name == 'token_limit':
            return self._create_token_limit_scanner(scanner_config)
        elif scanner_name == 'toxicity':
            return self._create_toxicity_scanner(scanner_config)
        return None

    def create_enabled_input_scanners(self):
        """
        Create and return a list of enabled scanners based on the global configuration.

        Returns:
            list: A list of enabled scanner instances.
        """
        enabled_scanners_names_and_configs = {k: v for k, v in self._input_scanners_config.items() if v.get("enabled")}
        enabled_scanners_objects = []
        for scanner_name, scanner_config in enabled_scanners_names_and_configs.items():
            try:
                logger.info(f"Attempting to create scanner: {scanner_name}")
                scanner_object = self._create_input_scanner(scanner_name, scanner_config)
                enabled_scanners_objects.append(scanner_object)
            except Exception as e:
                logger.exception(
                    f"An unexpected error occured during creating input scanner {scanner_name}: {e}"
                )
                continue
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
        newly_enabled_scanners = {k: {in_k: in_v for in_k, in_v in v.items() if in_k != 'id'} for k, v in new_scanners_config.items() if v.get("enabled")}
        previously_enabled_scanners = {k: v for k, v in self._input_scanners_config.items() if v.get("enabled")}
        if newly_enabled_scanners == previously_enabled_scanners: # if the enables scanners are the same we do nothing
            logger.info("No changes in list for enabled scanners. Checking configuration changes...")
            return False
        else:
            logger.warning("Sanners configuration has been changed, re-creating scanners")
            self._input_scanners_config.clear()
            stripped_new_scanners_config = {k: {in_k: in_v for in_k, in_v in v.items() if in_k != 'id'} for k, v in new_scanners_config.items()}
            self._input_scanners_config.update(stripped_new_scanners_config)
            return True

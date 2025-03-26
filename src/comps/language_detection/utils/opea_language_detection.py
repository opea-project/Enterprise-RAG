# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re

from typing import Union

from comps.language_detection.utils.detector import detect_language
from comps.language_detection.utils.prompt import get_prompt_template, get_language_name, validate_language_name
from comps import PromptTemplateInput, GeneratedDoc, TranslationInput, get_opea_logger


logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEALanguageDetector:
    def __init__(self, is_standalone=False):
        self._is_standalone = is_standalone
        logger.info("Language Detection microservice initialized.")

    def run(self, input: Union[GeneratedDoc, TranslationInput]) -> PromptTemplateInput:
        """
        If is_standalone is False, detects the language of the query and sets up a translation prompt if needed, without modifying the query.
        If is_standlaone is True, detects language of the provided text and sets up a translation prompt to translate text to target language.

        Args:
            input (Union[GeneratedDoc, TranslationInput]): The input document containing the initial query and answer or text and target_language.

        Returns:
            PromptTemplateInput: The prompt template and place holders for translation.
        """
        if self._is_standalone:
            if not input.text.strip():
                logger.error("No text provided.")
                raise ValueError("Text to to be translated cannot be empty.")
            
            if not input.target_language.strip():
                logger.error("Target language not provided.")
                raise ValueError("Target language cannot be empty.")
            
            # Detect the language of the query
            src_lang_code = detect_language(input.text)
            source_language = get_language_name(src_lang_code)

            if not source_language:
                logger.error(f"The detected language {src_lang_code} is not supported.")
                raise ValueError("Original language of text is not supported.")

            logger.info(f"Detected language of the text: {source_language}")

            # Check if the provided target language is valid
            target_language = input.target_language.strip()
            if not validate_language_name(target_language):
                logger.error(f"Target language {target_language} is not supported.")
                raise ValueError("Provided target language is not supported.")
        else:
            if not input.prompt.strip():
                logger.error("No initial query provided.")
                raise ValueError("Initial query cannot be empty.")
            
            if not input.text.strip():
                logger.error("No answer provided from LLM.")
                raise ValueError("Answer from LLM cannot be empty.")

            # Extract question from prompt
            match = re.search(r"### Question:\s*(.*?)\s*(?=### Answer:|$)", input.prompt, re.DOTALL)

            if match:
                extracted_question = match.group(1).strip()  # Remove any leading/trailing whitespace
            else:
                logger.error("Question could not be found in the prompt.")
                raise ValueError("Question not found in the prompt!") 
    
            # Detect the language of the query (target language)
            tgt_lang_code = detect_language(extracted_question)
            target_language = get_language_name(tgt_lang_code)

            if not target_language:
                logger.error(f"The detected query language {tgt_lang_code} is not supported.")
                raise ValueError("Language of query is not supported.")

            logger.info(f"Detected language of the query: {target_language}")

            # Detect the language of the answer
            src_lang_code = detect_language(input.text)
            source_language = get_language_name(src_lang_code)

            if not source_language:
                logger.error(f"The detected answer language {src_lang_code} is not supported.")
                raise ValueError("Language of answer is not supported.")

            logger.info(f"Detected language of the answer: {source_language}")

            # Prevents back-translation to English if RAG LLM generates answer in the same language
            if source_language == target_language:
                source_language = "en"

        # Return the prompt template input for translation
        return PromptTemplateInput(data={"text": input.text, "source_lang": source_language, "target_lang": target_language}, prompt_template=get_prompt_template())

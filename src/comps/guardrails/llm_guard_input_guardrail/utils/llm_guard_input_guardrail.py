# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from llm_guard import scan_prompt
from fastapi import HTTPException

from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_scanners import InputScannersConfig
from comps import get_opea_logger, LLMParamsDoc

logger = get_opea_logger("opea_llm_guard_input_guardrail_microservice")


class OPEALLMGuardInputGuardrail:
    """
    OPEALLMGuardInputGuardrail is responsible for scanning and sanitizing LLM input prompts
    using various input scanners provided by LLM Guard.

    This class initializes the input scanners based on the provided configuration and
    scans the input prompts to ensure they meet the required guardrail criteria.

    Attributes:
        _scanners (list): A list of enabled scanners.

    Methods:
        __init__(usv_config: dict):
            Initializes the OPEALLMGuardInputGuardrail with the provided configuration.
        
        scan_llm_input(input_doc: LLMParamsDoc) -> tuple[str, dict[str, bool], dict[str, float]]:
            Scans the prompt from an LLMParamsDoc object and returns the sanitized prompt,
            validation results, and scores.
    """

    def __init__(self, usv_config: dict):
        """
        Initializes the OPEALLMGuardInputGuardrail with the provided configuration.

        Args:
            usv_config (dict): The configuration dictionary for initializing the input scanners.

        Raises:
            Exception: If an unexpected error occurs during the initialization of scanners.
        """
        try:
            self._scanners_config = InputScannersConfig(usv_config)
            self._scanners = self._scanners_config.create_enabled_input_scanners()
        except Exception as e:
            logger.exception(
                f"An unexpected error occured during initializing \
                    LLM Guard Input Guardrail scanners: {e}"
            )
            raise

    def scan_llm_input(self, input_doc: LLMParamsDoc) -> LLMParamsDoc:
        """
        Scan the prompt from an LLMParamsDoc object.

        Args:
            input_doc (LLMParamsDoc): The input document containing the prompt to be scanned.

        Returns:
            tuple[str, dict[str, bool], dict[str, float]]: A tuple containing the sanitized prompt, 
            a dictionary of validation results, and a dictionary of scores.

        Raises:
            HTTPException: If the prompt is not valid based on the scanner results.
            Exception: If an unexpected error occurs during scanning.
        """
        try:
            # if self._scanners_config.changed(input_doc.input_guardrail_params.dict()): # TODO: to be enabled in v1.0
            #    self._scanners = self._scanners_config.create_enabled_input_scanners()
            prompt = input_doc.query
            sanitized_prompt, results_valid, results_score = scan_prompt(self._scanners, prompt)
            if False in results_valid.values():
                msg = f"Prompt {prompt} is not valid, scores: {results_score}"
                logger.error(f"{msg}")
                raise HTTPException(status_code=500, detail=f"{msg}")
            input_doc.query = sanitized_prompt
            return input_doc
        except Exception as e:
            logger.exception(
                f"An unexpected error occured during scanning prompt with \
                    LLM Guard Output Guardrail: {e}"
            )
            raise HTTPException(status_code=500, detail=f"{e}") from e

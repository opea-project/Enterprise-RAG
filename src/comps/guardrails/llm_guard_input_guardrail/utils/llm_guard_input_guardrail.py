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

    def _get_anonymize_vault(self):
        anon = [item for item in self._scanners if type(item).__name__ == "Anonymize"]
        if len(anon) > 0:
            return anon[0]._vault.get()
        return None

    def _recreate_anonymize_scanner_if_exists(self):
        anon = [item for item in self._scanners if type(item).__name__ == "Anonymize"]
        logger.info(f"Anonymize scanner found: {len(anon)}")
        if len(anon) > 0:
            self._scanners.remove(anon[0])
            self._scanners.append(self._scanners_config.create_anonymize_scanner())

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
            fresh_scanners = False
            if input_doc.input_guardrail_params is not None:
                if self._scanners_config.changed(input_doc.input_guardrail_params.dict()):
                    self._scanners = self._scanners_config.create_enabled_input_scanners()
                    fresh_scanners = True
            else:
                logger.warning("Input guardrail params not found in input document.")
            if self._scanners:
                if not fresh_scanners:
                    logger.info("Recreating anonymize scanner if exists.")
                    self._recreate_anonymize_scanner_if_exists()
                prompt = input_doc.query
                sanitized_prompt, results_valid, results_score = scan_prompt(self._scanners, prompt)
                if False in results_valid.values():
                    msg = f"Prompt {prompt} is not valid, scores: {results_score}"
                    logger.error(f"{msg}")
                    usr_msg = "I'm sorry, I cannot assist you with your prompt."
                    raise HTTPException(status_code=466, detail=f"{usr_msg}")
                input_doc.query = sanitized_prompt
                if input_doc.output_guardrail_params is not None:
                    input_doc.output_guardrail_params.anonymize_vault = self._get_anonymize_vault()
                else:
                    logger.warning("No output guardrails params, could not append the vault for Anonymize scanner.")
                return input_doc
            else:
                logger.info("No input scanners enabled. Skipping scanning.")
                return input_doc
        except Exception as e:
            logger.exception(
                f"An unexpected error occured during scanning prompt with \
                    LLM Guard Output Guardrail: {e}"
            )
            raise

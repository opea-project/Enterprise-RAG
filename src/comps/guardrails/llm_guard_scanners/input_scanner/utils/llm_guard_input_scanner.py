# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Optional
from llm_guard import scan_prompt
from llm_guard.input_scanners import BanSubstrings, InvisibleText, Regex
from fastapi import HTTPException

# Documentation for input scanners https://llm-guard.com/input_scanners/anonymize/

INPUT_SCANNERS = {  #TODO: enable rest of scanners
    'BanSubstrings': BanSubstrings(substrings=["backdoor", "malware", "virus"]), # TODO: ensure external configuration per scanner, example for now
    'InvisibleText': InvisibleText(),
    'Regex': Regex(patterns=[r"Bearer [A-Za-z0-9-._~+/]+"])
}

class LLMGuardInputScanner:
    """
    Class used for defining input LLM Guard scanners
    """

    _scanners = []

    def __init__(self, config: list):
        try:
            for scanner in config:
                self._scanners.append(INPUT_SCANNERS[scanner])
        except Exception as e:
            logging.error(f"An unexpected error occured during initializing LLM Guard input scanners: {e}")
            raise


    def scan_input(self, prompt: str) -> tuple[str, dict[str, bool], dict[str, float]]:
        """
        Scan prompt from LLMParamsDoc object.

        Args:
            prompt (str): prompt to LLM Model
        """

        try:
            sanitized_prompt, results_valid, results_score = scan_prompt(self._scanners, prompt)
            if False in results_valid.values():
                msg = f"Prompt {prompt} is not valid, scores: {results_score}"
                logging.error(f"{msg}")
                raise HTTPException(status_code=400, detail=f"{msg}")

            return sanitized_prompt
        except Exception as e:
            logging.error(f"An unexpected error occured during scanning prompt with LLM Guard input scanners: {e}")
            raise




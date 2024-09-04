# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from fastapi import HTTPException
from llm_guard import scan_output
from llm_guard.output_scanners import BanSubstrings, JSON, ReadingTime, Regex, URLReachability

from comps import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

# Documentation for output scanners: https://llm-guard.com/output_scanners/ban_competitors/

OUTPUT_SCANNERS = {  #TODO: enable rest of scanners
    'BanSubstrings':  BanSubstrings(substrings=["backdoor", "malware", "virus"]),
    'JSON': JSON(),
    'ReadingTime': ReadingTime(max_time=50, truncate=True),
    'Regex': Regex(patterns=[r"Bearer [A-Za-z0-9-._~+/]+"]),
    'URLReachability': URLReachability(success_status_codes=[200, 201, 202, 301, 302], timeout=1)
}

class LLMGuardOutputScanner:
    """
    Class used for defining output LLM Guard scanners
    """

    _scanners = []

    def __init__(self, config: list):
        try:
            for scanner in config:
                self._scanners.append(OUTPUT_SCANNERS[scanner])
        except Exception as e:
            logger.error(f"An unexpected error occured during initializing LLM Guard output scanners: {e}")
            raise


    def scan_llm_output(self, prompt: str, output: str) -> str:
        """
        Scan output from LLMParamsDoc object.

        Args:
            output (str): out to LLM Model
        """
        try:
            sanitized_output, results_valid, results_score = scan_output(self._scanners, prompt, output)
            if False in results_valid.values():
                msg = f"Output {output} is not valid, scores: {results_score}"
                logger.error(f"{msg}")
                raise HTTPException(status_code=400, detail=f"{msg}")
            return sanitized_output
        except Exception as e:
            logger.error(f"An unexpected error occured during scanning output with LLM Guard output scanners: {e}")
            raise
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from comps import (
    LLMParamsDoc,
    ServiceType,
    MegaServiceEndpoint,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

from comps.guardrails.llm_guard_scanners.input_scanner.utils import llm_guard_input_scanner

logger = get_opea_logger("llm_guard_input_scanner_microservice") # TODO: to be changed to after folder structure changes


def start_llm_guard_input_scanner_service(llm_guard_input_scanner: llm_guard_input_scanner.LLMGuardInputScanner, opea_microservice_name: str):
    """Create the embedding service with the given LLM Guard input scanner.

    Args:
        llm_guard_input_scanner (llm_guard_input_scanner.LLMGuardInputScanner): An instance of LLM Guard Input Scanner class.
        opea_microservice_name (str): The name of the microservice.
    """

    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.LLM_GUARD_INPUT_SCANNER,
        endpoint=str(MegaServiceEndpoint.LLM_GUARD_INPUT_SCANNER),
        host="0.0.0.0",
        port=8050,
        input_datatype=LLMParamsDoc,
        output_datatype=LLMParamsDoc,
    )
    @register_statistics(names=[opea_microservice_name])
    def input_scanner(input: LLMParamsDoc) -> LLMParamsDoc:
        start = time.time()
        sanitized_prompt = llm_guard_input_scanner.scan_input(input.query)
        input.query = sanitized_prompt
        statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)
        return input

    opea_microservices[opea_microservice_name].start()


if __name__ == "__main__":
    log_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    try:
        logger.info("Initializing LLMGuardInputScanner")
        config = ['BanSubstrings', 'InvisibleText', 'Regex'] #TODO: make config configurable through k8s // config.ini
        input_scanner = llm_guard_input_scanner.LLMGuardInputScanner(config)
        opea_microservice_name = "opea_service@llm_guard_input_scanner"
        start_llm_guard_input_scanner_service(input_scanner, opea_microservice_name)
    except Exception as e:
        logger.exception(f"Error initializing LLMGuardInputScanner: {e}")
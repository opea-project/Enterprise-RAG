# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import dotenv_values

from comps import (
    LLMParamsDoc,
    ServiceType,
    MegaServiceEndpoint,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
)
from comps.guardrails.llm_guard_input_guardrail.utils.llm_guard_input_guardrail import (
    OPEALLMGuardInputGuardrail
)

USVC_NAME = "opea_service@llm_guard_input_scanner"
logger = get_opea_logger("opea_llm_guard_input_guardrail_microservice")

usvc_config = {
    **dotenv_values(".env"),
    **os.environ # override loaded values with environment variables - priotity
}

input_guardrail = OPEALLMGuardInputGuardrail(usvc_config)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.LLM_GUARD_INPUT_SCANNER,
    endpoint=str(MegaServiceEndpoint.LLM_GUARD_INPUT_SCANNER),
    host="0.0.0.0",
    port=usvc_config.get('LLM_GUARD_INPUT_SCANNER_USVC_PORT', 8050),
    input_datatype=LLMParamsDoc,
    output_datatype=LLMParamsDoc,
)

@register_statistics(names=[USVC_NAME])
def process(input_doc: LLMParamsDoc) -> LLMParamsDoc:
    """
    Process the input document using the OPEALLMGuardInputGuardrail.
    This function processes the input document by scanning it using the LLM Guard Input Scanner.

    Args:
        input_doc (LLMParamsDoc): The input document to be processed.

    Returns:
        LLMParamsDoc: The processed document with LLM parameters.
    """
    return input_guardrail.scan_llm_input(input_doc)


if __name__ == "__main__":
    log_level = usvc_config.get("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    opea_microservices[USVC_NAME].start()


# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import dotenv_values

from comps import (
    TextDocList,
    ServiceType,
    MegaServiceEndpoint,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
)

from comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_guardrail import (
    OPEALLMGuardDataprepGuardrail
)

USVC_NAME = "opea_service@llm_guard_dataprep_scanner"
logger = get_opea_logger("opea_llm_guard_dataprep_guardrail_microservice")

usvc_config = {
    **dotenv_values("impl/microservice/.env"),
    **os.environ # override loaded values with environment variables - priority
}

dataprep_guardrail = OPEALLMGuardDataprepGuardrail(usvc_config)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.LLM_GUARD_DATAPREP_SCANNER,
    endpoint=str(MegaServiceEndpoint.LLM_GUARD_DATAPREP_SCANNER),
    host="0.0.0.0",
    port=int(usvc_config.get('LLM_GUARD_DATAPREP_SCANNER_USVC_PORT', 8070)),
    input_datatype=TextDocList,
    output_datatype=TextDocList,
)

@register_statistics(names=[USVC_NAME])
def process(dataprep_docs: TextDocList) -> TextDocList:
    """
    Process the documents uploaded to dataprep using the OPEALLMGuardDataprepGuardrail.
    This function processes the input document by scanning it using the LLM Guard Dataprep Scanner.

    Args:
        dataprep_docs (TextDocList): The input document to be processed.

    Returns:
        TextDocList: The scanned dataprep documents.
    """
    return dataprep_guardrail.scan_dataprep_docs(dataprep_docs)


if __name__ == "__main__":
    log_level = usvc_config.get("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    opea_microservices[USVC_NAME].start()
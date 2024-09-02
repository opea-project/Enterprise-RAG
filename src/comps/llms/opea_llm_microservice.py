# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from fastapi.responses import StreamingResponse
from langsmith import traceable
from typing import Union

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    MegaServiceEndpoint,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
)
from comps.llms.utils.opea_llm import OPEALlm

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
opea_llm = OPEALlm(config_file=config_file)

@register_microservice(
    name=opea_llm.name,
    service_type=ServiceType.LLM,
    endpoint=str(MegaServiceEndpoint.CHAT),
    host=opea_llm.host,
    port=opea_llm.port,
    input_datatype=LLMParamsDoc,
    output_datatype=(Union[GeneratedDoc, StreamingResponse]),
)
@register_statistics(names=[opea_llm.name])
@traceable(run_type="llm")
def process(input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
    return opea_llm.run(input)

if __name__ == "__main__":
    log_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    logger.debug("Starting OPEA LLM Microservice")

    opea_microservices[opea_llm.name].start()

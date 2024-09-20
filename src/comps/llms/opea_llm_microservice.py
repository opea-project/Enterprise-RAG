# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import load_dotenv
from fastapi.responses import Response
from langsmith import traceable

from comps import (
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

USV_NAME='opea_service@llm'
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

# Load environment variables from .env file
load_dotenv("./impl/microservice/.env")

opea_llm = OPEALlm()

@register_microservice(
    name=USV_NAME,
    service_type=ServiceType.LLM,
    endpoint=str(MegaServiceEndpoint.CHAT),
    host='0.0.0.0',
    port=int(os.getenv('LLM_USVC_PORT', default=9000)),
    input_datatype=LLMParamsDoc,
    output_datatype=Response, # can be either "comps.GeneratedDoc" for non-streaming mode, or "fastapi.responses.StreamingResponse" for streaming mode 
)
@register_statistics(names=[USV_NAME])
@traceable(run_type="llm")
def process(input: LLMParamsDoc) -> Response:
    return opea_llm.run(input)

if __name__ == "__main__":
    log_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    logger.debug("Starting OPEA LLM Microservice")
    opea_microservices[USV_NAME].start()

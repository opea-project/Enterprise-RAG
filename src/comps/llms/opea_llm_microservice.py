# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException
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
    sanitize_env,
    statistics_dict,
)
from comps.llms.utils.opea_llm import OPEALlm

# Define the unique service name for the microservice
USVC_NAME='opea_service@llm'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEALlm class with environment variables.
opea_llm = OPEALlm(
    model_name=sanitize_env(os.getenv('LLM_MODEL_NAME')),
    model_server=sanitize_env(os.getenv('LLM_MODEL_SERVER')),
    model_server_endpoint=sanitize_env(os.getenv('LLM_MODEL_SERVER_ENDPOINT')),
    connector_name=sanitize_env(os.getenv('LLM_CONNECTOR')),
)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.LLM,
    endpoint=str(MegaServiceEndpoint.CHAT),
    host='0.0.0.0',
    port=int(os.getenv('LLM_USVC_PORT', default=9000)),
    input_datatype=LLMParamsDoc,
    output_datatype=Response, # can be either "comps.GeneratedDoc" for non-streaming mode, or "fastapi.responses.StreamingResponse" for streaming mode
    validate_methods=[opea_llm._connector._validate]
)
@register_statistics(names=[USVC_NAME])
@traceable(run_type="llm")
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
def process(input: LLMParamsDoc) -> Response:
    """
    Processes the given LLMParamsDoc input using the OPEA LLM microservice.

    Args:
        input (LLMParamsDoc): The input parameters for the LLM processing.

    Returns:
        Response: The response from the OPEA LLM microservice.
    """
    start = time.time()
    try:
        # Pass the input to the 'run' method of the microservice instance
        res = opea_llm.run(input)
    except Exception as e:
         logger.exception(f"An error occurred while processing: {str(e)}")
         raise HTTPException(status_code=500,
                             detail=f"An error occurred while processing: {str(e)}"
    )
    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")

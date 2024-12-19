# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException

from comps import (
    LLMParamsDoc,
    MegaServiceEndpoint,
    PromptTemplateInput,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.prompt_template.utils.opea_prompt_template import OPEAPromptTemplate

# Define the unique service name for the microservice
USVC_NAME='opea_service@prompt_template'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEALlm class with environment variables.
opea_prompt_template = OPEAPromptTemplate()

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.PROMPT_TEMPLATE,
    endpoint=str(MegaServiceEndpoint.PROMPT_TEMPLATE),
    host='0.0.0.0',
    port=int(os.getenv('PROMPT_TEMPLATE_USVC_PORT', default=7900)),
    input_datatype=PromptTemplateInput,
    output_datatype=LLMParamsDoc,
)

@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: PromptTemplateInput) -> LLMParamsDoc:
    """

    Returns:
        LLMParamsDoc: The processed document with LLM parameters.
    """
    start = time.time()
    try:
        # Pass the input to the 'run' method of the microservice instance
        res = await opea_prompt_template.run(input)
    except ValueError as e:
        logger.exception(f"An internal error occurred while processing: {str(e)}")
        raise HTTPException(status_code=400,
                            detail=f"An internal error occurred while processing: {str(e)}"
        )
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

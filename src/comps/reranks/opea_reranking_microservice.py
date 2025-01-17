# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from asyncio import TimeoutError
from dotenv import load_dotenv
from fastapi import HTTPException
from langsmith import traceable
from requests.exceptions import RequestException, Timeout


from comps import (
    MegaServiceEndpoint,
    SearchedDoc,
    PromptTemplateInput,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    sanitize_env,
    statistics_dict,
)
from comps.reranks.utils.opea_reranking import OPEAReranker

# Define the unique service name for the microservice
USVC_NAME='opea_service@reranking'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEALlm class with environment variables.
opea_reranker = OPEAReranker(
    service_endpoint=sanitize_env(os.getenv('RERANKING_SERVICE_ENDPOINT')),
)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.RERANK,
    endpoint=str(MegaServiceEndpoint.RERANKING),
    host='0.0.0.0',
    port=int(os.getenv('RERANKING_USVC_PORT', default=8000)),
    input_datatype=SearchedDoc,
    output_datatype=PromptTemplateInput,
)
@traceable(run_type="llm")
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: SearchedDoc) -> PromptTemplateInput:
    """
    Asynchronously process the input document using the OPEAReranker..

    Args:
        input (SearchedDoc): The input document to be processed.

    Returns:
        PromptTemplateInput: The result of the processing containing reranked top_n documents

    Raises:
        HTTPException: If a ValueError or any other exception occurs during processing.

    """

    start = time.time()
    try:
        # Pass the input to the 'run' method of the microservice instance
        res = await opea_reranker.run(input)
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except TimeoutError as e:
        error_message = f"A Timeout error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=408, detail=error_message)
    except Timeout as e:
        error_message = f"A Timeout error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=408, detail=error_message)
    except RequestException as e:
        error_code = e.response.status_code if e.response else 503
        error_message = f"A RequestException occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=error_code, detail=error_message)
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

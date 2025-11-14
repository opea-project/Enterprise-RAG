# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import Response
from openai import BadRequestError
from requests.exceptions import ConnectionError, RequestException

from comps import (
    TextDocList,
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
from comps.docsum.utils.opea_docsum import OPEADocsum

# Define the unique service name for the microservice
USVC_NAME='opea_service@docsum'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEADocsum class with environment variables.
opea_docsum = OPEADocsum(llm_usvc_endpoint=sanitize_env(os.getenv("DOCSUM_LLM_USVC_ENDPOINT")),
                         default_summary_type=sanitize_env(os.getenv("DOCSUM_DEFAULT_SUMMARY_TYPE")),
                         max_concurrency=int(os.getenv("DOCSUM_MAX_CONCURRENCY", default=16))
                         )
# Semaphore will be lazily initialized in the async context
endpoint_semaphore = None

def get_endpoint_semaphore():
    """Lazily initialize the semaphore in the running event loop."""
    global endpoint_semaphore
    if endpoint_semaphore is None:
        endpoint_semaphore = asyncio.Semaphore(6)
    return endpoint_semaphore

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.DOC_SUMMARY,
    endpoint=str(MegaServiceEndpoint.DOC_SUMMARY),
    host='0.0.0.0',
    port=int(os.getenv('DOCSUM_USVC_PORT', default=9001)),
    input_datatype=TextDocList,
    output_datatype=Response, # can be either "comps.GeneratedDoc" for non-streaming mode, or "fastapi.responses.StreamingResponse" for streaming mode
    validate_methods=[]
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: TextDocList) -> Response:
    """
    Processes the given TextDocList input using the OPEA DocSum microservice.

    Args:
        input (TextDocList): The input parameters for the DocSum processing.

    Returns:
        Response: The response from the OPEA DocSum microservice.
    """
    semaphore = get_endpoint_semaphore()
    async with semaphore:
        start = time.time()
        try:
            # Pass the input to the 'run' method of the microservice instance
            res = await opea_docsum.run(input)
        except BadRequestError as e:
            error_message = f"A BadRequestError occurred while processing: {str(e)}"
            logger.exception(error_message)
            raise HTTPException(status_code=400, detail=error_message)
        except ValueError as e:
            error_message = f"A ValueError occurred while processing: {str(e)}"
            logger.exception(error_message)
            raise HTTPException(status_code=400, detail=error_message)
        except ConnectionError as e:
            error_message = f"A Connection error occurred while processing: {str(e)}"
            logger.exception(error_message)
            raise HTTPException(status_code=404, detail=error_message)
        except RequestException as e:
            error_code = e.response.status_code if e.response else 500
            error_message = f"A RequestException occurred while processing: {str(e)}"
            logger.exception(error_message)
            raise HTTPException(status_code=error_code, detail=error_message)
        except Exception as e:
            error_message = f"An error occurred while processing: {str(e)}"
            logger.exception(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
        return res


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import Response
from langsmith import traceable
from openai import BadRequestError
from requests.exceptions import ConnectionError, ReadTimeout, RequestException

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
from comps.cores.mega.utils import get_access_token

# Define the unique service name for the microservice
USVC_NAME='opea_service@llm'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Get the token
access_token = get_access_token(sanitize_env(os.getenv('LLM_VLLM_TOKEN_URL')), sanitize_env(os.getenv('LLM_VLLM_CLIENT_ID')), sanitize_env(os.getenv('LLM_VLLM_CLIENT_SECRET'))) if sanitize_env(os.getenv('LLM_VLLM_TOKEN_URL')) and sanitize_env(os.getenv('LLM_VLLM_CLIENT_ID')) and sanitize_env(os.getenv('LLM_VLLM_CLIENT_SECRET')) else None
# If token is passed directly override it
if os.getenv('LLM_VLLM_API_KEY'):
    access_token = sanitize_env(os.getenv('LLM_VLLM_API_KEY')) 

headers = {}
if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}

# Initialize an instance of the OPEALlm class with environment variables.
opea_llm = OPEALlm(
    model_name=sanitize_env(os.getenv('LLM_MODEL_NAME')),
    model_server=sanitize_env(os.getenv('LLM_MODEL_SERVER')),
    model_server_endpoint=sanitize_env(os.getenv('LLM_MODEL_SERVER_ENDPOINT')),
    insecure_endpoint=(sanitize_env(os.getenv('LLM_TLS_SKIP_VERIFY')) == "True"),
    disable_streaming=(sanitize_env(os.getenv('LLM_DISABLE_STREAMING')) == "True"),
    llm_output_guard_exists=(sanitize_env(os.getenv('LLM_OUTPUT_GUARD_EXISTS')) == "True"),
    headers=headers,
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
async def process(input: LLMParamsDoc) -> Response:
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
        res = await opea_llm.run(input)
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except ReadTimeout as e:
        error_message = f"A Timeout error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=408, detail=error_message)
    except ConnectionError as e:
        error_message = f"A Connection error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    except BadRequestError as e:
        error_message = f"A BadRequestError occured while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except RequestException as e:
        error_code = e.response.status_code if e.response else 500
        error_message = f"A RequestException occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=error_code, detail=error_message)
    except NotImplementedError as e:
        error_message = f"A NotImplementedError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=501, detail=error_message)
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

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import os
import time
import requests

from dotenv import load_dotenv
from fastapi import Request, HTTPException
from typing import Union
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError
import asyncio

from comps import (
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

# from utils import opea_asr
from comps.asr.utils.opea_asr import OPEAASR

# Define the unique service name for the microservice
USVC_NAME='opea_service@asr_microservice'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEAASR class with environment variables.
opea_asr = OPEAASR(
    model_name=sanitize_env(os.getenv("ASR_MODEL_NAME")),
    model_server=sanitize_env(os.getenv("ASR_MODEL_SERVER")),
    endpoint=sanitize_env(os.getenv("ASR_MODEL_SERVER_ENDPOINT")),
)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.ASR,
    endpoint=str(MegaServiceEndpoint.ASR),
    host="0.0.0.0",
    port=int(os.getenv('ASR_USVC_PORT', default=8400)),
    input_datatype=Request,
    output_datatype=Response
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(asr_input: Request) -> Response:
    """
    Process the input audio using the OPEAASR.

    Args:
        asr_input (Request): The input audio to be processed.

    Returns:
        Response: The processed streaming response with generated text.
    """

    try:
        form = await asr_input.form()
        file_field = form["data"]  # "data" is the form field name from -F "data=@..."
        # Read the raw bytes from the uploaded file
        file_bytes = await file_field.read()

    except ValidationError as e:
        err_msg = f"ValidationError creating GeneratedDoc: {e.errors()}"
        logger.error(err_msg)
        raise HTTPException(status_code=422, detail=err_msg) from e
    except Exception as e:
         logger.exception(f"An error occurred while processing: {str(e)}")
         raise HTTPException(status_code=500, detail=f"An error occurred while processing: {str(e)}")
    return await opea_asr.run(file_bytes)


if __name__ == "__main__":
    # Start the microservice
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
    opea_microservices[USVC_NAME].start()

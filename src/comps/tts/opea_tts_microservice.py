# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from dotenv import dotenv_values
from fastapi import Request, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError
from comps import (
    GeneratedDoc,
    ServiceType,
    MegaServiceEndpoint,
    get_opea_logger,
    change_opea_logger_level,
    opea_microservices,
    register_microservice,
    register_statistics,
    sanitize_env,
    statistics_dict
)
from comps.tts.utils.opea_tts import OPEATTS

USVC_NAME = "opea_service@tts_microservice"

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

opea_tts = OPEATTS(
    model_name=sanitize_env(os.getenv("TTS_MODEL_NAME")),
    model_server=sanitize_env(os.getenv("TTS_MODEL_SERVER")),
    endpoint=sanitize_env(os.getenv("TTS_MODEL_SERVER_ENDPOINT")), 
)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TTS,
    endpoint=str(MegaServiceEndpoint.TTS),
    host="0.0.0.0",
    port=int(os.getenv('TTS_USVC_PORT', default=8200)),
    input_datatype=Request,
    output_datatype=Response
)

@register_statistics(names=[USVC_NAME])
async def process(tts_input: Request) -> StreamingResponse:
    """
    Process the TTS input request.

    This function processes the TTS input by converting text to speech.
    It handles both JSON and streaming responses.

    Args:
        tts_input (Request): The TTS input request to be processed.

    Returns:
        StreamingResponse: The processed streaming response with generated speech.

    Raises:
        Exception: If there is an error creating the GeneratedDoc or decoding the streaming
        response.
    """
    try:
        data = await tts_input.json()
        # doc = GeneratedDoc(**data)
    except ValidationError as e:
        err_msg = f"ValidationError creating GeneratedDoc: {e.errors()}"
        logger.error(err_msg)
        raise HTTPException(status_code=422, detail=err_msg) from e
    except Exception as e:
        logger.error(f"Problem with creating GenerateDoc: {e}")
        raise HTTPException(status_code=500, detail=f"{e}") from e
    return await opea_tts.run(data)

if __name__ == "__main__":
    logger.info(f"Started TTS Microservice: {USVC_NAME}")
    opea_microservices[USVC_NAME].start()

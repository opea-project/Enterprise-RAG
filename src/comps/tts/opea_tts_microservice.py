# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from aiohttp.client_exceptions import ClientResponseError
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import Response
from requests.exceptions import ConnectionError, ReadTimeout

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
from comps.cores.proto.api_protocol import AudioSpeechRequest
from comps.tts.utils.opea_tts import OPEATTS

# Define the unique service name for the microservice
USVC_NAME = 'opea_service@tts'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEATTS class with environment variables.
opea_tts = OPEATTS(
    model_server=sanitize_env(os.getenv('TTS_MODEL_SERVER')),
    model_server_endpoint=sanitize_env(os.getenv('TTS_MODEL_SERVER_ENDPOINT'))
)


# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TTS,
    endpoint=str(MegaServiceEndpoint.TTS),
    host='0.0.0.0',
    port=int(os.getenv('TTS_USVC_PORT', default=9009)),
    input_datatype=AudioSpeechRequest,
    output_datatype=Response,
    validate_methods=[opea_tts._validate_model_server],
)
@register_statistics(names=[USVC_NAME])
async def process(request: AudioSpeechRequest, raw_request: Request) -> Response:
    """
    Processes text-to-speech conversion using the OPEA TTS microservice.

    Args:
        request: AudioSpeechRequest containing:
            - input: Text to convert to speech
            - voice: Voice to use (optional)
            - response_format: Audio format (mp3, wav)
            - model: Model name (optional)
            - streaming: Whether to stream the response (optional, default: False)
        raw_request: FastAPI Request object for monitoring client disconnections

    Returns:
        Response or StreamingResponse: Complete audio when streaming=False, streamed audio when streaming=True.
    """
    start = time.time()

    try:
        res = await opea_tts.run(request, raw_request)

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
        raise HTTPException(status_code=503, detail=error_message)
    except ClientResponseError as e:
        if hasattr(e, "status"):
            raise HTTPException(status_code=e.status, detail=e.message)
        else:
            raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")

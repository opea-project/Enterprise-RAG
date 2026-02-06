# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException
from typing import Union

from comps import (
    PromptTemplateInput,
    MegaServiceEndpoint,
    GeneratedDoc,
    TranslationInput,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    sanitize_env,
    statistics_dict,
)
from comps.language_detection.utils.opea_language_detection import OPEALanguageDetector

# Define the unique service name for the microservice
USVC_NAME='opea_service@language_detection'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the language detector class with environment variables.
opea_language_detector = OPEALanguageDetector(is_standalone=(sanitize_env(os.getenv('LANG_DETECT_STANDALONE')) == "True"))

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.LANGUAGE_DETECTION,
    endpoint=str(MegaServiceEndpoint.LANGUAGE_DETECTION),
    host='0.0.0.0',
    port=int(os.getenv('LANGUAGE_DETECTION_USVC_PORT', default=8001)),
    input_datatype=Union[GeneratedDoc, TranslationInput],
    output_datatype=PromptTemplateInput,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
def process(input: Union[GeneratedDoc, TranslationInput]) -> PromptTemplateInput:
    """
    Process the input document using the OPEALanguageDetector.

    Args:
        input (Union[GeneratedDoc, TranslationInput]): The input document to be processed.

    Returns:
        PromptTemplateInput: The prompt template and placeholders for translation.
    """
    start = time.time()
    try:
        # Pass the input to the 'run' method of the microservice instance
        res = opea_language_detector.run(input)
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

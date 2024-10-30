# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import os
import time
import requests

from dotenv import load_dotenv
from fastapi import HTTPException
from typing import Union

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
from comps.cores.proto.docarray import EmbedDoc, EmbedDocList, TextDoc, TextDocList

# from utils import opea_embedding
from comps.embeddings.utils.opea_embedding import OPEAEmbedding

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_embedding'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEAEmbedding class with environment variables.
opea_embedding = OPEAEmbedding(
    model_name=sanitize_env(os.getenv("EMBEDDING_MODEL_NAME")),
    model_server=sanitize_env(os.getenv("EMBEDDING_MODEL_SERVER")),
    endpoint=sanitize_env(os.getenv("EMBEDDING_MODEL_SERVER_ENDPOINT")),
    connector=sanitize_env(os.getenv("EMBEDDING_CONNECTOR")),
)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.EMBEDDING,
    endpoint=str(MegaServiceEndpoint.EMBEDDINGS),
    host="0.0.0.0",
    port=int(os.getenv('EMBEDDING_USVC_PORT', default=6000)),
    input_datatype=Union[TextDoc, TextDocList],
    output_datatype=Union[EmbedDoc, EmbedDocList],
    validate_methods=[opea_embedding.validate_method]
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
def process(input: Union[TextDoc, TextDocList]) -> Union[EmbedDoc, EmbedDocList]:
    """
    Process the input document using the OPEAEmbedding.

    Args:
        input (Union[TextDoc, TextDocList]): The input document to be processed.
    """
    start = time.time()
    logger.debug(f"Received input: {input}")

    try:
        # Pass the input to the 'run' method of the microservice instance
        res = opea_embedding.run(input)

    except ValueError as e:
        logger.exception(f"An internal error occurred while processing: {str(e)}")
        raise HTTPException(status_code=400,
                            detail=f"An internal error occurred while processing: {str(e)}"
        )
    except requests.exceptions.HTTPError as e:
        if hasattr(e.response, "status_code") and e.response.status_code == 413:
            raise HTTPException(status_code=413, detail=f"Input text is too long. Provide a valid input text. Error: {ast.literal_eval(e.response.text)['error']}")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=ast.literal_eval(e.response.text)['error'])
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

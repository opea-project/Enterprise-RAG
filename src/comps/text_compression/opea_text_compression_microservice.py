# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from aiohttp.client_exceptions import ClientResponseError
from asyncio import TimeoutError
from dotenv import load_dotenv
from fastapi import HTTPException
from requests.exceptions import HTTPError, RequestException, Timeout

from comps import (
    MegaServiceEndpoint,
    TextSplitterInput,
    TextCompressionInput,
    ServiceType,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    sanitize_env
)
from comps.text_compression.utils.opea_text_compression import OPEATextCompressor

# Define the unique service name for the microservice
USVC_NAME='opea_service@text_compression'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEATextCompressor class with environment variables.
opea_token_compressor = OPEATextCompressor(default_techniques=sanitize_env(os.getenv("DEFAULT_TEXT_COMPRESSION_METHODS")))

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TEXT_COMPRESSION,
    endpoint=str(MegaServiceEndpoint.TEXT_COMPRESSION),
    host='0.0.0.0',
    port=int(os.getenv('TEXT_COMPRESSION_USVC_PORT', default=9397)),
    input_datatype=TextCompressionInput,
    output_datatype=TextSplitterInput,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def invoke(input: TextCompressionInput) -> TextSplitterInput:
    """
    Process the input text through token compression.

    Args:
        input (InputText): The input containing text documents to be compressed.
            - loaded_docs: DocList[TextDoc] containing documents to compress
            - metadata: Optional dict with compression configuration

    Returns:
        CompressedText: The compressed text documents.
            - compressed_docs: DocList[TextDoc] containing compressed documents
    """
    try:
        doc_count = len(input.loaded_docs) if input.loaded_docs else 0
        logger.info(f"Received compression request with {doc_count} documents")
        start_time = time.time()

        # Extract compression parameters
        compression_techniques = input.compression_techniques

        if not input.loaded_docs or len(input.loaded_docs) == 0:
            logger.warning("No documents provided for compression")
            return TextSplitterInput(loaded_docs=[])

        # Call the token compressor to compress the documents
        compressed_docs = await opea_token_compressor.compress_docs(
            docs=input.loaded_docs,
            techniques=compression_techniques,
        )
        processing_time = time.time() - start_time

        # Calculate overall compression stats
        total_original = sum(len(doc.text) for doc in input.loaded_docs) if input.loaded_docs else 0
        total_compressed = sum(len(doc.text) for doc in compressed_docs) if compressed_docs else 0
        compression_ratio = total_compressed / total_original if total_original > 0 else 1.0

        logger.info(f"Compression completed in {processing_time:.2f}s. "
                  f"Reduced from {total_original} to {total_compressed} characters "
                  f"({compression_ratio:.2%} of original)")

        return TextSplitterInput(loaded_docs=compressed_docs)

    except (ClientResponseError, HTTPError) as e:
        logger.exception(f"HTTP error during compression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error from compression service: {str(e)}")
    except Timeout:
        logger.exception("Timeout while calling compression service")
        raise HTTPException(status_code=504, detail="Compression service timed out")
    except TimeoutError:
        logger.exception("Async timeout while calling compression service")
        raise HTTPException(status_code=504, detail="Compression service timed out")
    except RequestException as e:
        logger.exception(f"Request error during compression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to compression service: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error during compression: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")

if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")

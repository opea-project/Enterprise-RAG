# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from concurrent.futures import ProcessPoolExecutor
import os
import time

from urllib3.exceptions import MaxRetryError
from dotenv import load_dotenv
from utils import opea_textsplitter
from fastapi import HTTPException
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.utils.utils import sanitize_env
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import TextSplitterInput, TextDocList
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_text_splitter'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEATextSplitter class with environment variables.
# OPEATextSplitter is a singleton so we initialize it with the environment variables.
# Next, data splitter calls can be overriden with the input parameters if passed.
def run_splitter(loaded_docs, chunk_size, chunk_overlap, use_semantic_chunking):
    opea_splitter = opea_textsplitter.OPEATextSplitter(
        chunk_size=int(sanitize_env(os.getenv("CHUNK_SIZE"))),
        chunk_overlap=int(sanitize_env(os.getenv("CHUNK_OVERLAP"))),
        use_semantic_chunking=(sanitize_env(os.getenv("USE_SEMANTIC_CHUNKING")).lower() == "true")
    )
    textdocs = opea_splitter.split_docs(
        loaded_docs=loaded_docs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        use_semantic_chunking=use_semantic_chunking
    )
    return textdocs

# Process Pool Executor was introduced due to API being unresponsive while computing non-io tasks.
# Originally, async functions are run in event loop which means that they block the server thread
# thus making it unresponsive for other requests - mainly health_check - which then might cause
# some issues on k8s deployments, showing the pod as not ready by failing the liveness probe.
# While moving it to sync function fixed that issue this meant that it would run in a separate
# thread but was instead slower due to not using async io calls. The resolution is to run it
# as an async function for io improvement, but spawn a separate process for heavy CPU usage calls.
# Setting max_workers to 1 ensures that the CPU heavy calls are not overutilizing the pod resources.
# https://github.com/fastapi/fastapi/issues/3725#issuecomment-902629033
# https://luis-sena.medium.com/how-to-optimize-fastapi-for-ml-model-serving-6f75fb9e040d

pool = ProcessPoolExecutor(max_workers=1)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TEXT_SPLITTER,
    endpoint=str(MegaServiceEndpoint.TEXT_SPLITTER),
    host="0.0.0.0",
    port=int(os.getenv('TEXT_SPLITTER_USVC_PORT', default=9399)),
    input_datatype=TextSplitterInput,
    output_datatype=TextDocList,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: TextSplitterInput) -> TextDocList:
    start = time.time()

    loaded_docs = input.loaded_docs

    chunk_size = int(sanitize_env(str(input.chunk_size) if input.chunk_size else os.getenv("CHUNK_SIZE")))
    chunk_overlap = int(sanitize_env(str(input.chunk_overlap) if input.chunk_overlap else os.getenv("CHUNK_OVERLAP")))
    use_semantic_chunking = sanitize_env(str(input.use_semantic_chunking) if input.use_semantic_chunking is not None else os.getenv("USE_SEMANTIC_CHUNKING")).lower() == "true"

    logger.debug(f"Dataprep loaded docs: {loaded_docs}")

    textdocs = None
    loop = asyncio.get_event_loop()
    try:
        textdocs = await loop.run_in_executor(pool, run_splitter, loaded_docs, chunk_size, chunk_overlap, use_semantic_chunking)
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=f"An internal error occurred while processing: {str(e)}")
    except MaxRetryError as e:
        logger.exception(e)
        raise HTTPException(status_code=503, detail=f"Could not connect to remote server: {str(e)}")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing: {str(e)}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return TextDocList(docs=textdocs)


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")

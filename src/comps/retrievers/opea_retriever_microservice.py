# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.utils.utils import sanitize_env
from utils import opea_retriever
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import EmbedDoc, EmbedDocList, SearchedDoc
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_retriever'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEARetriever class with environment variables.

retriever = opea_retriever.OPEARetriever(
    vector_store=sanitize_env(os.getenv("VECTOR_STORE"))
)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.RETRIEVER,
    endpoint=str(MegaServiceEndpoint.RETRIEVAL),
    host="0.0.0.0",
    port=int(os.getenv('RETRIEVER_USVC_PORT', default=6620)),
    input_datatype=Union[EmbedDoc, EmbedDocList],
    output_datatype=SearchedDoc,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: Union[EmbedDoc, EmbedDocList], request: Request) -> SearchedDoc:
    start = time.time()

    search_detail = retriever.filter_expression_for_rbac(request)
    vector = []
    if isinstance(input, EmbedDocList):
        logger.warning("Only one document is allowed for retrieval. Using the first document.")
        vector = input.docs[0] # EmbedDocList[0]
    else:
        vector = input # EmbedDoc

    logger.info(f"Retrieving documents for input: {vector.text}. K={vector.k}, Search Type={vector.search_type}")

    result_vectors = None
    try:
        if (sanitize_env(os.getenv("USE_HIERARCHICAL_INDICES")).lower() == "true"):
            k_summaries = int(sanitize_env(os.getenv("K_SUMMARIES")))
            k_chunks = int(sanitize_env(os.getenv("K_CHUNKS")))
            result_vectors = await retriever.hierarchical_retrieve(vector, k_summaries, k_chunks, search_by=search_detail)
        else:
            result_vectors = await retriever.retrieve(input=vector, search_by=search_detail)
    except ValueError as e:
        logger.exception(f"A ValueError occured while validating the input in retriever: {str(e)}")
        raise HTTPException(status_code=400,
                            detail=f"A ValueError occured while validating the input in retriever: {str(e)}"
        )
    except NotImplementedError as e:
        logger.exception(f"A NotImplementedError occured in retriever: {str(e)}")
        raise HTTPException(status_code=501,
                            detail=f"A NotImplementedError occured in retriever: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"An Error occured while retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An Error while retrieving documents. {e}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    logger.info(f"Retrieved {len(result_vectors.retrieved_docs)} documents in {time.time() - start} seconds.")

    for doc in result_vectors.retrieved_docs:
        if 'file_id' in doc.metadata:
            logger.debug(f"Score: {doc.metadata['vector_distance']} - File: {doc.metadata['file_id']} - Text: {doc.text[0:32]}...")

        if 'link_id' in doc.metadata:
            logger.debug(f"Score: {doc.metadata['vector_distance']} - Link: {doc.metadata['link_id']} - Text: {doc.text[0:32]}...")

    result_vectors.conversation_history = input.conversation_history
    return result_vectors


if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()

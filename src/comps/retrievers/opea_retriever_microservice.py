# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union
from dotenv import load_dotenv
from fastapi import HTTPException
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
def process(input: Union[EmbedDoc, EmbedDocList]) -> SearchedDoc:
    start = time.time()

    vector = []
    if isinstance(input, EmbedDocList): # only one doc is allowed
        vector = input.docs[0] # EmbedDocList[0]
    else:
        vector = input # EmbedDoc

    result_vectors = None
    try:
        result_vectors = retriever.retrieve(vector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while retrieving documents. {e}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return result_vectors


if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()

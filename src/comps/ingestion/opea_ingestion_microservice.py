# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from dotenv import load_dotenv
from fastapi import HTTPException
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.utils.utils import sanitize_env
from utils import opea_ingestion
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import EmbedDocList
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict


# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_ingestion'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEAIngestion class with environment variables.
ingestion = opea_ingestion.OPEAIngestion(
    vector_store=sanitize_env(os.getenv("VECTOR_STORE"))
)

@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.INGESTION,
    endpoint=str(MegaServiceEndpoint.INGEST),
    host="0.0.0.0",
    port=int(os.getenv('INGESTION_USVC_PORT', default=6120)),
    input_datatype=EmbedDocList,
    output_datatype=EmbedDocList,
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
def process(input: EmbedDocList) -> EmbedDocList:
    start = time.time()
    
    embed_vector = None
    try:
        embed_vector = ingestion.ingest(input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while ingesting documents. {e}")

    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return embed_vector


if __name__ == "__main__":
    opea_microservices[USVC_NAME].start()

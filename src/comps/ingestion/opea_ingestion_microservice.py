# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from utils import opea_ingestion
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import EmbedDocList
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

import logging
import os

def start_ingestion_service(opea_ingestion: opea_ingestion.OPEAIngestion, opea_microservice_name: str):
    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.INGESTION,
        endpoint=str(MegaServiceEndpoint.INGEST),
        host="0.0.0.0",
        port=6120,
        input_datatype=EmbedDocList,
        output_datatype=EmbedDocList,
    )
    @register_statistics(names=[opea_microservice_name])
    def ingest(input: EmbedDocList) -> EmbedDocList:
        start = time.time()
        embed_vector = opea_ingestion.ingest(input)
        statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)
        return embed_vector

    opea_microservices[opea_microservice_name].start()

if __name__ == "__main__":
    try:
        ingestion = opea_ingestion.OPEAIngestion(
            vector_store=os.getenv("VECTOR_STORE", "redis")
        )

        opea_microservice_name = "opea_service@opea_ingestion"
        start_ingestion_service(ingestion, opea_microservice_name)
    except Exception as e:
        logging.exception(f"Error initializing OPEAIngestion: {e}")

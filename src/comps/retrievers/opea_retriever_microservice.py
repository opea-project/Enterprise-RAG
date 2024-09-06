# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from utils import opea_retriever
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import EmbedDocList, SearchedDoc
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

import logging
import os

def start_ingestion_service(opea_retriever: opea_retriever.OPEARetriever, opea_microservice_name: str):
    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.RETRIEVER,
        endpoint=str(MegaServiceEndpoint.RETRIEVAL),
        host="0.0.0.0",
        port=6620,
        input_datatype=EmbedDocList,
        output_datatype=SearchedDoc,
    )
    @register_statistics(names=[opea_microservice_name])
    def retrieve(input: EmbedDocList) -> SearchedDoc:
        start = time.time()
        vector = []

        # only one doc is allowed
        if not isinstance(input, (list, tuple)):
            vector = input.docs # EmbedDoc
        else:
            vector = input.docs[0] # List[EmbedDoc][0]

        result_vectors = opea_retriever.retrieve(vector)
        statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)
        return result_vectors

    opea_microservices[opea_microservice_name].start()

if __name__ == "__main__":
    try:
        retriever = opea_retriever.OPEARetriever(
            vector_store=os.getenv("VECTOR_STORE", "redis")
        )
        opea_microservice_name = "opea_service@opea_retriever"
        start_ingestion_service(retriever, opea_microservice_name)
    except Exception as e:
        logging.exception(f"Error initializing OPEARetriever: {e}")

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from fastapi import HTTPException
from comps.cores.proto.docarray import EmbedDocList, TextDocList
from utils import opea_embedding
from comps import (
    EmbedDoc,
    ServiceType,
    MegaServiceEndpoint,
    change_opea_logger_level,
    get_opea_logger,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


# TODO: Find common way of starting the refactored microservices
def start_embedding_service(opea_embedding: opea_embedding.OPEAEmbedding, opea_microservice_name: str):
    """Create the embedding service with the given OPEAEmbedding instance.

    Args:
        opea_embedding (embedding_utils.OPEAEmbedding): An instance of OPEAEmbedding class.
        opea_microservice_name (str): The name of the microservice.
    """

    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.EMBEDDING,
        endpoint=str(MegaServiceEndpoint.EMBEDDINGS),
        host="0.0.0.0",
        port=6000,
        input_datatype=TextDocList,
        output_datatype=EmbedDocList,
    )
    @register_statistics(names=[opea_microservice_name])
    def embedding(input: TextDocList) -> EmbedDocList:
        start = time.time()
        docs = []
        docs_to_parse = input.docs

        if not isinstance(docs_to_parse, (list, tuple)):
            docs_to_parse = [docs_to_parse]

        for doc in docs_to_parse:
            if doc.text.strip() == "":
                continue

            embed_vector = opea_embedding.embed_query(doc.text)
            res = EmbedDoc(text=doc.text, embedding=embed_vector, metadata=doc.metadata)
            docs.append(res)

        if len(docs) == 0:
            raise HTTPException(status_code=400, detail="Input text is empty. Provide a valid input text.")

        statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)        
        
        if not isinstance(input.docs, (list, tuple)):
            return EmbedDocList(docs=docs[0]) # return TextDoc
        else:
            return EmbedDocList(docs=docs) # return List[TextDoc]

    opea_microservices[opea_microservice_name].start()


if __name__ == "__main__":
    log_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
    change_opea_logger_level(logger, log_level)

    embedding = opea_embedding.OPEAEmbedding(
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "bge-large-en-v1.5"),
        model_server=os.getenv("EMBEDDING_MODEL_SERVER", "tei"),
        framework=os.getenv("FRAMEWORK", "langchain"),
        endpoint=os.getenv("EMBEDDING_MODEL_SERVER_ENDPOINT", "http://localhost:8090")
    )

    opea_microservice_name = "opea_service@opea_embedding"
    start_embedding_service(embedding, opea_microservice_name)
    logger.info(f"Started OPEA embedding microservice: {opea_microservice_name}")

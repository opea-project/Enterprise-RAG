# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.docarray import EmbedDocList

from comps.vectorstores.utils.opea_vectorstore import OPEAVectorStore

class OPEAIngestion:
    """
    Singleton class for managing ingestion into vector stores via microservice API calls.
    """

    _instance = None

    def __new__(cls, vector_store: str):
        if cls._instance is None:
            cls._instance = super(OPEAIngestion, cls).__new__(cls)
            cls._instance._initialize(vector_store)
        return cls._instance

    def _initialize(self, vector_store: str):
        self.vector_store = OPEAVectorStore(vector_store)

    def ingest(self, input: EmbedDocList) -> EmbedDocList:
        docs = input.docs
        if not isinstance(input.docs, (list, tuple)):
            docs = [input.docs] # [EmbedDoc]

        self.vector_store.add_texts(input=docs)
        return input

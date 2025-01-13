# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from comps.vectorstores.impl.milvus.opea_milvus import OPEAMilvus
from comps.vectorstores.utils.wrappers.wrapper import VectorStoreWrapper

class MilvusVectorStore(VectorStoreWrapper):
    """
    A wrapper class for interacting with a Milvus vector store.
    Args:
        batch_size (int): The batch size for vector operations. Defaults to 32.
        index_name (str): The name of the index. Defaults to "default_index".
    Attributes:
        client (OPEAMilvus): The Milvus client instance.
    """
    def __init__(self, batch_size: int = 32, index_name: str = "default_index"):
        """
        Initializes a new instance of the MilvusVectorStore class.
        Args:
            batch_size (int): The batch size for vector operations. Defaults to 32.
            index_name (str): The name of the index. Defaults to "default_index".
        """
        url = MilvusVectorStore.format_url_from_env()
        self.batch_size = batch_size
        self.client = self._client(url, index_name)
        
    def _client(self, url, index_name):
        return OPEAMilvus(url=url, index_name=index_name)

    @staticmethod
    def format_url_from_env():
        """
        Formats the Milvus URL based on the environment variables.
        Returns:
            str: The formatted Milvus URL.
        """
        milvus_url = os.getenv("MILVUS_URL", None)
        if milvus_url:
            return milvus_url
        else:
            host = os.getenv("MILVUS_HOST", 'localhost')
            port = int(os.getenv("MILVUS_PORT", 19530))

            schema = "http"
            return f"{schema}://{host}:{port}/"

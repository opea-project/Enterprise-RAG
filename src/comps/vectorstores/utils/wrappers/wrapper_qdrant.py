# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from comps.vectorstores.impl.qdrant.opea_qdrant import OPEAQdrant
from comps.vectorstores.utils.wrappers.wrapper import VectorStoreWrapper

class QdrantVectorStore(VectorStoreWrapper):
    """
    A wrapper class for interacting with the Qdrant vector store.
    Args:
        batch_size (int, optional): The batch size for vector operations. Defaults to 32.
        index_name (str, optional): The name of the index. Defaults to "default_index".
    Attributes:
        client (OPEAQdrant): The client object for interacting with the Qdrant server.
    Methods:
        format_url_from_env(): A static method to format the Qdrant URL from environment variables.
    """
    def __init__(self, batch_size: int = 32, index_name: str = "default_index"):
        """
        Initializes a new instance of the QdrantVectorStore class.
        Args:
            batch_size (int, optional): The batch size for vector operations. Defaults to 32.
            index_name (str, optional): The name of the index. Defaults to "default_index".
        """
        url = QdrantVectorStore.format_url_from_env()
        self.batch_size = batch_size
        self.client = self._client(url, index_name)
        
    def _client(self, url, index_name):
        return OPEAQdrant(url=url, index_name=index_name)

    @staticmethod
    def format_url_from_env():
        """
        Formats the Qdrant URL from environment variables.
        Returns:
            str: The formatted Qdrant URL.
        """
        qdrant_url = os.getenv("QDRANT_URL", None)
        if qdrant_url:
            return qdrant_url
        else:
            host = os.getenv("QDRANT_HOST", 'localhost')
            port = int(os.getenv("QDRANT_PORT", 6333))

            schema = "http"
            return f"{schema}://{host}:{port}/"

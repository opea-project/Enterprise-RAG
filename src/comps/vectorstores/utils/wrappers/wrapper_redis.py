# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from comps.vectorstores.impl.redis.opea_redis import OPEARedis
from comps.vectorstores.utils.wrappers.wrapper import VectorStoreWrapper
from comps.cores.utils.utils import get_boolean_env_var

class RedisVectorStore(VectorStoreWrapper):
    """
    A wrapper class for Redis vector store.
    Args:
        batch_size (int): The batch size for vector operations. Defaults to 32.
        index_name (str): The name of the index. Defaults to "default_index".
    Attributes:
        batch_size (int): The batch size for vector operations.
        client (OPEARedis): The Redis client for vector operations.
    Methods:
        format_url_from_env(): Formats the Redis URL based on environment variables.
    """
    def __init__(self, batch_size: int = 32, index_name: str = "default_index"):
        """
        Initializes a RedisVectorStore object.
        Args:
            batch_size (int): The batch size for vector operations. Defaults to 32.
            index_name (str): The name of the index. Defaults to "default_index".
        """
        url = RedisVectorStore.format_url_from_env()
        self.batch_size = batch_size
        self.client = self._client(url, index_name)
        
    def _client(self, url, index_name):
        return OPEARedis(url=url, index_name=index_name)

    @staticmethod
    def format_url_from_env():
        """
        Formats the Redis URL based on environment variables.
        Returns:
            str: The formatted Redis URL.
        """
        redis_url = os.getenv("REDIS_URL", None)
        if redis_url:
            return redis_url
        else:
            host = os.getenv("REDIS_HOST", 'localhost')
            port = int(os.getenv("REDIS_PORT", 6379))

            using_ssl = get_boolean_env_var("REDIS_SSL", False)
            schema = "rediss" if using_ssl else "redis"

            username = os.getenv("REDIS_USERNAME", "default")
            password = os.getenv("REDIS_PASSWORD", None)
            credentials = "" if password is None else f"{username}:{password}@"

            return f"{schema}://{credentials}{host}:{port}/"

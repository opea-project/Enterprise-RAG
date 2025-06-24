from abc import ABC
import os
from typing import Any
import jwt
import json
from redis import Redis
from minio.error import S3Error
from app.utils import get_local_minio_client, get_local_minio_client_using_token_credentials, filtered_list_bucket
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

if os.getenv("OPEA_LOGGER_LEVEL", "INFO").upper() == "DEBUG":
    import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1

# jwt token should consist of:
# {
#   "access_token": "x",
#   "expires_in": 300,
#   "refresh_expires_in": 1800,
#   "refresh_token": "xxxx",
#   "token_type": "Bearer",
#   "id_token": "xxxx",
#   "not-before-policy": 0,
#   "session_state": "6257dee0-c34a-4e3e-bbb4-494bf98aec74",
#   "scope": "openid email profile"
# }

class AbstractRBAC(ABC):
    def __init__(self, rbac_type: str):
        self.rbac_type = rbac_type
        self.client = get_local_minio_client()

    def get_user_id(self, jwt_token):
        token = jwt.decode(jwt_token, options={"verify_signature": False})
        return token.get('sub')

    def check_bucket_for_read_access(self, client, bucket_name):
        files = []
        try:
            objects = client.list_objects(bucket_name)
            files = list(objects)  # Convert iterator to list for safe iteration
        except S3Error as e:
            logger.error(f"S3Error on bucket {bucket_name}")
            logger.error(f"\t{e}")
            return False

        count_files = len(files)
        logger.debug(f"Bucket {bucket_name} has {count_files} files")

        if files is None or count_files == 0:
            logger.debug(f"Bucket {bucket_name} is empty, skipping")
            raise ValueError(f"Bucket {bucket_name} is empty")

        for file in files: # iterate over files but it will use only the first file
            try:
                head = client.stat_object(bucket_name, file.object_name)
                if head and head.size > 0:
                    logger.debug(f"\tBucket {bucket_name} is readable")
                    return True
                else:
                    break
            except Exception as e:
                logger.error(f"\tError accessing file {file.object_name} in bucket {bucket_name}: {e}")
                break

        logger.debug(f"\tNo readable files found in bucket {bucket_name}, skipping.")
        return False

    def get_buckets(self):
        return []

class StaticRBAC(AbstractRBAC):
    def __init__(self, jwt_token: str):
        super().__init__('STATIC')
        self.jwt_token = jwt_token

    def get_buckets(self):
        # Config should be either a list or a dictionary
        # If it's a list, return it as is
        # config = ['bucket1', 'bucket2', 'bucket3']
        # If it's a dictionary, return the list of buckets for the user_id
        # config = { 'user_id_1': ['bucket1', 'bucket2'], 'user_id_2': ['bucket3'] }

        config = os.getenv("VECTOR_DB_RBAC_STATIC_CONFIG", None)

        if config is None or config == "":
            logger.debug("No static RBAC configuration found. Returning empty list.")
            return []

        try:
            config = json.loads(config)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding static RBAC JSON configuration: {e}")
            return []

        if isinstance(config, list):
            logger.debug("Static RBAC configuration is a list.")
            return config

        if isinstance(config, dict):
            logger.debug("Static RBAC configuration is a dictionary.")
            user_id = self.get_user_id(self.jwt_token['access_token'])
            return config.get(user_id, [])

        logger.debug("Static RBAC configuration is neither a list nor a dictionary. Returning empty list.")
        return []

class AlwaysRBAC(AbstractRBAC):
    def __init__(self, jwt_token: str):
        super().__init__('CURRENT')
        self.jwt_token = jwt_token
        self.token_client = get_local_minio_client_using_token_credentials(self.jwt_token)

    def get_buckets(self):
        bucket_list = filtered_list_bucket(self.client)
        bucket_list_with_read_access = []

        logger.debug(f"readable bucket list {len(bucket_list)}")

        for bucket in bucket_list:
            try:
                logger.debug(f"Checking bucket {bucket} for read access")
                read_access = self.check_bucket_for_read_access(self.token_client, bucket)
                if read_access:
                    logger.debug(f"Adding bucket {bucket} to list of readable buckets")
                    bucket_list_with_read_access.append(bucket)
                else:
                    logger.debug(f"Bucket as no read access {bucket}")
            except ValueError as e:
                logger.error(f"Error checking bucket {bucket}: {e}")
                continue

        return bucket_list_with_read_access

class CachedRBAC(AbstractRBAC):
    def __init__(self, jwt_token: str):
        super().__init__('CACHED')
        self.cache = self.get_cache_client()
        self.jwt_token = jwt_token
        self.token_client = get_local_minio_client_using_token_credentials(self.jwt_token)

    def get_cache_client(self):
        return Redis.from_url(os.getenv('CELERY_BROKER_URL'))

    def get_buckets(self):
        bucket_list = filtered_list_bucket(self.client)
        bucket_list_with_read_access = []
        user_id = self.get_user_id(self.jwt_token['access_token'])
        logger.debug(f"readable bucket list {len(bucket_list)}")

        for bucket in bucket_list:
            try:
                logger.debug(f"Checking cached bucket {bucket} for read access")
                read_access = self.get_cached_bucket_read(user_id, bucket, self.cache, self.token_client)
                if read_access:
                    logger.debug(f"Adding bucket {bucket} to list of readable buckets")
                    bucket_list_with_read_access.append(bucket)
                else:
                    logger.debug(f"Bucket as no read access {bucket}")
            except ValueError as e:
                logger.error(f"Error checking bucket {bucket}: {e}")
                continue

        return bucket_list_with_read_access

    def get_cached_bucket_read(self, user_id: str, bucket_name: str, cache: Any, client: Any):
        ttl_seconds = int(os.getenv('VECTOR_DB_RBAC_CACHE_EXPIRATION', "3600"))
        cache_key = f"bucket_read_access:{user_id}:{bucket_name}"

        if not cache.exists(cache_key):
            logger.debug(f"Cache for {cache_key} does not exist. Creating new entry.")
            read_access = self.check_bucket_for_read_access(client, bucket_name)
            if read_access:
                logger.debug(f"Adding bucket {bucket_name} to list of readable buckets")
                cache.setex(cache_key, ttl_seconds, 'OK') # key, ttl, data
                return True
            else:
                logger.debug(f"Bucket {bucket_name} is not readable, skipping")
                return False
        else:
            logger.debug(f"Cache for {cache_key} exists. Retrieving from cache.")
            return True

class NoneRBAC(AbstractRBAC):
    def __init__(self, rbac_type: str):
        super().__init__(rbac_type)

    def get_buckets(self):
        # No RBAC validation, return empty list
        logger.debug("No RBAC validation, returning filtered bucket list.")
        bucket_list = filtered_list_bucket(self.client)
        return bucket_list

class RBACFactory():
    VECTOR_DB_RBAC_VALIDATION_TYPES=["NONE", "ALWAYS", "CACHED", "STATIC"]

    def __new__(cls, rbac_type: str, jwt_token: str = None):
        rbac_type = rbac_type.upper()

        if rbac_type not in RBACFactory.VECTOR_DB_RBAC_VALIDATION_TYPES:
            raise ValueError(f"Invalid RBAC type: {rbac_type}. Must be one of {RBACFactory.VECTOR_DB_RBAC_VALIDATION_TYPES}")

        if rbac_type == 'STATIC':
            logger.debug("Validating bucket permission on every request from static config.")
            return StaticRBAC(jwt_token)
        elif rbac_type == 'ALWAYS':
            logger.debug("Validating bucket permission on every request from storage.")
            return AlwaysRBAC(jwt_token)
        elif rbac_type == 'CACHED':
            logger.debug("Validating bucket permission on every request from cache.")
            return CachedRBAC(jwt_token)
        elif rbac_type == 'NONE':
            logger.debug("Validating bucket permissions by passing filtered bucket list.")
            return NoneRBAC(rbac_type)
        else:
            raise NotImplementedError(f"RBAC type {rbac_type} is not implemented.")

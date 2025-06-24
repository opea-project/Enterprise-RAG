import os
import re
import urllib3
from urllib3 import Retry
from urllib3.util import Timeout
from minio import Minio
from minio.credentials import EnvMinioProvider, WebIdentityProvider
from minio.signer import presign_v4
from datetime import datetime, timedelta
from urllib.parse import urlunsplit
from urllib3.util.url import parse_url

from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

def get_local_minio_client():
    endpoint = os.getenv('EDP_INTERNAL_URL', 'http://edp-minio:9000')
    cert_check = str(os.getenv('EDP_INTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, region, cert_check)

def get_local_minio_client_using_token_credentials(jwt_token, verify=False):
    endpoint = os.getenv('EDP_INTERNAL_URL', 'minio:9000')
    cert_check = str(os.getenv('EDP_EXTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    if jwt_token.get('access_token', None) is None:
        raise ValueError("JWT token does not contain access_token")
    credentials = WebIdentityProvider(
        jwt_provider_func=lambda: jwt_token,
        sts_endpoint=os.getenv('EDP_STS_ENDPOINT', endpoint)
    )
    return get_minio_client(endpoint, region, cert_check, credentials)

def get_remote_minio_client():
    endpoint = os.getenv('EDP_EXTERNAL_URL', 'http://edp-minio:9000')
    cert_check = str(os.getenv('EDP_EXTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, region, cert_check)

def get_http_client(endpoint, cert_check=True):
    from requests.utils import select_proxy, get_environ_proxies
    from requests.exceptions import InvalidProxyURL
    cert_check = str(cert_check).lower() not in ['false', '0', 'f', 'n', 'no']

    endpoint = str(endpoint)
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = f"http://{endpoint}"
    endpoint = parse_url(endpoint)
    proxy = select_proxy(endpoint.url, get_environ_proxies(endpoint.url))

    if endpoint.scheme == 'https' and not cert_check:
        urllib3.disable_warnings() # skip InsecureRequestWarning message 

    timeout_time = timedelta(seconds=30).seconds
    timeout = Timeout(connect=timeout_time, read=timeout_time)
    cert_reqs = 'CERT_REQUIRED' if cert_check else 'CERT_NONE'
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )

    if proxy:
        if not proxy.startswith(('http://', 'https://')):
            proxy = f"http://{proxy}"
        proxy_url = parse_url(proxy)
        if not proxy_url.host:
            raise InvalidProxyURL(
                "Please check proxy URL. It is malformed "
                "and could be missing the host."
            )
        return urllib3.ProxyManager(
            proxy_url.url,
            timeout=timeout,
            cert_reqs=cert_reqs,
            retries=retries
        )
    else:
        return urllib3.PoolManager(
            timeout=timeout,
            cert_reqs=cert_reqs,
            retries=retries
        )

def get_minio_client(endpoint=None, region=None, cert_check=True, credentials=None):
    cert_check = str(cert_check).lower() not in ['false', '0', 'f', 'n', 'no']
    if not credentials:
        credentials = EnvMinioProvider()
    endpoint = parse_url(endpoint)
    http_client = get_http_client(endpoint, cert_check)
    # pass only host and port to minio
    minio = Minio(
        endpoint._replace(scheme=None, path=None, query=None, fragment=None).url,
        credentials=credentials,
        secure=True if endpoint.scheme == 'https' else False,
        region=region,
        http_client=http_client,
        cert_check=cert_check
    )

    return minio


def generate_presigned_url(client, method, bucket_name, object_name, expires = timedelta(days=7), region = 'us-east-1'):
    """
    Generate a presigned URL for accessing an object in an S3 bucket.
    Parameters:
    client (object): The client object that contains the necessary methods and properties for generating the URL.
    method (str): The HTTP method to be used with the presigned URL (e.g., 'GET', 'PUT').
    bucket_name (str): The name of the S3 bucket.
    object_name (str): The name of the object in the S3 bucket.
    region (str, optional): The AWS region where the S3 bucket is located. Defaults to 'us-east-1'.
    Returns:
    str: A presigned URL that can be used to access the specified object in the S3 bucket.
    """

    base_url = client._base_url.build(
        method,
        region,
        bucket_name=bucket_name,
        object_name=object_name,
        query_params={},
    )

    presigned_url = presign_v4(
        method,
        base_url,
        region,
        client._provider.retrieve(),
        datetime.now(),
        int(expires.total_seconds())
    )

    return urlunsplit(presigned_url)

def filtered_list_bucket(client):
    buckets = client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    regex_filter = str(os.getenv('BUCKET_NAME_REGEX_FILTER', ''))
    if len(regex_filter) > 0:
        bucket_names = [name for name in bucket_names if re.match(regex_filter, name)]
        logger.debug(f"Displaying {len(bucket_names)}/{len(buckets)} buckets after applying regex filter: {regex_filter}")

    return bucket_names

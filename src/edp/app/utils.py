import os

import urllib3
from urllib3 import Retry
from urllib3.util import Timeout
from minio import Minio
from minio.credentials import EnvMinioProvider
from minio.signer import presign_v4
from datetime import datetime, timedelta
from urllib.parse import urlunsplit
from urllib3.util.url import parse_url

def get_local_minio_client():
    endpoint = os.getenv('EDP_INTERNAL_URL', 'minio:9000')
    cert_check = str(os.getenv('EDP_INTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, region, cert_check)

def get_remote_minio_client():
    endpoint = os.getenv('EDP_EXTERNAL_URL', 'minio:9000')
    cert_check = str(os.getenv('EDP_EXTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, region, cert_check)

def get_http_client(endpoint, cert_check=True):
    from requests.utils import select_proxy, get_environ_proxies, prepend_scheme_if_needed
    from requests.exceptions import InvalidProxyURL
    cert_check = str(cert_check).lower() not in ['false', '0', 'f', 'n', 'no']

    endpoint = str(endpoint)
    endpoint = prepend_scheme_if_needed(endpoint, "http")
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
        proxy = prepend_scheme_if_needed(proxy, "http")
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

def get_minio_client(endpoint=None, region=None, cert_check=True):
    cert_check = str(cert_check).lower() not in ['false', '0', 'f', 'n', 'no']

    endpoint = parse_url(endpoint)
    http_client = get_http_client(endpoint, cert_check)
    # pass only host and port to minio
    minio = Minio(
        endpoint._replace(scheme=None, path=None, query=None, fragment=None).url,
        credentials=EnvMinioProvider(),
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

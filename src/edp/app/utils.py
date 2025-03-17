import os

import urllib3
from urllib3 import Retry
from urllib3.util import Timeout
from minio import Minio
from minio.credentials import EnvMinioProvider
from minio.signer import presign_v4
from datetime import datetime, timedelta
from urllib.parse import urlunsplit

def get_local_minio_client():
    endpoint = os.getenv('EDP_INTERNAL_URL', 'minio:9000')
    url_secure = str(os.getenv('EDP_INTERNAL_SECURE', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, url_secure, region)

def get_remote_minio_client():
    endpoint = os.getenv('EDP_EXTERNAL_URL', 'minio:9000')
    url_secure = str(os.getenv('EDP_EXTERNAL_SECURE', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')
    return get_minio_client(endpoint, url_secure, region)

def get_minio_client(endpoint=None, url_secure=None, region=None):
    is_secure = str(url_secure).lower() not in ['false', '0', 'f', 'n', 'no']

    http_client = None
    proxy = None

    if is_secure:
        proxy = os.getenv('https_proxy', None)
    else:
        proxy = os.getenv('http_proxy', None)

    if is_secure and proxy is not None and proxy != '':
        if not proxy.startswith(('http://', 'https://')):
            proxy = ('https://' if is_secure else 'http://') + proxy
        cert_check = True
        timeout = timedelta(minutes=1).seconds
        http_client=urllib3.ProxyManager(
            proxy,
            timeout=Timeout(connect=timeout, read=timeout),
            cert_reqs='CERT_REQUIRED' if cert_check else 'CERT_NONE',
            retries=Retry(
                total=5,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504]
            )
        )

    # pass only host and port to minio
    http_prefix='http://'
    https_prefix='https://'
    endpoint = endpoint.rstrip('/')
    if endpoint.startswith(http_prefix):
        endpoint = endpoint[len(http_prefix):]
    if endpoint.startswith(https_prefix):
        endpoint = endpoint[len(https_prefix):]

    minio = Minio(
        endpoint,
        credentials=EnvMinioProvider(),
        secure=is_secure,
        region=region,
        http_client=http_client
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

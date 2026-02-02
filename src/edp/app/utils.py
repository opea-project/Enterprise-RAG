import os
import re
import urllib3
from urllib3 import Retry
from urllib3.util import Timeout
from minio import Minio
from minio.credentials import EnvMinioProvider, WebIdentityProvider, StaticProvider
from minio.signer import presign_v4
from datetime import datetime, timedelta
from urllib.parse import urlunsplit
from urllib3.util.url import parse_url

from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

class BearerTokenHttpClient(urllib3.PoolManager):
    """
    Custom HTTP client that injects Bearer token into all requests.
    """

    def __init__(self, bearer_token: str, base_client: urllib3.PoolManager):
        self._bearer_token = bearer_token # The OIDC access token to use for authentication
        self._base_client = base_client

        super().__init__()

    def urlopen(self, method, url, body=None, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['Authorization'] = f'Bearer {self._bearer_token}'
        response = self._base_client.urlopen(method, url, body=body, headers=headers, **kwargs)
        return response

    def clear(self):
        if hasattr(self._base_client, 'clear'):
            self._base_client.clear()

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
        sts_endpoint=os.getenv('EDP_STS_ENDPOINT', endpoint),
	    http_client=get_http_client(endpoint, cert_check)
    )
    return get_minio_client(endpoint, region, cert_check, credentials)


def get_seaweedfs_client_using_bearer_token(jwt_token):
    """
    Create a MinIO-compatible client for SeaweedFS using Bearer token auth.
    SeaweedFS Advanced IAM validates OIDC tokens directly without requiring
    STS AssumeRoleWithWebIdentity calls. This function creates a client that
    injects the Bearer token into all requests.
    """

    endpoint = os.getenv('EDP_INTERNAL_URL', 'seaweedfs-s3:8333')
    cert_check = str(os.getenv('EDP_INTERNAL_CERT_VERIFY', True))
    region = os.getenv('EDP_BASE_REGION', 'us-east-1')

    access_token = jwt_token.get('access_token')
    if access_token is None:
        raise ValueError("JWT token does not contain access_token")

    # use dummy keys (required for minio), real auth done via Bearer header
    credentials = StaticProvider("access-key-dummy", "secret-key-dummy")

    # Parse endpoint and create Bearer-injecting HTTP client
    cert_check_bool = str(cert_check).lower() not in ['false', '0', 'f', 'n', 'no']
    parsed_endpoint = parse_url(endpoint)

    http_client = BearerTokenHttpClient(access_token, get_http_client(parsed_endpoint, cert_check_bool))

    # Create MinIO client with custom HTTP client
    minio_endpoint = parsed_endpoint._replace(scheme=None, path=None, query=None, fragment=None).url

    minio = Minio(
        minio_endpoint,
        credentials=credentials,
        secure=True if parsed_endpoint.scheme == 'https' else False,
        region=region,
        http_client=http_client,
        cert_check=cert_check_bool
    )

    return minio

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


def generate_presigned_url(client, method, bucket_name, object_name, expires = timedelta(days=7), region = 'us-east-1', credentials=None):
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

    query_params = {}

    # If credentials are provided from WebIdentityProvider,
    # session token has to be added to query params.
    # Otherwise, MinIO will return InvalidTokenId error due to validation in following:
    # https://github.com/minio/minio/blob/7ced9663e6a791fef9dc6be798ff24cda9c730ac/cmd/auth-handler.go#L278
    if credentials and credentials._session_token:
        query_params['X-Amz-Security-Token'] = credentials._session_token

    # This retrieves credentials from client if not passed
    if credentials is None:
        credentials = client._provider.retrieve()

    base_url = client._base_url.build(
        method,
        region,
        bucket_name=bucket_name,
        object_name=object_name,
        query_params=query_params
    )

    presigned_url = presign_v4(
        method,
        base_url,
        region,
        credentials,
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

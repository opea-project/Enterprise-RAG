import os
from minio import Minio
from minio.credentials import EnvMinioProvider
from minio.signer import presign_v4
from datetime import datetime, timedelta
from urllib.parse import urlunsplit

def generate_presigned_url(method, bucket_name, object_name, expires = timedelta(days=7), region = 'us-east-1'):
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

    minio = Minio(
        os.getenv('MINIO_EXTERNAL_URL', 's3.erag.com'),
        credentials=EnvMinioProvider(),
        secure=True
    )

    base_url = minio._base_url.build(
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
        minio._provider.retrieve(),
        datetime.now(),
        int(expires.total_seconds())
    )

    return urlunsplit(presigned_url)

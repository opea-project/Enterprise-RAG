# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import List, Union
import uuid
import validators
import uvicorn
from datetime import timedelta
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from minio.error import S3Error
from urllib.parse import unquote_plus
from app.utils import generate_presigned_url, get_local_minio_client, get_remote_minio_client
from app.database import get_db, init_db
from app.models import FileResponse, FileStatus, LinkRequest, LinkResponse, LinkStatus, PresignedRequest, MinioEventData, S3EventData, PresignedResponse
from app.tasks import process_file_task, delete_file_task, process_link_task, delete_link_task, celery
from celery.result import AsyncResult
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from sqlalchemy.sql import functions
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import Response

app = FastAPI()

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "./.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

minio_external = get_remote_minio_client()
minio_internal = get_local_minio_client()

@app.get('/health')
def health_check():
    """
    Perform a health check of the application.
    Returns:
        Response: A JSON response with a message indicating the health status.
    """
    return JSONResponse(content={'message': 'OK'})

@app.get("/metrics")
async def metrics():
    with get_db() as db:
        registry = CollectorRegistry()

        files = db.query(FileStatus).filter(FileStatus.marked_for_deletion == False).count() # noqa: E712
        files_for_deletion = db.query(FileStatus).filter(FileStatus.marked_for_deletion == True).count() # noqa: E712
        links = db.query(LinkStatus).filter(LinkStatus.marked_for_deletion == False).count() # noqa: E712
        links_for_deletion = db.query(LinkStatus).filter(LinkStatus.marked_for_deletion == True).count() # noqa: E712
        files_chunks = db.query(
            functions.sum(FileStatus.chunks_total).label('chunks_total_sum'),
            functions.sum(FileStatus.chunks_processed).label('chunks_processed_sum')
        ).filter(FileStatus.marked_for_deletion == False).one() # noqa: E712
        links_chunks = db.query(
            functions.sum(LinkStatus.chunks_total).label('chunks_total_sum'),
            functions.sum(LinkStatus.chunks_processed).label('chunks_processed_sum')
        ).filter(LinkStatus.marked_for_deletion == False).one() # noqa: E712
        files_statuses = db.query(
            FileStatus.status,
            functions.count(FileStatus.status).label('status_count')
        ).group_by(FileStatus.status).all()
        files_statuses = dict(files_statuses)
        links_statuses = db.query(
            LinkStatus.status,
            functions.count(LinkStatus.status).label('status_count')
        ).group_by(LinkStatus.status).all()
        links_statuses = dict(links_statuses)

        gauge_files = Gauge(name='edp_files_total', documentation='Total number of files in the database', registry=registry)
        gauge_files.set(files or 0)

        gauge_links = Gauge(name='edp_links_total', documentation='Total number of links in the database', registry=registry)
        gauge_links.set(links or 0)

        gauge_files_for_deletion = Gauge(name='edp_files_for_deletion_total', documentation='Total number of files marked for deletion', registry=registry)
        gauge_files_for_deletion.set(files_for_deletion or 0)

        gauge_links_for_deletion = Gauge(name='edp_links_for_deletion_total', documentation='Total number of links marked for deletion', registry=registry)
        gauge_links_for_deletion.set(links_for_deletion or 0)

        gauge_files_chunks = Gauge(name='edp_files_chunks_total', documentation='Total number of chunks for files', registry=registry)
        gauge_files_chunks.set(files_chunks.chunks_processed_sum or 0)

        gauge_links_chunks = Gauge(name='edp_links_chunks_total', documentation='Total number of chunks for links', registry=registry)
        gauge_links_chunks.set(links_chunks.chunks_processed_sum or 0)

        gauge_total_chunks = Gauge(name='edp_chunks_total', documentation='Total number of chunks', registry=registry)
        gauge_total_chunks.set((files_chunks.chunks_total_sum or 0) + (links_chunks.chunks_total_sum or 0))

        for obj_status in 'uploaded, error, processing, dataprep, dpguard, embedding, ingested, deleting, canceled, blocked'.split(', '):
            file_count = files_statuses.get(obj_status, 0)
            file_gauge = Gauge(name=f'edp_files_{obj_status}_total', documentation=f'Total number of files with status {obj_status}', registry=registry)
            file_gauge.set(file_count)
            link_count = links_statuses.get(obj_status, 0)
            link_gauge = Gauge(name=f'edp_links_{obj_status}_total', documentation=f'Total number of links with status {obj_status}', registry=registry)
            link_gauge.set(link_count)

        celery_inspector = celery.control.inspect()
        reserved = celery_inspector.reserved()
        scheduled = celery_inspector.scheduled()
        active = celery_inspector.active()

        gauge_reserved = Gauge(name='edp_celery_reserved_tasks_total', documentation='Total number of reserved tasks', registry=registry)
        gauge_reserved.set(sum(len(v) for v in reserved.values()) if reserved else 0)
        gauge_scheduled = Gauge(name='edp_celery_scheduled_tasks_total', documentation='Total number of scheduled tasks', registry=registry)
        gauge_scheduled.set(sum(len(v) for v in scheduled.values()) if scheduled else 0)
        gauge_active = Gauge(name='edp_celery_active_tasks_total', documentation='Total number of active tasks', registry=registry)
        gauge_active.set(sum(len(v) for v in active.values()) if active else 0)

        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    data = await request.json()
    logger.error(f"{request.method} {request.url}")
    logger.error(f"{request.headers}")
    logger.error(f"{data}")
    logger.error(f"{exc_str}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logger.error(f"Error within database connection {exc.__class__.__name__}: {exc_str}")
    content = { 'message': 'Error within database connection' }
    return JSONResponse(content=content, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

# -------------- Minio operations ------------


@app.post('/api/presignedUrl')
def presigned_url(input: PresignedRequest, request: Request) -> PresignedResponse:
    """
    Generate a presigned URL for accessing an object in an S3 bucket.
    This function generates a presigned URL for either
    uploading (PUT), downloading (GET) an object from an S3 bucket using MinIO
    or deleting (DELETE) an object from an S3 bucket.
    Returns:
        Response: A JSON response containing the presigned URL or an error message.
    Error Responses:
        400: Missing bucket_name or object_name.
        400: Invalid method.
        400: An error occurred while generating the presigned URL.
    Request JSON Parameters:
        bucket_name (str): The name of the S3 bucket.
        object_name (str): The name of the object in the S3 bucket.
        method (str): The HTTP method for the presigned URL ('PUT', 'GET', 'DELETE').
    Example:
        {
            "bucket_name": "my-bucket",
            "object_name": "my-object",
            "method": "PUT"
        }
    """

    bucket_name = input.bucket_name
    object_name = input.object_name
    method = input.method

    if not bucket_name or not object_name:
        raise HTTPException(status_code=400, detail="Please provide both bucket_name and object_name")

    if method not in ['PUT', 'GET', 'DELETE']:
        raise HTTPException(status_code=400, detail="Invalid method")

    expiry = timedelta(days=1)
    if method == 'DELETE':
        expiry = timedelta(seconds=60)

    region = os.getenv('EDP_BASE_REGION', None)
    try:
        url = generate_presigned_url(minio_external, method, bucket_name, object_name, expiry, region)
        logger.debug(f"Generated presigned url for [{method}] {bucket_name}/{object_name}")
        return PresignedResponse(url=url)
    except S3Error as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail="An error occurred while generating a presigned URL.")

@app.get('/api/list_buckets')
def list_buckets():
    """
    List all buckets in the MinIO storage.
    Returns:
        Response: A JSON response containing a list of buckets.
    """
    bucket_names = filtered_list_bucket(minio_internal)
    return JSONResponse(content={'buckets': bucket_names})

# -------------- Event processing ------------


def add_new_file(bucket_name, object_name, etag, content_type, size):
    """
    Adds a new file to the database and enqueues a file processing job.

    This function first deletes any existing files with the same bucket name and object name.
    Then, it adds a new file entry to the database with the provided metadata and commits the transaction.
    Finally, it enqueues a file processing job and updates the file entry with the task ID and job name.

    Args:
        bucket_name (str): The name of the bucket where the file is stored.
        object_name (str): The name of the object (file) in the bucket.
        etag (str): The entity tag (ETag) of the file.
        content_type (str): The MIME type of the file.
        size (int): The size of the file in bytes.

    Returns:
        FileStatus: The file status object representing the newly added file.

    Raises:
        Exception: If there is an error deleting existing files or committing to the database.
    """
    with get_db() as db:
        try:
            old_files = db.query(FileStatus).filter(FileStatus.bucket_name == bucket_name, FileStatus.object_name == object_name).all()
            for old_file in old_files:
                delete_existing_file(old_file.bucket_name, old_file.object_name)
        except Exception as e:
            logger.error(f"Error deleting existing file: {e}")
            db.rollback()
            raise HTTPException(status_code=400, detail="Error deleting existing file")

        file_status = FileStatus(
            bucket_name=bucket_name,
            object_name=object_name,
            etag=etag,
            content_type=content_type,
            size=size,
            status='uploaded',
            created_at=datetime.now(timezone.utc)
        )
        db.add(file_status)
        db.commit()

        logger.debug(f"Added file {bucket_name}/{object_name} to database with id {file_status.id}")

        try:
            # Save DB and enqueue file processing job
            task = process_file_task.delay(file_id=file_status.id)
            file_status.task_id = task.id
            file_status.job_name = 'file_processing_job'
            db.commit()
            logger.debug(f"File processing task enqueued with id {task.id}")
        except Exception as e:
            logger.error(f"Error committing to database: {e}")
            db.rollback() # rollback only the delay job
        return file_status


def delete_existing_file(bucket_name, object_name):
    """
    Marks an existing file for deletion and schedules a task to delete the file.

    Args:
        bucket_name (str): The name of the bucket where the file is stored.
        object_name (str): The name of the file to be deleted.

    Returns:
        None
    """
    with get_db() as db:
        file_statuses = db.query(FileStatus).filter(FileStatus.bucket_name == bucket_name, FileStatus.object_name == object_name, FileStatus.marked_for_deletion == False).all() # noqa: E712
        if file_statuses:
            for file_status in file_statuses:
                file_status.marked_for_deletion = True
                file_status.status = 'deleting'
                db.commit()
                task = delete_file_task.delay(file_id=file_status.id, countdown=3) # delay by 3 seconds
                file_status.job_name = 'file_deleting_job'
                file_status.job_message = ''
                file_status.task_id = task.id
                db.commit()
                logger.debug(f"File processing task enqueued with id {task.id}")


def add_new_link(uri):
    """
    Adds a new link to the database and enqueues a processing task.

    This function performs the following steps:
    1. Deletes any existing links with the same URI.
    2. Adds a new link with the status 'uploaded' to the database.
    3. Enqueues a background task to process the link.

    Args:
        uri (str): The URI of the link to be added.

    Returns:
        LinkStatus: The newly created LinkStatus object.

    Raises:
        HTTPException: If there is an error deleting existing links or committing to the database.
    """
    with get_db() as db:
        try:
            old_links = db.query(LinkStatus).filter(LinkStatus.uri == uri).all()
            for old_link in old_links:
                delete_existing_link(old_link.uri)
        except Exception as e:
            logger.error(f"Error deleting existing link: {e}")
            db.rollback()
            raise HTTPException(status_code=400, detail="Error deleting existing link")

        link_status = LinkStatus(
            uri=uri,
            status='uploaded',
            created_at=datetime.now(timezone.utc)
        )
        db.add(link_status)
        db.commit()

        logger.debug(f"Link {uri} saved in database with id {link_status.id}.")

        try:
            task = process_link_task.delay(link_id=link_status.id)
            link_status.job_name = 'link_processing_job'
            link_status.task_id = task.id
            db.commit()
            logger.debug(f"Link {link_status.id} processing task enqueued with id {task.id}")
        except Exception as e:
            logger.error(f"Error committing to database: {e}")
            db.rollback() # rollback only the delay job
        return link_status

def delete_existing_link(uri):
    """
    Marks an existing link for deletion and enqueues a deletion task.

    This function retrieves a link from the database using the provided URI.
    If the link exists, it updates the link's status to 'deleting', marks it
    for deletion, and commits the changes to the database. It then enqueues
    a deletion task and updates the link with the task details.

    Args:
        uri (str): The URI of the link to be deleted.

    Returns:
        None
    """
    with get_db() as db:
        link_statuses = db.query(LinkStatus).filter(LinkStatus.uri == uri, LinkStatus.marked_for_deletion == False).all()  # noqa: E712

        if link_statuses:
            for link_status in link_statuses:
                link_status.marked_for_deletion = True
                link_status.status = 'deleting'
                db.commit()
                task = delete_link_task.delay(link_id=link_status.id)
                link_status.job_name = 'link_deleting_job'
                link_status.job_message = ''
                link_status.task_id = task.id
                db.commit()
                logger.debug(f"Link {link_status.id} deletion task enqueued with id {task.id}")

def filtered_list_bucket(client):
    buckets = client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    regex_filter = str(os.getenv('BUCKET_NAME_REGEX_FILTER', ''))
    if len(regex_filter) > 0:
        bucket_names = [name for name in bucket_names if re.match(regex_filter, name)]
        logger.debug(f"Displaying {len(bucket_names)}/{len(buckets)} buckets after applying regex filter: {regex_filter}")

    return bucket_names

def sync_files(minio_client, add_file_func, update_file_func, delete_file_func, skip_file_func=None):
    """
    Synchronizes files between MinIO storage and the database.
    This function performs the following steps:
    1. Retrieves the database connection.
    2. Fetches the list of buckets from MinIO storage.
    3. For each bucket, it lists the objects and compares them with the database records.
    4. If a file exists in both MinIO and the database but has changed, it updates the database.
    5. If a file is new in MinIO, it adds it to the database.
    6. If a file exists in the database but not in MinIO, it deletes the record from the database.
    7. Returns a JSON response indicating the success or failure of the synchronization process.
    Returns:
        Response: A JSON response with a message indicating the result of the synchronization process.
    """

    bucket_names = filtered_list_bucket(minio_client)

    with get_db() as db:
        try:
            for bucket_name in bucket_names:
                minio_files = minio_client.list_objects(bucket_name)
                for obj in minio_files:
                    file_status = db.query(FileStatus).filter(FileStatus.bucket_name == bucket_name, FileStatus.object_name == obj.object_name).first()
                    if file_status:
                        if file_status.etag != obj.etag or file_status.size != obj.size:
                            # File exists and seems to be changed, delete it and add a new one
                            if callable(update_file_func):
                                update_file_func(bucket_name, obj.object_name, obj.etag, obj.content_type, obj.size)
                            logger.debug(f"File {obj.object_name} in bucket {bucket_name} has changed. Processing.")
                        else:
                            # File exactly the same, skip
                            if callable(skip_file_func):
                                skip_file_func(bucket_name, obj.object_name)
                            logger.debug(f"File {obj.object_name} in bucket {bucket_name} has the same size and etag. Skipping.")
                    else:
                        # File is a new file without any data in vector database
                        if callable(add_file_func):
                            add_file_func(bucket_name, obj.object_name, obj.etag, obj.content_type, obj.size)
                        logger.debug(f"File {obj.object_name} in bucket {bucket_name} is a new file. Processing.")
        except S3Error as e:
            logger.error(f"An error occurred: {e}")
        db.commit()

    with get_db() as db:
        try:
            for bucket_name in bucket_names:
                minio_files = minio_client.list_objects(bucket_name)
                minio_objects = [obj.object_name for obj in minio_files]
                files_in_db_but_not_in_minio = db.query(FileStatus).filter(FileStatus.bucket_name == bucket_name, FileStatus.object_name.notin_(minio_objects)).all()

                for obj in files_in_db_but_not_in_minio:
                    if callable(delete_file_func):
                        delete_file_func(obj.bucket_name, obj.object_name)
                    logger.debug(f"File {obj.object_name} in bucket {obj.bucket_name} does not exist in storage but is in DB. Deleting.")

        except S3Error as e:
            logger.error(f"An error occurred: {e}")
        db.commit()

    with get_db() as db:
        objects_from_buckets_in_db_but_not_in_storage = db.query(FileStatus).filter(FileStatus.bucket_name.notin_(bucket_names))
        for obj in objects_from_buckets_in_db_but_not_in_storage:
            if callable(delete_file_func):
                delete_file_func(obj.bucket_name, obj.object_name)
            logger.debug(f"File {obj.object_name} in bucket {obj.bucket_name} - whole bucket is missing. Deleting.")

    return True

@app.post('/minio_event')
def process_minio_event(event: Union[S3EventData, MinioEventData], request: Request):
    """
    Processes events from MinIO.
    This function handles events related to object creation and deletion in a MinIO bucket.
    It processes the event data, extracts relevant information, and performs actions such as
    adding new files to the database or deleting existing files.
    Event Types Handled:
    - Object Created: 's3:ObjectCreated:Put', 's3:ObjectCreated:CompleteMultipartUpload'
    - Object Removed: 's3:ObjectRemoved:Delete', 's3:ObjectRemoved:NoOP', 's3:ObjectRemoved:DeleteMarkerCreated'
    Returns:
        Response: A JSON response indicating the result of the event processing.
    """
    files_added = 0
    files_deleted = 0
    for record in event.Records:
        if record.eventName in ['s3:ObjectCreated:Put', 's3:ObjectCreated:CompleteMultipartUpload', 'ObjectCreated:Put', 'ObjectCreated:CompleteMultipartUpload']:
            bucket_name = unquote_plus(record.s3.bucket.name)
            object_name = unquote_plus(record.s3.object.key)
            etag = record.s3.object.eTag
            content_type = record.s3.object.contentType
            size = record.s3.object.size or 0
            try:
                add_new_file(bucket_name, object_name, etag, content_type, size)
            except Exception as e:
                logger.error(f"Error adding file to database: {e}")
            files_added += 1
            return JSONResponse(content={'message': 'File(s) uploaded successfully'})

        if record.eventName in ['s3:ObjectRemoved:Delete', 's3:ObjectRemoved:NoOP', 's3:ObjectRemoved:DeleteMarkerCreated', 'ObjectRemoved:Delete', 'ObjectRemoved:DeleteMarkerCreated']:
            bucket_name = unquote_plus(record.s3.bucket.name)
            object_name = unquote_plus(record.s3.object.key)
            try:
                delete_existing_file(bucket_name, object_name)
            except Exception as e:
                logger.error(f"Error deleting existing file: {e}")
            files_deleted += 1

    if files_added > 0 and files_deleted > 0:
        return JSONResponse(content={'message': 'File(s) uploaded and deleted successfully'})
    if files_added > 0:
        return JSONResponse(content={'message': 'File(s) uploaded successfully'})
    if files_deleted > 0:
        return JSONResponse(content={'message': 'File(s) deleted successfully'})

    raise HTTPException(status_code=501, detail="Event not implemented")


# ------------- API link management ------------


@app.get("/api/links")
def api_links(request: Request) -> List[LinkResponse]:
    """
    Retrieve and return a list of API links with their statuses and metadata.
    This function queries the database for all LinkStatus records, ordered by their creation date.
    Returns:
        list: A list of links with their metadata and status information.
    Returns:
        200: A list of links with their metadata and status information.
    """

    with get_db() as db:
        links = db.query(LinkStatus).order_by(LinkStatus.created_at).filter(LinkStatus.marked_for_deletion == False).all() # noqa: E712
        return [link.to_response() for link in links]


@app.post('/api/links')
def api_add_link(input: LinkRequest, request: Request):
    """
    Adds new links to the database after validating them.

    Args:
        input (LinkRequest): An object containing the list of links to be added.
        request (Request): The request object.

    Raises:
        HTTPException: If any of the URLs in the input are invalid.

    Returns:
        JSONResponse: A JSON response containing a success message and the list of added URLs.
    """

    links = list(set([unquote_plus(link.strip()) for link in input.links]))
    # Validate urls
    for link_url in links:
        if not validators.url(link_url):
            raise HTTPException(status_code=400, detail=f"Invalid URL passed: {link_url}")

    added_urls = []
    for link_url in links:
        try:
            uri = unquote_plus(link_url.strip())
            link_status = add_new_link(uri)
            added_urls.append(str(link_status.id))
        except Exception as e:
            logger.error(f"Error adding link {uri} to database: {e}")
    if len(added_urls) == 0:
        raise HTTPException(status_code=400, detail="Error adding link(s) to database")
    else:
        return JSONResponse(content={'message': 'Link(s) added successfully', 'id': added_urls})


@app.delete('/api/link/{link_uuid}')
def api_delete_link(link_uuid: str, request: Request):
    """
    Deletes a link based on the provided UUID.

    Args:
        link_uuid (str): The UUID of the link to be deleted.
        request (Request): The request object.

    Raises:
        HTTPException: If the provided UUID is invalid.
        HTTPException: If the link is not found.
        HTTPException: If an error occurs during deletion.

    Returns:
        JSONResponse: A JSON response indicating the result of the deletion.
    """

    try:
        link_id = uuid.UUID(link_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid link_id passed: #{link_uuid}")

    with get_db() as db:
        try:
            link = db.query(LinkStatus).filter(LinkStatus.id == link_id).first()
            if link:
                delete_existing_link(link.uri)
                return JSONResponse(content={'message': 'Link deleted successfully'})
            else:
                raise HTTPException(status_code=404, detail="Link not found")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(status_code=400, detail="Error deleting link")


@app.post("/api/link/{link_uuid}/retry")
def api_link_task_retry(link_uuid: str, request: Request):
    """
    Retry processing a link by its UUID.

    This endpoint validates the provided link UUID, and
    attempts to reset and reprocess the link if it exists in the database.

    Args:
        link_uuid (str): The UUID of the link to be retried.

    Returns:
        Response: A JSON response indicating the result of the operation.
            - 200: Task enqueued successfully.
            - 400: Invalid link_uuid.
            - 404: Link not found.
    """

    try:
        link_id = uuid.UUID(link_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid link_id passed: {link_uuid}")

    with get_db() as db:
        link = db.query(LinkStatus).filter(LinkStatus.id == link_id).first()

        if link:
            link.chunks_total = 0
            link.chunks_processed = 0
            link.job_message = ''
            link.status = 'uploaded'
            db.commit()
            task = process_link_task.delay(link_id=link.id)
            link.job_name = 'link_processing_job'
            link.task_id = task.id
            db.commit()
            return JSONResponse(content={'message': 'Task enqueued successfully'})
        else:
            raise HTTPException(status_code=404, detail="Link not found")


@app.delete("/api/link/{link_uuid}/task")
def api_link_task_cancel(link_uuid: str, request: Request):
    """
    Cancel a processing task associated with a link.

    Args:
        link_uuid (str): The UUID of the link whose task is to be canceled. This removes the task from the queue.

    Returns:
        Response: A JSON response indicating the result of the cancellation attempt.
            - 400: If the provided link UUID is invalid.
            - 404: If the link is not found or does not have an associated task.
            - 200: If the task is successfully canceled and the link status is updated.
    """

    try:
        link_id = uuid.UUID(link_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid link_id passed: {link_uuid}")

    with get_db() as db:
        link = db.query(FileStatus).filter(FileStatus.id == link_id).first()

        if link and link.task_id:
            try:
                task = AsyncResult(link.task_id)
                task.revoke(terminate=True)
                link.status = 'canceled'
                link.task_id = ''
                link.job_name = ''
                link.job_message = 'Processing task canceled'
                db.commit()
                return JSONResponse(content={'message': 'LinkStatus processing task canceled'})
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error canceling task: {e}")
        else:
            raise HTTPException(status_code=404, detail="Link not found")


# ------------- API file management ------------

@app.get("/api/files")
def api_files(request: Request) -> List[FileResponse]:
    """
    Retrieve a list of files with their statuses and metadata from the database.
    Returns:
        list: A list of files with their metadata and status information.
    """

    with get_db() as db:
        files = db.query(FileStatus).order_by(FileStatus.created_at).filter(FileStatus.marked_for_deletion == False).all() # noqa: E712
        return [file.to_response() for file in files]


@app.post("/api/file/{file_uuid}/retry")
def api_file_task_retry(file_uuid: str, request: Request):
    """
    Retry processing a file by its UUID.

    This endpoint validates the provided file UUID, and
    attempts to reset and reprocess the file if it exists in the database.

    Args:
        file_uuid (str): The UUID of the file to be retried.

    Returns:
        Response: A JSON response indicating the result of the operation.
            - 200: Task enqueued successfully.
            - 400: Invalid file_id.
            - 404: File not found.
    """

    try:
        file_id = uuid.UUID(file_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid file_id passed: {file_uuid}")

    with get_db() as db:
        file = db.query(FileStatus).filter(FileStatus.id == file_id).first()

        if file:
            file.chunks_total = 0
            file.chunks_processed = 0
            file.job_message = ''
            file.status = 'uploaded'
            db.commit()
            task = process_file_task.delay(file_id=file.id)
            file.job_name = 'file_processing_job'
            file.task_id = task.id
            db.commit()
            return JSONResponse(content={'message': 'Task enqueued successfully'})
        else:
            raise HTTPException(status_code=404, detail="File not found")


@app.delete("/api/file/{file_uuid}/task")
def api_file_task_cancel(file_uuid: str, request: Request):
    """
    Cancel a processing task associated with a file.

    Args:
        file_uuid (str): The UUID of the file whose task is to be canceled. This removes the task from the queue.

    Returns:
        Response: A JSON response indicating the result of the cancellation attempt.
            - 400: If the provided file UUID is invalid.
            - 404: If the file is not found or does not have an associated task.
            - 200: If the task is successfully canceled and the file status is updated.
    """

    try:
        file_id = uuid.UUID(file_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid file_id passed: {file_uuid}")

    with get_db() as db:
        file = db.query(FileStatus).filter(FileStatus.id == file_id).first()

        if file and file.task_id:
            try:
                task = AsyncResult(file.task_id)
                task.revoke(terminate=True)
                file.status = 'canceled'
                file.task_id = ''
                file.job_name = ''
                file.job_message = 'Processing task canceled'
                db.commit()
                return JSONResponse(content={'message': 'FileStatus processing task canceled'})
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error canceling task: {e}")
        else:
            raise HTTPException(status_code=404, detail="File not found")

@app.get('/api/files/sync')
def api_sync_diff(request: Request):
    """
    This function shows the difference between the files in MinIO storage and the database.
    It returns an array containing a list of files and their action that would be performed.
    """
    diff = []

    def add_file_func(bucket_name, object_name, etag, content_type, size, obj=diff):
        obj.append({ 'action': 'add', 'bucket_name': bucket_name, 'object_name': object_name })

    def update_file_func(bucket_name, object_name, etag, content_type, size, obj=diff):
        obj.append({ 'action': 'update', 'bucket_name': bucket_name, 'object_name': object_name })

    def delete_file_func(bucket_name, object_name, obj=diff):
        obj.append({ 'action': 'delete', 'bucket_name': bucket_name, 'object_name': object_name })

    def skip_file_func(bucket_name, object_name, obj=diff):
        obj.append({ 'action': 'no action', 'bucket_name': bucket_name, 'object_name': object_name })

    try:
        sync_files(minio_internal, add_file_func, update_file_func, delete_file_func, skip_file_func)
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise HTTPException(status_code=400, detail="Error during generating sync diff")

    return JSONResponse(content=diff)

@app.post('/api/files/sync')
def api_sync(request: Request):
    """
    This function calls the sync_files function to synchronize files between MinIO storage and the database.
    It schedules tasks to celery with the files to be added and deleted.
    Returns:
        JSONResponse: A JSON response indicating the result of the synchronization process.
    Raises:
        HTTPException: If an error occurs during the synchronization process.
    """
    try:
        sync_files(minio_internal, add_new_file, add_new_file, delete_existing_file)
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise HTTPException(status_code=400, detail="Error during sync")

    return JSONResponse(content={'message': 'Files synced successfully'})


# -------------- Debugging Features ---------------

@app.post("/api/file/{file_uuid}/extract")
def api_file_text_extract(file_uuid: str, request: Request):
    try:
        file_id = uuid.UUID(file_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid file_id passed: {file_uuid}")

    with get_db() as db:
        file = db.query(FileStatus).filter(FileStatus.id == file_id).first()

        try:
            import base64
            import requests

            minio_response = minio_internal.get_object(bucket_name=file.bucket_name, object_name=file.object_name)
            file_data = minio_response.read()
            file_base64 = base64.b64encode(file_data).decode('ascii')
            logger.debug(f"[{file.id}] Retrievied file from S3 storage.")

            DATAPREP_ENDPOINT  = os.environ.get('DATAPREP_ENDPOINT')
            response = requests.post(DATAPREP_ENDPOINT, json={
                'files': [ {'filename': file.object_name, 'data64': file_base64} ],
                'chunk_size': request.query_params.get('chunk_size', 512),
                'chunk_overlap': request.query_params.get('chunk_overlap', 0),
                'process_table': request.query_params.get('process_table', 'false'),
                'table_strategy': request.query_params.get('table_strategy', 'fast'),
            })

            if response.status_code != 200:
                return JSONResponse(status_code=500, content={'details': f"Something went wrong: {response.text}"})
            else:
                return JSONResponse(content={'docs': response.json()})
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Error downloading file. {e}")
        finally:
            minio_response.close()
            minio_response.release_conn()

@app.post("/api/link/{link_uuid}/extract")
def api_link_text_extract(link_uuid: str, request: Request):
    try:
        link_id = uuid.UUID(link_uuid, version=4)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid link_id passed: {link_uuid}")

    with get_db() as db:
        link = db.query(LinkStatus).filter(LinkStatus.id == link_id).first()

        try:
            import requests

            DATAPREP_ENDPOINT  = os.environ.get('DATAPREP_ENDPOINT')
            response = requests.post(DATAPREP_ENDPOINT, json={
                'links': [ str(link.uri) ],
                'chunk_size': request.query_params.get('chunk_size', 512),
                'chunk_overlap': request.query_params.get('chunk_overlap', 0),
                'process_table': request.query_params.get('process_table', 'false'),
                'table_strategy': request.query_params.get('table_strategy', 'fast'),
            })

            if response.status_code != 200:
                return JSONResponse(status_code=500, content={'details': f"Something went wrong: {response.text}"})
            else:
                return JSONResponse(content={'docs': response.json()})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error downloading link. {e}")

@app.post("/api/retrieve")
async def api_retrieve(request: Request):
    try:
        import requests
        EMBEDDING_ENDPOINT  = os.environ.get('EMBEDDING_ENDPOINT')
        RETRIEVER_ENDPOINT  = os.environ.get('RETRIEVER_ENDPOINT')
        RERANKER_ENDPOINT  = os.environ.get('RERANKER_ENDPOINT')

        d = await request.json()
        logger.debug(d)

        def get_f(data, field, default=None):
            return data.get(field, default)

        embedding_request = { 'text': get_f(d, 'query') }
        logger.debug(f"Request to embedding: {embedding_request}")
        response = requests.post(EMBEDDING_ENDPOINT, json=embedding_request)

        if response.status_code != 200:
            return JSONResponse(status_code=500, content={'details': f"Embedding went wrong: {response.text}"})

        retriever_request = response.json()
        retriever_request['search_type'] = get_f(d, 'search_type', 'similarity')
        retriever_request['k'] =  get_f(d, 'k', '32')
        retriever_request['distance_threshold'] =  get_f(d, 'distance_threshold', None)
        retriever_request['fetch_k'] =  get_f(d, 'fetch_k', '20')
        retriever_request['lambda_mult'] =  get_f(d, 'lambda_mult', '0.5')
        retriever_request['score_threshold'] =  get_f(d, 'score_threshold', '0.2')

        logger.debug(f"Request to retriever: {retriever_request}")
        response = requests.post(RETRIEVER_ENDPOINT, json=retriever_request)

        if str(get_f(d, 'reranker', 'false')).lower() == 'true':
            reranker_request = response.json()
            reranker_request['top_n'] =  get_f(d, 'top_n', '5')
            reranker_request['rerank_score_threshold'] =  get_f(d, 'rerank_score_threshold', '0.02')

            logger.debug(f"Request to reranker: {reranker_request}")
            request = requests.post(RERANKER_ENDPOINT, json=reranker_request)
            if request.status_code != 200:
                return JSONResponse(status_code=500, content={'details': f"Reranker went wrong: {request.text}"})
            else:
                return JSONResponse(content={'docs': request.json()})

        if response.status_code != 200:
            return JSONResponse(status_code=500, content={'details': f"Retriever went wrong: {response.text}"})
        else:
            return JSONResponse(content={'docs': response.json()})
    except Exception as e:
        return JSONResponse(content={'details': f"Something went wrong: {e}"})

# ---------------------------------------

if __name__ == '__main__':
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5000)

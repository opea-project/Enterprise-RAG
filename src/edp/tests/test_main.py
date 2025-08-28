from unittest.mock import patch, MagicMock
from minio.error import S3Error
from app.main import app
from fastapi.testclient import TestClient
from urllib3.response import HTTPResponse as BaseHTTPResponse
from app.main import add_new_file, delete_existing_file, filtered_list_bucket

client = TestClient(app)

def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'message': 'OK'}

@patch('app.main.get_db')
def test_metrics(mock_get_db):
    mock_inspect = MagicMock()
    mock_inspect.stats.return_value = {'worker1': {'status': 'ok'}}
    with patch('app.main.celery.control.inspect', return_value=mock_inspect):
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        response = client.get('/metrics')
        assert response.status_code == 200
        assert 'edp_files_total' in response.text
        assert 'edp_links_total' in response.text
        assert 'edp_files_for_deletion_total' in response.text
        assert 'edp_links_for_deletion_total' in response.text
        assert 'edp_files_chunks_total' in response.text
        assert 'edp_links_chunks_total' in response.text
        assert 'edp_chunks_total' in response.text
        assert 'edp_files_uploaded_total' in response.text
        assert 'edp_files_error_total' in response.text
        assert 'edp_files_processing_total' in response.text
        assert 'edp_files_text_extracting_total' in response.text
        assert 'edp_files_text_compression_total' in response.text
        assert 'edp_files_text_splitting_total' in response.text
        assert 'edp_files_embedding_total' in response.text
        assert 'edp_files_ingested_total' in response.text
        assert 'edp_files_deleting_total' in response.text
        assert 'edp_files_canceled_total' in response.text
        assert 'edp_links_uploaded_total' in response.text
        assert 'edp_links_error_total' in response.text
        assert 'edp_links_processing_total' in response.text
        assert 'edp_links_text_extracting_total' in response.text
        assert 'edp_links_text_compression_total' in response.text
        assert 'edp_links_text_splitting_total' in response.text
        assert 'edp_links_embedding_total' in response.text
        assert 'edp_celery_reserved_tasks_total' in response.text
        assert 'edp_celery_scheduled_tasks_total' in response.text
        assert 'edp_celery_active_tasks_total' in response.text

def test_filtered_list_bucket():
    with patch('app.main.minio_internal') as mock_minio:
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "test-bucket"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "myown-bucket"
        mock_bucket3 = MagicMock()
        mock_bucket3.name = "my-bucket"
        mock_minio.list_buckets.return_value = [mock_bucket1, mock_bucket2, mock_bucket3]

        bucket_names = filtered_list_bucket(mock_minio)
        assert bucket_names == ["test-bucket", "myown-bucket", "my-bucket"]

def test_filtered_list_bucket_with_regex():
    with patch('app.main.minio_internal') as mock_minio:
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "test-bucket"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "myown-bucket"
        mock_bucket3 = MagicMock()
        mock_bucket3.name = "my-bucket"
        mock_minio.list_buckets.return_value = [mock_bucket1, mock_bucket2, mock_bucket3]

        with patch('os.getenv', return_value='my.*') as mock_getenv:
            bucket_names = filtered_list_bucket(mock_minio)
            mock_getenv.assert_called_with('BUCKET_NAME_REGEX_FILTER', '')
            assert bucket_names == ["myown-bucket", "my-bucket"]

@patch('app.main.get_db')
@patch('app.main.process_file_task')
@patch('app.main.delete_existing_file')
def test_add_new_file(mock_delete_existing_file, mock_process_file_task, mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db
    mock_process_file_task.delay.return_value = MagicMock(id="123e4567-e89b-12d3-a456-426614174000")
    mock_delete_existing_file.return_value = MagicMock()

    bucket_name = "test-bucket"
    object_name = "test-object"
    etag = "test-etag"
    content_type = "application/octet-stream"
    size = 1024

    # Mock existing files to be deleted
    mock_old_file = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_old_file]


    file_status = add_new_file(bucket_name, object_name, etag, content_type, size)

    # Check if new file was added to the database
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called()

    # Check if the file processing task was enqueued
    mock_process_file_task.delay.assert_called_once_with(file_id=file_status.id, countdown=1)

    assert file_status.bucket_name == bucket_name
    assert file_status.object_name == object_name
    assert file_status.etag == etag
    assert file_status.content_type == content_type
    assert file_status.size == size
    assert file_status.status == 'uploaded'
    assert file_status.task_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_status.job_name == 'file_processing_job'

@patch('app.main.get_db')
@patch('app.main.delete_file_task')
def test_delete_existing_file(mock_delete_file_task, mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db
    mock_delete_file_task.delay.return_value = MagicMock(id="123e4567-e89b-12d3-a456-426614174000")

    bucket_name = "test-bucket"
    object_name = "test-object"

    # Mock existing files to be marked for deletion
    mock_file_status = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_file_status]

    delete_existing_file(bucket_name, object_name)

    # Check if the file was marked for deletion and status updated
    mock_file_status.marked_for_deletion = True
    mock_file_status.status = 'deleting'
    mock_db.commit.assert_called()

    # Check if the file deletion task was enqueued
    mock_delete_file_task.delay.assert_called_once_with(file_id=mock_file_status.id, countdown=3)

    assert mock_file_status.job_name == 'file_deleting_job'
    assert mock_file_status.task_id == "123e4567-e89b-12d3-a456-426614174000"

@patch('app.main.get_db')
def test_delete_existing_file_no_files(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db

    bucket_name = "test-bucket"
    object_name = "test-object"

    # Mock no existing files to be marked for deletion
    mock_db.query.return_value.filter.return_value.all.return_value = []

    delete_existing_file(bucket_name, object_name)

    # Check that no files were marked for deletion and no tasks were enqueued
    mock_db.commit.assert_not_called()

def test_presigned_url():
    methods = ["GET", "PUT", "DELETE"]
    for method in methods:
        payload = {
            "bucket_name": "my-bucket",
            "object_name": "my-object",
            "method": method
        }
        with patch('app.main.generate_presigned_url') as mock_generate_presigned_url:
            mock_generate_presigned_url.return_value = "http://example.com/presigned-url"
            response = client.post('/api/presignedUrl', json=payload)
            assert response.status_code == 200
            assert response.json() == {'url': 'http://example.com/presigned-url'}

def test_presigned_url_missing_data():
    fields = ["bucket_name", "object_name"]
    for field in fields:
        payload = {
            "bucket_name": "my-bucket",
            "object_name": "my-object",
            "method": 'GET'
        }
        payload[field] = ""
        with patch('app.main.generate_presigned_url') as mock_generate_presigned_url:
            mock_generate_presigned_url.return_value = "http://example.com/presigned-url"
            response = client.post('/api/presignedUrl', json=payload)
            assert response.status_code == 400
            assert response.json() == {'detail': 'Please provide both bucket_name and object_name'}

def test_presigned_url_s3_error():
    methods = ["GET", "PUT", "DELETE"]
    for method in methods:
        payload = {
            "bucket_name": "my-bucket",
            "object_name": "my-object",
            "method": method
        }
        with patch('app.main.generate_presigned_url' ) as mock_generate_presigned_url:
            mock_generate_presigned_url.side_effect = S3Error(
                code='NoSuchBucket',
                resource='my-bucket/my-object',
                message='The specified bucket does not exist',
                request_id='',
                host_id='',
                response=BaseHTTPResponse()
            )
            response = client.post('/api/presignedUrl', json=payload)
            assert response.status_code == 400
            assert response.json()['detail'].startswith('An error occurred')

def test_presigned_url_wrong_method():
    methods = ['POST', 'PATCH']
    for method in methods:
        payload = {
            "bucket_name": "my-bucket",
            "object_name": "my-object",
            "method": method
        }

        response = client.post('/api/presignedUrl', json=payload)
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid method'}

def test_api_links():
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        response = client.get('/api/links')
        assert response.status_code == 200
        assert response.json() == []

def test_api_add_link():
    payload = {
        "links": ["http://example.com"]
    }
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch('app.main.process_link_task') as mock_task:
            mock_task.return_value = MagicMock(job_name="link_processing_job", id="123e4567-e89b-12d3-a456-426614174000")
            response = client.post('/api/links', json=payload)
        assert response.status_code == 200
        assert response.json() == {'id': ['None'], 'message': 'Link(s) added successfully'}

def test_api_add_invalid_link():
    payload = {
        "links": ["-1"]
    }
    response = client.post('/api/links', json=payload)
    assert response.status_code == 400
    assert response.json()['detail'].startswith('Invalid URL passed')

def test_api_add_existing_link():
    payload = {
        "links": ["http://example.com"]
    }
    with patch('app.main.get_db') as mock_get_db, \
         patch('app.main.delete_existing_link') as mock_delete_existing_link:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(uri="http://example.com")
        ]
        response = client.post('/api/links', json=payload)
        mock_delete_existing_link.assert_called_once_with("http://example.com")
        assert response.status_code == 200
        assert response.json() == {'id': ['None'], 'message': 'Link(s) added successfully'}

def test_api_add_link_exception():
    payload = {
        "links": ["http://example.com"]
    }
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = Exception("Database commit failed")
        response = client.post('/api/links', json=payload)
        assert response.status_code == 400
        assert response.json()['detail'].startswith('Error adding link(s) to database')

@patch('app.main.delete_existing_link')
def test_api_delete_link(mock_delete_existing_link):
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        mock_delete_existing_link.return_value = MagicMock(id="123e4567-e89b-12d3-a456-426614174000")
        response = client.delete(f'/api/link/{link_uuid}')
        assert response.status_code == 200
        assert response.json() == {'message': 'Link deleted successfully'}

def test_api_delete_link_invalid_id():
    link_uuid = "-1"
    response = client.delete(f'/api/link/{link_uuid}')
    assert response.status_code == 400
    assert response.json()['detail'].startswith('Invalid link_id')

@patch('app.main.delete_existing_link')
def test_api_delete_link_exception(mock_delete_existing_link):
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    mock_delete_existing_link.return_value = MagicMock(id="123e4567-e89b-12d3-a456-426614174000")
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.side_effect = Exception("Database query failed")
        response = client.delete(f'/api/link/{link_uuid}')
        assert response.status_code == 400
        assert response.json()['detail'].startswith('Error deleting link')

def test_api_delete_link_not_found():
    link_uuid = "123e4567-e89b-12d3-a456-426614174001"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.delete(f'/api/link/{link_uuid}')
        assert response.status_code == 400
        assert response.json()['detail'].startswith('Error deleting link')

def test_api_files():
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        response = client.get('/api/files')
        assert response.status_code == 200
        assert response.json() == []

def test_api_file_task_retry():
    file_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch('app.main.process_file_task') as mock_task:
            mock_task.return_value = MagicMock(job_name="link_processing_job", id="123e4567-e89b-12d3-a456-426614174000")
            response = client.post(f'/api/file/{file_uuid}/retry')
        assert response.status_code == 200
        assert response.json() == {'message': 'Task enqueued successfully'}

def test_api_file_task_retry_invalid():
    file_uuid = "-1"
    response = client.post(f'/api/file/{file_uuid}/retry')
    assert response.status_code == 400
    assert response.json()['detail'].startswith('Invalid file_id')

def test_api_file_task_retry_not_found():
    file_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.post(f'/api/file/{file_uuid}/retry')
        assert response.status_code == 404
        assert response.json() == {'detail': 'File not found'}

def test_api_file_task_cancel():
    file_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_file = MagicMock()
        mock_file.task_id = "task_id"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        with patch('app.main.AsyncResult') as mock_async_result:
            mock_task = MagicMock()
            mock_async_result.return_value = mock_task
            response = client.delete(f'/api/file/{file_uuid}/task')
            assert response.status_code == 200
            assert response.json() == {'message': 'FileStatus processing task canceled'}

def test_api_file_task_cancel_invalid():
    file_uuid = "-1"
    response = client.delete(f'/api/file/{file_uuid}/task')
    assert response.status_code == 400
    assert response.json()['detail'].startswith('Invalid file_id')

def test_api_file_task_cancel_not_found():
    file_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.delete(f'/api/file/{file_uuid}/task')
        assert response.status_code == 404
        assert response.json() == {'detail': 'File not found'}

def test_api_file_task_cancel_exception():
    file_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_file = MagicMock()
        mock_file.file_id = file_uuid
        mock_file.task_id = file_uuid
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        with patch('app.main.AsyncResult') as mock_async_result:
            mock_task = MagicMock()
            mock_task.revoke.side_effect = Exception("Task revoke failed")
            mock_async_result.return_value = mock_task
            response = client.delete(f'/api/file/{file_uuid}/task')
            assert response.status_code == 400
            assert response.json()['detail'].startswith('Error canceling task')

def test_s3_put_event():
    payload = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-west-2",
                "eventTime": "2025-02-24T13:07:08.792Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "AWS:secret"
                },
                "requestParameters": {
                    "sourceIPAddress": "134.191.197.184"
                },
                "responseElements": {
                    "x-amz-request-id": "random2",
                    "x-amz-id-2": "random3"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "tf-s3-queue-20250224125707326300000001",
                    "bucket": {
                        "name": "edp-s3-default-bucket",
                        "ownerIdentity": {
                            "principalId": "AS7IWF4R36R0T"
                        },
                        "arn": "arn:aws:s3:::edp-s3-default-bucket"
                    },
                    "object": {
                        "key": "test.txt",
                        "size": 18,
                        "eTag": "bdeca7cd9b893ac3dc3fea2dd24da5a6",
                        "sequencer": "0067BC6EFCBE1A1EE8"
                    }
                }
            }
        ]
    }
    with patch('app.main.process_file_task') as mock_task:
        mock_task.return_value = MagicMock(job_name="file_processing_job", id="123e4567-e89b-12d3-a456-426614174000")
        response = client.post('/minio_event', json=payload)
        assert response.json() == {'message': 'File(s) uploaded successfully'}
        assert response.status_code == 200

def test_minio_put_event():
    payload = {
        "EventName": "s3:ObjectCreated:Put",
        "Key": "test/photo.png",
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "minio:s3",
                "awsRegion": "",
                "eventTime": "2024-11-18T09:42:12.709Z",
                "eventName": "s3:ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                },
                "requestParameters": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk",
                    "region": "",
                    "sourceIPAddress": "172.19.0.6"
                },
                "responseElements": {
                    "x-amz-id-2": "dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8",
                    "x-amz-request-id": "180906BB2E581534",
                    "x-minio-deployment-id": "f24c3f26-677d-40c7-8884-c1652b7659d8",
                    "x-minio-origin-endpoint": "http://172.19.0.2:9000"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "Config",
                    "bucket": {
                    "name": "test",
                    "ownerIdentity": {
                        "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                    },
                    "arn": "arn:aws:s3:::test"
                    },
                    "object": {
                    "key": "photo.png",
                    "size": 92097,
                    "eTag": "90176eac2c7f404c3d56263c3bd3ac93",
                    "contentType": "application/octet-stream",
                    "userMetadata": {
                        "content-type": "application/octet-stream"
                    },
                    "sequencer": "180906BB2E6792A7"
                    }
                },
                "source": {
                    "host": "172.19.0.6",
                    "port": "",
                    "userAgent": "MinIO (Linux; x86_64) minio-py/7.2.10"
                }
            }
        ]
    }
    with patch('app.main.process_file_task') as mock_task:
        mock_task.return_value = MagicMock(job_name="file_processing_job", id="123e4567-e89b-12d3-a456-426614174000")
        response = client.post('/minio_event', json=payload)
        assert response.json() == {'message': 'File(s) uploaded successfully'}
        assert response.status_code == 200

def test_s3_delete_event():
    payload = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-west-2",
                "eventTime": "2025-02-26T12:52:57.395Z",
                "eventName": "ObjectRemoved:Delete",
                "userIdentity": {
                    "principalId": "random2"
                },
                "requestParameters": {
                    "sourceIPAddress": "134.191.197.182"
                },
                "responseElements": {
                    "x-amz-request-id": "CVG4V03RT0PWY5FS",
                    "x-amz-id-2": "random3"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "tf-s3-queue-20250224125707326300000001",
                    "bucket": {
                        "name": "edp-s3-default-bucket",
                        "ownerIdentity": {
                            "principalId": "AS7IWF4R36R0T"
                        },
                        "arn": "arn:aws:s3:::edp-s3-default-bucket"
                    },
                    "object": {
                        "key": "sdfsdfsdf.txt",
                        "sequencer": "0067BF0EA96062684C"
                    }
                }
            }
        ]
    }
    with patch('app.main.delete_existing_file') as mock_task:
        mock_task.return_value = MagicMock(job_name="file_deleting_job", id="123e4567-e89b-12d3-a456-426614174000")
        response = client.post('/minio_event', json=payload)
        assert response.json() == {'message': 'File(s) deleted successfully'}
        assert response.status_code == 200

def test_minio_delete_event():
    payload = {
        "EventName": "s3:ObjectRemoved:Delete",
        "Key": "test/photo.png",
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "minio:s3",
                "awsRegion": "",
                "eventTime": "2024-11-18T09:42:12.709Z",
                "eventName": "s3:ObjectRemoved:Delete",
                "userIdentity": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                },
                "requestParameters": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk",
                    "region": "",
                    "sourceIPAddress": "172.19.0.6"
                },
                "responseElements": {
                    "x-amz-id-2": "dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8",
                    "x-amz-request-id": "180906BB2E581534",
                    "x-minio-deployment-id": "f24c3f26-677d-40c7-8884-c1652b7659d8",
                    "x-minio-origin-endpoint": "http://172.19.0.2:9000"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "Config",
                    "bucket": {
                        "name": "test",
                        "ownerIdentity": {
                            "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                        },
                        "arn": "arn:aws:s3:::test"
                    },
                    "object": {
                        "key": "photo.png",
                        "sequencer": "180906BB2E6792A7"
                    }
                },
                "source": {
                    "host": "172.19.0.6",
                    "port": "",
                    "userAgent": "MinIO (Linux; x86_64) minio-py/7.2.10"
                }
            }
        ]
    }
    with patch('app.main.delete_existing_file') as mock_task:
        mock_task.return_value = MagicMock(job_name="file_deleting_job", id="123e4567-e89b-12d3-a456-426614174000")
        response = client.post('/minio_event', json=payload)
        assert response.json() == {'message': 'File(s) deleted successfully'}
        assert response.status_code == 200

def test_minio_unknown_event():
    payload = {
        "EventName": "unknown",
        "Key": "test/photo.png",
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "minio:s3",
                "awsRegion": "",
                "eventTime": "2024-11-18T09:42:12.709Z",
                "eventName": "unknown",
                "userIdentity": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                },
                "requestParameters": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk",
                    "region": "",
                    "sourceIPAddress": "172.19.0.6"
                },
                "responseElements": {
                    "x-amz-id-2": "dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8",
                    "x-amz-request-id": "180906BB2E581534",
                    "x-minio-deployment-id": "f24c3f26-677d-40c7-8884-c1652b7659d8",
                    "x-minio-origin-endpoint": "http://172.19.0.2:9000"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "Config",
                    "bucket": {
                    "name": "test",
                    "ownerIdentity": {
                        "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                    },
                    "arn": "arn:aws:s3:::test"
                    },
                    "object": {
                    "key": "photo.png",
                    "size": 92097,
                    "eTag": "90176eac2c7f404c3d56263c3bd3ac93",
                    "contentType": "application/octet-stream",
                    "userMetadata": {
                        "content-type": "application/octet-stream"
                    },
                    "sequencer": "180906BB2E6792A7"
                    }
                },
                "source": {
                    "host": "172.19.0.6",
                    "port": "",
                    "userAgent": "MinIO (Linux; x86_64) minio-py/7.2.10"
                }
            }
        ]
    }

    response = client.post('/minio_event', json=payload)
    assert response.json() == {'detail': 'Event not implemented'}
    assert response.status_code == 501

def test_s3_unknown_event():
    payload = {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "minio:s3",
                "awsRegion": "",
                "eventTime": "2024-11-18T09:42:12.709Z",
                "eventName": "unknown",
                "userIdentity": {
                    "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                },
                "requestParameters": {
                    "sourceIPAddress": "172.19.0.6"
                },
                "responseElements": {
                    "x-amz-id-2": "dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8",
                    "x-amz-request-id": "180906BB2E581534"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "Config",
                    "bucket": {
                    "name": "test",
                    "ownerIdentity": {
                        "principalId": "V2MQZp28DJILe0g-dMApWT35GA9GmYxvzJCMHGBPkDk"
                    },
                    "arn": "arn:aws:s3:::test"
                    },
                    "object": {
                        "key": "photo.png",
                        "sequencer": "180906BB2E6792A7"
                    }
                }
            }
        ]
    }

    response = client.post('/minio_event', json=payload)
    assert response.json() == {'detail': 'Event not implemented'}
    assert response.status_code == 501

def test_api_sync():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects, \
            patch('app.main.add_new_file') as mock_add_new_file, \
            patch('app.main.delete_existing_file') as mock_delete_existing_file:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="test-object", etag="test-etag", size=1024, content_type="application/octet-stream")
        mock_list_objects.return_value = [mock_object]

        # Mock database files
        mock_file_status = MagicMock(bucket_name="test-bucket", object_name="test-object", etag="test-etag", size=1024)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file_status

        response = client.post('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == {'message': 'Files synced successfully'}

        # Check if add_new_file and delete_existing_file were called appropriately
        mock_add_new_file.assert_not_called()
        mock_delete_existing_file.assert_not_called()

def test_api_sync_new_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects, \
            patch('app.main.add_new_file') as mock_add_new_file, \
            patch('app.main.delete_existing_file') as mock_delete_existing_file:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="new-object", etag="new-etag", size=2048, content_type="application/octet-stream")
        mock_list_objects.return_value = [mock_object]

        # Mock database files
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == {'message': 'Files synced successfully'}

        # Check if add_new_file was called for the new object
        mock_add_new_file.assert_called_once()
        mock_delete_existing_file.assert_not_called()

def test_api_sync_deleted_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects, \
            patch('app.main.add_new_file') as mock_add_new_file, \
            patch('app.main.delete_existing_file') as mock_delete_existing_file:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_list_objects.return_value = []

        # Mock database files
        mock_file_status = MagicMock(bucket_name="test-bucket", object_name="test-object", etag="test-etag", size=1024)
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_file_status]

        response = client.post('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == {'message': 'Files synced successfully'}

        # Check if delete_existing_file was called for the missing object
        mock_add_new_file.assert_not_called()
        mock_delete_existing_file.assert_called_once_with("test-bucket", "test-object")

def test_api_sync_changed_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects, \
            patch('app.main.add_new_file') as mock_add_new_file, \
            patch('app.main.delete_existing_file') as mock_delete_existing_file:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="test-object", etag="new-etag", size=2048, content_type="application/octet-stream")
        mock_list_objects.return_value = [mock_object]

        # Mock database files
        mock_file_status = MagicMock(bucket_name="test-bucket", object_name="test-object", etag="old-etag", size=1024)
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_file_status]

        response = client.post('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == {'message': 'Files synced successfully'}

        # Check if add_new_file was called for the changed object
        mock_add_new_file.assert_called_once()
        mock_delete_existing_file.assert_called_once_with("test-bucket", "test-object")

def test_api_sync_diff_new_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="new-object", etag="new-etag", size=2048, content_type="application/octet-stream")
        mock_list_objects.return_value = [mock_object]

        # Mock database files
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == [{'action': 'add', 'bucket_name': 'test-bucket', 'object_name': 'new-object'}]

def test_api_sync_diff_deleted_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_list_objects.return_value = []

        # Mock database files
        mock_file_status = MagicMock(bucket_name="test-bucket", object_name="test-object", etag="test-etag", size=1024)
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_file_status]

        response = client.get('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == [{'action': 'delete', 'bucket_name': 'test-bucket', 'object_name': 'test-object'}]

def test_api_sync_diff_changed_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="test-object", etag="new-etag", size=2048, content_type="application/octet-stream")
        mock_list_objects.return_value = [mock_object]

        # Mock database files - we update the etag and size
        mock_db.query.return_value.filter.return_value.all.return_value = [] # no additional files in db

        response = client.get('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == [{'action': 'update', 'bucket_name': 'test-bucket', 'object_name': 'test-object'}]

def test_api_sync_diff_no_change_file():
    with patch('app.main.get_db') as mock_get_db, \
            patch('app.main.minio_internal.list_buckets') as mock_list_buckets, \
            patch('app.main.minio_internal.list_objects') as mock_list_objects:

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock MinIO buckets and objects
        mock_bucket = MagicMock()
        mock_bucket.name = "test-bucket"
        mock_list_buckets.return_value = [mock_bucket]

        mock_object = MagicMock(object_name="test-object", etag="old-etag", size=1024)
        mock_list_objects.return_value = [mock_object]

        # Mock database files
        mock_db.query.return_value.filter.return_value.first.return_value = mock_object
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = client.get('/api/files/sync')

        assert response.status_code == 200
        assert response.json() == [{'action': 'no action', 'bucket_name': 'test-bucket', 'object_name': 'test-object'}]

def test_api_link_task_retry():
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch('app.main.process_link_task') as mock_task:
            mock_task.return_value = MagicMock(job_name="link_processing_job", id="123e4567-e89b-12d3-a456-426614174000")
            response = client.post(f'/api/link/{link_uuid}/retry')
        assert response.status_code == 200
        assert response.json() == {'message': 'Task enqueued successfully'}

def test_api_link_task_retry_invalid():
    link_uuid = "-1"
    response = client.post(f'/api/link/{link_uuid}/retry')
    assert response.json()['detail'].startswith('Invalid link_id')
    assert response.status_code == 400

def test_api_link_task_retry_not_found():
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.post(f'/api/link/{link_uuid}/retry')
        assert response.status_code == 404
        assert response.json() == {'detail': 'Link not found'}

def test_api_link_task_cancel():
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_link = MagicMock()
        mock_link.task_id = "task_id"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_link
        with patch('app.main.AsyncResult') as mock_async_result:
            mock_task = MagicMock()
            mock_async_result.return_value = mock_task
            response = client.delete(f'/api/link/{link_uuid}/task')
            assert response.status_code == 200
            assert response.json() == {'message': 'LinkStatus processing task canceled'}

def test_api_link_task_cancel_invalid():
    link_uuid = "-1"
    response = client.delete(f'/api/link/{link_uuid}/task')
    assert response.status_code == 400
    assert response.json()['detail'].startswith('Invalid link_id')

def test_api_link_task_cancel_not_found():
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.delete(f'/api/link/{link_uuid}/task')
        assert response.status_code == 404
        assert response.json() == {'detail': 'Link not found'}

def test_api_link_task_cancel_exception():
    link_uuid = "123e4567-e89b-12d3-a456-426614174000"
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_link = MagicMock()
        mock_link.link_id = link_uuid
        mock_link.task_id = link_uuid
        mock_db.query.return_value.filter.return_value.first.return_value = mock_link
        with patch('app.main.AsyncResult') as mock_async_result:
            mock_task = MagicMock()
            mock_task.revoke.side_effect = Exception("Task revoke failed")
            mock_async_result.return_value = mock_task
            response = client.delete(f'/api/link/{link_uuid}/task')
            assert response.status_code == 400
            assert response.json()['detail'].startswith('Error canceling task')

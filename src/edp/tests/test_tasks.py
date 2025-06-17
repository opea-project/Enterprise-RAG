from unittest.mock import patch, MagicMock
from json.decoder import JSONDecodeError
from app.tasks import process_file_task, delete_file_task, process_link_task, delete_link_task, response_err

def test_response_error_json_reply():
    mock_r = MagicMock()
    mock_r.json.return_value = {'detail': 'Error details'}
    text = response_err(mock_r)
    assert text == 'Error details'

    mock_r = MagicMock()
    mock_r.json.return_value = {'key': 'value'}
    mock_r.text = "{'key': 'value'}"
    text = response_err(mock_r)
    assert text ==  "{'key': 'value'}"

    mock_r = MagicMock()
    mock_r.json.side_effect = JSONDecodeError('JSON error', 'error', 0)
    mock_r.text = "{'key': 'value'}"
    text = response_err(mock_r)
    assert text ==  "{'key': 'value'}"

def test_process_file_task_success():
    with patch('app.tasks.requests.post') as mock_post, \
         patch('app.tasks.WithEDPTask.minio') as minio, \
         patch('app.tasks.WithEDPTask.db') as mock_db:

        mock_file_db = MagicMock()
        mock_file_db.id = 1
        mock_file_db.bucket_name = 'test_bucket'
        mock_file_db.object_name = 'test_file.txt'
        mock_file_db.etag = 'test_etag'
        mock_db.query().filter().first.return_value = mock_file_db

        minio_response_mock = MagicMock()
        minio_response_mock.read.return_value = b'test_data'
        minio.get_object.return_value = minio_response_mock

        # Setup API responses for all processing steps
        delete_response = MagicMock(status_code=200)
        text_extractor_response = MagicMock(status_code=200)
        text_extractor_response.json.return_value = {'loaded_docs': ['doc1', 'doc2']}
        text_compression_response = MagicMock(status_code=200)
        text_compression_response.json.return_value = {'loaded_docs': ['compressed1', 'compressed2']}
        text_splitter_response = MagicMock(status_code=200)
        text_splitter_response.json.return_value = {'docs': [{'text': 'chunk1', 'metadata': {}}, {'text': 'chunk2', 'metadata': {}}]}
        embedding_response = MagicMock(status_code=200)
        embedding_response.json.return_value = {'embedded_docs': [{'text': 'chunk1', 'embedding': [0.1, 0.2]}]}
        ingestion_response = MagicMock(status_code=200)

        # Configure mock_post to return different responses for different calls
        mock_post.side_effect = [
            delete_response,           # Delete existing data
            text_extractor_response,   # Text extractor
            text_compression_response, # Text compression
            text_splitter_response,    # Text splitter
            embedding_response,        # First embedding batch
            ingestion_response         # First ingestion batch
        ]

        result = process_file_task(1)
        assert result == True  # noqa: E712

        # Verify status updates
        assert mock_file_db.status == 'ingested'
        assert mock_file_db.job_message == 'Data ingestion completed.'
        assert mock_file_db.task_id == ''

        # Verify the database was committed multiple times (at least once)
        assert mock_db.commit.call_count > 0

        # Verify all API endpoints were called
        assert mock_post.call_count == 6  # Based on our side_effect setup

def test_process_file_task_file_not_found():
    with patch('app.tasks.WithEDPTask.db') as mock_db:
        mock_db.query().filter().first.return_value = None
        try:
            process_file_task(1)
        except Exception as e:
            assert str(e) == "File with id 1 not found"

def test_delete_file_task_success():
    with patch('app.tasks.requests.post') as mock_post, \
         patch('app.tasks.WithEDPTask.db') as mock_db:

        mock_file_db = MagicMock()
        mock_file_db.id = 1
        mock_db.query().filter().first.return_value = mock_file_db

        mock_post.return_value.status_code = 200

        delete_file_task(1)
        mock_db.delete.assert_called_once_with(mock_file_db)

def test_delete_file_task_file_not_found():
    with patch('app.tasks.WithEDPTask.db') as mock_db:
        mock_db.query().filter().first.return_value = None
        try:
            delete_file_task(1)
        except Exception as e:
            assert str(e) == "File with id 1 not found"

def test_process_link_task_success():
    with patch('app.tasks.requests.post') as mock_post, \
         patch('app.tasks.WithEDPTask.db') as mock_db:

        mock_link_db = MagicMock()
        mock_link_db.id = 1
        mock_link_db.uri = 'http://example.com'
        mock_db.query().filter().first.return_value = mock_link_db

        # Setup API responses for all processing steps
        delete_response = MagicMock(status_code=200)
        text_extractor_response = MagicMock(status_code=200)
        text_extractor_response.json.return_value = {'loaded_docs': [{'text': 'doc1', 'metadata': {}}]}
        text_compression_response = MagicMock(status_code=200)
        text_compression_response.json.return_value = {'loaded_docs': ['compressed1', 'compressed2']}
        text_splitter_response = MagicMock(status_code=200)
        text_splitter_response.json.return_value = {'docs': [{'text': 'chunk1', 'metadata': {}}, {'text': 'chunk2', 'metadata': {}}]}
        embedding_response = MagicMock(status_code=200)
        embedding_response.json.return_value = {'embedded_docs': [{'text': 'chunk1', 'embedding': [0.1, 0.2]}]}
        ingestion_response = MagicMock(status_code=200)

        # Configure mock_post to return different responses for different calls
        mock_post.side_effect = [
            delete_response,           # Delete existing data
            text_extractor_response,   # Text extractor
            text_compression_response, # Text compression
            text_splitter_response,    # Text splitter
            embedding_response,        # First embedding batch
            ingestion_response         # First ingestion batch
        ]

        result = process_link_task(1)
        assert result == True  # noqa: E712

        # Verify status updates
        assert mock_link_db.status == 'ingested'
        assert mock_link_db.job_message == 'Data ingestion completed.'

        # Verify the database was committed multiple times
        assert mock_db.commit.call_count > 0

        # Verify all API endpoints were called
        assert mock_post.call_count == 6  # Based on our side_effect setup

def test_process_link_task_link_not_found():
    with patch('app.tasks.WithEDPTask.db') as mock_db:
        mock_db.query().filter().first.return_value = None
        try:
            process_link_task(1)
        except Exception as e:
            assert str(e) == "Link with id None not found"

def test_delete_link_task_success():
    with patch('app.tasks.requests.post') as mock_post, \
         patch('app.tasks.WithEDPTask.db') as mock_db:

        mock_link_db = MagicMock()
        mock_link_db.id = 1
        mock_db.query().filter().first.return_value = mock_link_db

        mock_post.return_value.status_code = 200

        delete_link_task(1)
        mock_db.delete.assert_called_once_with(mock_link_db)

def test_delete_link_task_link_not_found():
    with patch('app.tasks.WithEDPTask.db') as mock_db:
        mock_db.query().filter().first.return_value = None
        try:
            delete_link_task(1)
        except Exception as e:
            assert str(e) == "Link with id 1 not found"

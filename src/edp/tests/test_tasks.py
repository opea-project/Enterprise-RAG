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
         patch('app.tasks.Minio.get_object') as mock_get_object, \
         patch('app.tasks.WithEDPTask.db') as mock_db:
        
        mock_file_db = MagicMock()
        mock_file_db.id = 1
        mock_file_db.bucket_name = 'test_bucket'
        mock_file_db.object_name = 'test_file.txt'
        mock_file_db.etag = 'test_etag'
        mock_db.query().filter().first.return_value = mock_file_db
        
        mock_get_object.return_value.read.return_value = b'test_data'
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'docs': [{'metadata': {}}]}
        
        result = process_file_task(1)
        assert result == True  # noqa: E712

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
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'docs': [{'metadata': {}}]}
        
        result = process_link_task(1)
        assert result == True  # noqa: E712

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

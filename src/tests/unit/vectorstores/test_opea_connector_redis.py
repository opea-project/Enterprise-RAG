import pytest
from comps.vectorstores.utils.connectors.connector_redis import ConnectorRedis
import os

@pytest.fixture
def connector_redis():
    return ConnectorRedis()

@pytest.mark.parametrize(
    "env_vars, expected_url",
    [
        (
            {"REDIS_URL": "redis://localhost:6379", "VECTOR_STORE": "redis"},
            "redis://localhost:6379/",
        ),
        (
            {"REDIS_URL": "redis://localhost:6379", "VECTOR_STORE": "redis-cluster"},
            "redis://localhost:6379/?cluster=true",
        ),
        (
            {"REDIS_URL": "redis://localhost:6379?cluster=true", "VECTOR_STORE": "redis"},
            "redis://localhost:6379/?cluster=true",
        ),
        (
            {"REDIS_URL": "redis://localhost:6379?cluster=true", "VECTOR_STORE": "redis-cluster"},
            "redis://localhost:6379/?cluster=true",
        ),
        (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "VECTOR_STORE": "redis"},
            "redis://localhost:1234/",
        ),
         (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "REDIS_SSL": "true", "VECTOR_STORE": "redis"},
            "rediss://localhost:1234/",
        ),
        (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "VECTOR_STORE": "redis-cluster"},
            "redis://localhost:1234/?cluster=true",
        ),
        (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "REDIS_USERNAME": 'test', "REDIS_PASSWORD": 'test', "VECTOR_STORE": "redis-cluster"},
            "redis://test:test@localhost:1234/?cluster=true",
        ),
        (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "REDIS_USERNAME": 'test', "REDIS_PASSWORD": 'test', "VECTOR_STORE": "redis"},
            "redis://test:test@localhost:1234/",
        ),
    ],
)
def test_format_url_from_env(connector_redis, env_vars, expected_url):
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    # Call the function and assert the result
    assert connector_redis.format_url_from_env() == expected_url

    # Clean up environment variables
    for key in env_vars.keys():
        del os.environ[key]

import pytest
from comps.vectorstores.utils.connectors.connector_redis import ConnectorRedis
import os
import random
import string

@pytest.fixture
def connector_redis():
    return ConnectorRedis()

@pytest.mark.parametrize(
    "env_vars, expected_url_template",
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
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "REDIS_USERNAME": 'test', "REDIS_PASSWORD": "{password}", "VECTOR_STORE": "redis-cluster"},
            "redis://test:{password}@localhost:1234/?cluster=true",
        ),
        (
            {"REDIS_HOST": "localhost", "REDIS_PORT": "1234", "REDIS_USERNAME": 'test', "REDIS_PASSWORD": "{password}", "VECTOR_STORE": "redis"},
            "redis://test:{password}@localhost:1234/",
        ),
    ],
)
def test_format_url_from_env(connector_redis, env_vars, expected_url_template):
    # Generate a random password for each test run
    password_chars = string.ascii_letters + string.digits + string.punctuation # nosec B311
    password = ''.join(random.choice(password_chars) for _ in range(12)) # nosec B311
    
    # Replace password placeholder in env_vars and expected_url if needed
    for key in env_vars:
        if isinstance(env_vars[key], str) and "{password}" in env_vars[key]:
            env_vars[key] = env_vars[key].format(password=password)
    
    expected_url = expected_url_template.format(password=password) if "{password}" in expected_url_template else expected_url_template

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
    
    try:
        # Call the function and assert the result
        assert connector_redis.format_url_from_env() == expected_url
    finally:
        # Clean up environment variables
        for key in env_vars.keys():
            if key in os.environ:
                del os.environ[key]

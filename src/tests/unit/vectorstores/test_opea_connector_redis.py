import pytest
from comps.vectorstores.utils.connectors.connector_redis import ConnectorRedis

@pytest.fixture
def connector_redis():
    return ConnectorRedis()

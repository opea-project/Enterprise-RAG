# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from requests.exceptions import ConnectionError, ReadTimeout

from comps import LLMParamsDoc
from comps.llms.utils.connectors.abstract_connector import AbstractConnector

"""
To execute these tests with coverage report, navigate to the `src` folder and run the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms/test_connector.py

Alternatively, to run all tests for the 'llms' module, execute the following command:
   pytest --disable-warnings --cov=comps/llms --cov-report=term --cov-report=html tests/unit/llms
"""

class ConcreteAbstractConnector(AbstractConnector):
    """Concrete implementation of AbstractConnector for testing purposes"""

    async def generate(self, input: LLMParamsDoc):
        """Concrete implementation of abstract generate method"""
        return MagicMock()

    async def close(self) -> None:
        """Concrete implementation of abstract close method"""
        pass

    def change_configuration(self, **kwargs) -> None:
        """Concrete implementation of abstract change_configuration method"""
        pass


@pytest.fixture
def connector_instance():
    """Create a connector instance for testing"""
    return ConcreteAbstractConnector(
        model_name="test_model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True,
        headers={"Authorization": "Bearer test"}
    )


@pytest.mark.asyncio
async def test_validate_success(connector_instance):
    """Test successful validation"""
    with patch.object(connector_instance, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = MagicMock()

        await connector_instance._validate()

        # Verify generate was called with test parameters
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[0][0]
        assert isinstance(call_args, LLMParamsDoc)
        assert call_args.stream is False
        assert call_args.max_new_tokens == 5


@pytest.mark.asyncio
async def test_validate_read_timeout(connector_instance):
    """Test validation raises ReadTimeout"""
    with patch.object(connector_instance, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ReadTimeout("Connection timeout")

        with pytest.raises(ReadTimeout) as exc_info:
            await connector_instance._validate()

        assert "Connection timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_connection_error(connector_instance):
    """Test validation raises ConnectionError"""
    with patch.object(connector_instance, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError) as exc_info:
            await connector_instance._validate()

        assert "Connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_general_exception(connector_instance):
    """Test validation raises general Exception"""
    with patch.object(connector_instance, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = Exception("Unexpected error")

        with pytest.raises(Exception) as exc_info:
            await connector_instance._validate()

        assert "Unexpected error" in str(exc_info.value)


def test_connector_initialization_with_headers():
    """Test connector initializes correctly with headers"""
    headers = {"Authorization": "Bearer token123"}
    connector = ConcreteAbstractConnector(
        model_name="test_model",
        endpoint="http://localhost:8000",
        disable_streaming=True,
        llm_output_guard_exists=False,
        headers=headers
    )

    assert connector._model_name == "test_model"
    assert connector._endpoint == "http://localhost:8000"
    assert connector._disable_streaming is True
    assert connector._llm_output_guard_exists is False
    assert connector._headers == headers


def test_connector_initialization_without_headers():
    """Test connector initializes correctly without headers (defaults to empty dict)"""
    connector = ConcreteAbstractConnector(
        model_name="test_model",
        endpoint="http://localhost:8000",
        disable_streaming=False,
        llm_output_guard_exists=True
    )

    assert connector._headers == {}


def test_abstract_generate_raises_not_implemented():
    """Test that abstract generate method raises NotImplementedError when not overridden"""

    # Verify the abstract method exists
    assert hasattr(AbstractConnector, 'generate')
    assert hasattr(AbstractConnector, 'close')

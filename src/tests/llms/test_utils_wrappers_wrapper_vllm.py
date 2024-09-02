# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Run `pytest --disable-warnings --cov=comps/llms/utils --cov-report=term --cov-report=html tests/llms` to execute unit test with coverage report.
"""

# FIXME: unit tests not working after rewriting Tomek's code
import asyncio
import unittest
from unittest.mock import patch, MagicMock
from fastapi.responses import StreamingResponse
from comps.llms.utils.wrappers.wrapper_vllm import llm_generate, LLMParamsDoc, GeneratedDoc

class TestLLMGenerate(unittest.TestCase):

    @patch('comps.llms.utils.wrappers.wrapper_vllm.VLLMOpenAI')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.StreamingResponse')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.statistics_dict')
    def test_llm_generate_non_streaming(self, mock_statistics_dict, mock_streaming_response, mock_vllm_openai):
        # Mock params
        params = LLMParamsDoc(
            query="Test query",
            streaming=False,
            max_new_tokens=50,
            repetition_penalty=1.0,
            temperature=0.7,
            top_k=50,
            top_p=0.9
        )

        # Mock VLLMOpenAI response
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Generated text"
        mock_vllm_openai.return_value = mock_llm

        # Mock self object
        mock_self = MagicMock()
        mock_self._model_server_endpoint = "http://localhost"
        mock_self._model_name = "test-model"

        # Call the function
        result = llm_generate(mock_self, params)

        # Assertions
        self.assertIsInstance(result, GeneratedDoc)
        self.assertEqual(result.text, "Generated text")
        self.assertEqual(result.prompt, "Test query")

    @patch('comps.llms.utils.wrappers.wrapper_vllm.VLLMOpenAI')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.StreamingResponse')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.statistics_dict')
    def test_llm_generate_streaming(self, mock_statistics_dict, mock_streaming_response, mock_vllm_openai):
        # Mock params
        params = LLMParamsDoc(
            query="Test query",
            streaming=True,
            max_new_tokens=50,
            repetition_penalty=1.0,
            temperature=0.7,
            top_k=50,
            top_p=0.9
        )

        # Mock VLLMOpenAI response
        mock_llm = MagicMock()
        mock_vllm_openai.return_value = mock_llm

        # Mock StreamingResponse to return an actual StreamingResponse object
        def streaming_response_side_effect(*args, **kwargs):
            return StreamingResponse(iter(["Generated text part 1", "Generated text part 2"]))
        mock_streaming_response.side_effect = streaming_response_side_effect

        # Helper function to collect items from async generator
        async def collect_async_generator(async_gen):
            items = []
            async for item in async_gen:
                items.append(item)
            return items

        # Mock self object
        mock_self = MagicMock()
        mock_self._model_server_endpoint = "http://localhost"
        mock_self._model_name = "test-model"

        # Call the function
        result = llm_generate(mock_self, params)

        # Collect items from the async generator
        collected_items = asyncio.run(collect_async_generator(result.body_iterator))

        # Assertions
        self.assertIsInstance(result, StreamingResponse)
        self.assertEqual(collected_items, ["Generated text part 1", "Generated text part 2"])


    @patch('comps.llms.utils.wrappers.wrapper_vllm.VLLMOpenAI')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.StreamingResponse')
    @patch('comps.llms.utils.wrappers.wrapper_vllm.statistics_dict')
    def test_llm_generate_exception(self, mock_statistics_dict, mock_streaming_response, mock_vllm_openai):
        # Mock params
        params = LLMParamsDoc(
            query="Test query",
            streaming=False,
            max_new_tokens=50,
            repetition_penalty=1.0,
            temperature=0.7,
            top_k=50,
            top_p=0.9
        )

        # Mock VLLMOpenAI response
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("Error occurred")
        mock_vllm_openai.return_value = mock_llm

        # Mock self object
        mock_self = MagicMock()
        mock_self._model_server_endpoint = "http://localhost"
        mock_self._model_name = "test-model"

        # Call the function and assert that it raises an exception
        with self.assertRaises(Exception):
            llm_generate(mock_self, params)
        

if __name__ == '__main__':
    unittest.main()
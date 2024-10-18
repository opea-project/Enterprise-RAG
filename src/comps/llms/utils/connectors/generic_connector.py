# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from typing import Union

import openai
from fastapi.responses import StreamingResponse
from huggingface_hub import InferenceClient
from requests.exceptions import RequestException

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    get_opea_logger,
)
from comps.llms.utils.connectors.connector import LLMConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class TGIConnector:
    def __init__(self, model_name: str, endpoint: str):
        self._endpoint = endpoint
        self._client = InferenceClient(model=endpoint, timeout=600)


    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        try:
            generator = self._client.text_generation(
                            prompt=input.query,
                            stream=input.streaming,
                            max_new_tokens=input.max_new_tokens,
                            repetition_penalty=input.repetition_penalty,
                            temperature=input.temperature,
                            top_k=input.top_k,
                            top_p=input.top_p,
                        )

        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to invoke the Generic TGI Connector. Unable to connect to '{self._endpoint}', status_code: {error_code}. Check if the endpoint is available and running."
            logger.error(error_message)
            raise RequestException(error_message)
        except Exception as e:
            logger.error(f"Error invoking TGI: {e}")
            raise Exception(f"Error invoking TGI: {e}")

        if input.streaming:
            stream_gen_time = []
            start_local = time.time()
            def stream_generator():
                chat_response = ""
                try:
                    for text in generator:
                        stream_gen_time.append(time.time() - start_local)
                        chat_response += text
                        chunk_repr = repr(text)
                        logger.debug("[llm - chat_stream] chunk:{chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                    logger.debug("[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Error streaming from TGI: {e}")
                    yield "data: [ERROR]\n\n"
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            return GeneratedDoc(text=generator, prompt=input.query,
                                output_guardrail_params=input.output_guardrail_params)

class VLLMConnector:
    def __init__(self, model_name: str, endpoint: str):
        self._model_name = model_name
        self._endpoint = endpoint+"/v1"
        self._client = openai.OpenAI(
            api_key="EMPTY",
            base_url=self._endpoint,
            timeout=600,
        )

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        try:
            generator = self._client.completions.create(
                model=self._model_name,
                prompt=input.query,
                max_tokens=input.max_new_tokens,
                temperature=input.temperature,
                top_p=input.top_p,
                stream=input.streaming,
            )
        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to invoke the Generic VLLM Connector. Unable to connect to '{self._endpoint}', status_code: {error_code}. Check if the endpoint is available and running."
            logger.error(error_message)
            raise RequestException(error_message)
        except Exception as e:
            logger.error(f"Error invoking VLLM: {e}")
            raise Exception(f"Error invoking VLLM: {e}")

        if input.streaming:
            stream_gen_time = []
            start_local = time.time()

            def stream_generator():
                chat_response = ""
                try:
                    for chunk in generator:
                        text = chunk.choices[0].text
                        stream_gen_time.append(time.time() - start_local)
                        chat_response += text
                        chunk_repr = repr(text)
                        logger.debug(f"[llm - chat_stream] chunk:{chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                    logger.debug(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Error streaming from VLLM: {e}")
                    yield "data: [ERROR]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            return GeneratedDoc(text=generator.choices[0].text, prompt=input.query,
                                output_guardrail_params=input.output_guardrail_params)

SUPPORTED_INTEGRATIONS = {
    "tgi": TGIConnector,
    "vllm": VLLMConnector
}

class GenericLLMConnector(LLMConnector):
    _instance = None
    def __new__(cls, model_name: str, model_server: str, endpoint: str):
        if cls._instance is None:
            cls._instance = super(GenericLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint)
        else:
            if (cls._instance._endpoint != endpoint or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing GenericLLMConnector instance has different parameters: "
                              f"{cls._instance._endpoint} != {endpoint}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str):
        super().__init__(model_name, model_server, endpoint)
        self._connector = self._get_connector()
        self._validate()

    def _get_connector(self):
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"

            logger.error(error_message)
            raise ValueError(error_message)

        return SUPPORTED_INTEGRATIONS[self._model_server](self._model_name, self._endpoint)

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return self._connector.generate(input)

    def change_configuration(self, **kwargs) -> None:
        logger.error("Change configuration not supported for GenericLLMConnector")
        raise NotImplementedError
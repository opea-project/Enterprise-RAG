# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Union

from fastapi.responses import StreamingResponse
from langchain_community.llms import VLLMOpenAI
from langchain_huggingface import HuggingFaceEndpoint
from requests.exceptions import RequestException

from comps import GeneratedDoc, LLMParamsDoc, get_opea_logger
from comps.llms.utils.connectors.connector import LLMConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class TGIConnector:
    def __init__(self, model_name: str, endpoint: str):
        self._endpoint = endpoint

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        connector = HuggingFaceEndpoint(
            endpoint_url=self._endpoint,
            max_new_tokens=input.max_new_tokens,
            top_k=input.top_k,
            top_p=input.top_p,
            temperature=input.temperature,
            repetition_penalty=input.repetition_penalty,
        )

        if input.streaming:
            try:
                def stream_generator():
                    chat_response = ""
                    for text in connector.stream(input.query):
                        chat_response += text
                        chunk_repr = repr(text)
                        yield f"data: {chunk_repr}\n\n"
                    logger.debug(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            except Exception as e:
                logger.error(f"Error streaming from TGI: {e}")
                raise Exception(f"Error streaming from TGI: {e}")
        else:
            try:
                response = connector.invoke(input.query)
                return GeneratedDoc(text=response, prompt=input.query,
                                    output_guardrail_params=input.output_guardrail_params)
            except RequestException as e:
                error_code = e.response.status_code if e.response else 'No response'
                error_message = f"Failed to invoke the Langchain TGI Connector. Unable to connect to '{e.request.url}', status_code: {error_code}. Check if the endpoint is available and running."
                logger.error(error_message)
                raise RequestException(error_message)
            except Exception as e:
                logger.error(f"Error invoking TGI: {e}")
                raise Exception(f"Error invoking TGI: {e}")

class VLLMConnector:
    def __init__(self, model_name: str, endpoint: str):
        self._endpoint = endpoint+"/v1"
        self._model_name = model_name

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        try:
            llm = VLLMOpenAI(
                openai_api_key="EMPTY",
                openai_api_base=self._endpoint,
                max_tokens=input.max_new_tokens,
                model_name=self._model_name,
                top_p=input.top_p,
                temperature=input.temperature,
                streaming=input.streaming,
            )
        except Exception as e:
            error_message = "Failed to invoke the Langchain VLLM Connector. Check if the endpoint '{self._endpoint}' is correct and the VLLM service is running."
            logger.error(error_message)
            raise Exception(f"{error_message}: {e}")

        if input.streaming:
            try:
                def stream_generator():
                    chat_response = ""
                    for text in llm.stream(input.query):
                        chat_response += text
                        chunk_repr = repr(text)
                        yield f"data: {chunk_repr}\n\n"
                    logger.debug(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            except Exception as e:
                logger.error(f"Error streaming from VLLM: {e}")
                raise Exception(f"Error streaming from VLLM: {e}")
        else:
            try:
                response = llm.invoke(input.query)
                return GeneratedDoc(text=response, prompt=input.query,
                                    output_guardrail_params=input.output_guardrail_params)
            except Exception as e:
                logger.error(f"Error invoking VLLM: {e}")
                raise Exception(f"Error invoking VLLM: {e}")

SUPPORTED_INTEGRATIONS = {
    "tgi": TGIConnector,
    "vllm": VLLMConnector
}

class LangchainLLMConnector(LLMConnector):
    _instance = None
    def __new__(cls, model_name: str, model_server: str, endpoint: str):
        if cls._instance is None:
            cls._instance = super(LangchainLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint)
        else:
            if (cls._instance._endpoint != endpoint or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing LangchainLLMConnector instance has different parameters: "
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
        logger.error("Change configuration not supported for LangchainLLMConnector")
        raise NotImplementedError
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import httpx
import json
import time
from typing import Optional, Dict, Union

import openai
from fastapi.responses import StreamingResponse
from requests.exceptions import ConnectionError, ReadTimeout, RequestException

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    LLMPromptTemplate,
    get_opea_logger,
    TextDoc
)
from comps.cores.proto.api_protocol import (
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    DeltaMessage
)
from comps.llms.utils.connectors.connector import LLMConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class VLLMConnector:
    def __init__(self, model_name: str, endpoint: str, disable_streaming: bool, llm_output_guard_exists: bool, openai_format_streaming: bool = False, headers: Optional[Dict[str, str]] = None):
        self._model_name = model_name
        self._endpoint = endpoint+"/v1"
        self._disable_streaming = disable_streaming
        self._llm_output_guard_exists = llm_output_guard_exists
        self._headers = headers if headers is not None else {}
        self._openai_format_streaming = openai_format_streaming
        self._client = openai.AsyncOpenAI(
            api_key="EMPTY",
            base_url=self._endpoint,
            timeout=120,
            default_headers=self._headers,
            http_client=httpx.AsyncClient(headers={"Connection": "close"})
        )

    async def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        try:
            generator = await self._client.chat.completions.create(
                model=self._model_name,
                messages=input.messages.model_dump() if isinstance(input.messages, LLMPromptTemplate) else input.messages,
                max_tokens=input.max_new_tokens,
                temperature=input.temperature,
                top_p=input.top_p,
                stream=input.stream and not self._disable_streaming,
            )
        except ReadTimeout as e:
            error_message = f"Failed to stream from the Generic VLLM Connector. Connection established with '{e.request.url}' but " \
                "no response received in set timeout. Check if the model is running and all optimizations are set correctly."
            logger.error(error_message)
            raise ReadTimeout(error_message)
        except ConnectionError as e:
            error_message = f"Failed to stream from the Generic VLLM Connector. Unable to connect to '{e.request.url}'. Check if the endpoint is available and running."
            logger.error(error_message)
            raise ConnectionError(error_message)
        except RequestException as e:
            error_code = e.response.status_code if e.response else 'No response'
            error_message = f"Failed to stream from the Generic VLLM Connector. Unable to connect to '{self._endpoint}', status_code: {error_code}. Check if the endpoint is available and running."
            logger.error(error_message)
            raise RequestException(error_message)
        except openai.BadRequestError as e:
            error_message = f"Error streaming from VLLM:: {e}"
            logger.error(error_message)
            raise
        except Exception as e:
            logger.error(f"Error streaming from VLLM: {e}")
            raise Exception(f"Error streaming from VLLM: {e}")

        reranked_docs_output = []
        if isinstance(input.data, dict) and 'reranked_docs' in input.data:
            logger.debug(f"Reranked documents found in input data. {input.data['reranked_docs']}")
            reranked_docs_output = [TextDoc(**rdoc).to_reranked_doc().model_dump(exclude=['id']) for rdoc in input.data['reranked_docs']]

        user_prompt = [msg.content for msg in input.messages if msg.role == "user"]
        if not user_prompt:
            raise ValueError("No user prompt found in messages.")
        user_prompt = user_prompt[0]

        if input.stream and not self._disable_streaming:
            if self._llm_output_guard_exists:
                chat_response = ""
                async for chunk in generator:
                    text = chunk.choices[0].delta.content
                    chat_response += text
                return GeneratedDoc(text=chat_response, prompt=user_prompt, stream=input.stream,
                                output_guardrail_params=input.output_guardrail_params, data={"reranked_docs": reranked_docs_output})

            stream_gen_time = []
            start_local = time.time()

            async def stream_generator():
                chat_response = ""
                try:
                    async for chunk in generator:
                        text = chunk.choices[0].delta.content
                        stream_gen_time.append(time.time() - start_local)
                        chat_response += text

                        if self._openai_format_streaming:
                            stream_chunk = ChatCompletionStreamResponse(
                                model=self._model_name,
                                choices=[
                                    ChatCompletionResponseStreamChoice(
                                        index=0,
                                        delta=DeltaMessage(content=text),
                                        finish_reason=None
                                    )
                                ]
                            )
                            chunk_json = stream_chunk.model_dump_json()
                            logger.debug(f"[llm - chat_stream] OpenAI format chunk: {chunk_json}")
                            yield f"data: {chunk_json}\n\n"
                        else:
                            chunk_repr = repr(text)
                            logger.debug(f"[llm - chat_stream] chunk:{chunk_repr}")
                            yield f"data: {chunk_repr}\n\n"

                    logger.debug(f"[llm - chat_stream] stream response: {chat_response}")

                    if self._openai_format_streaming:
                        final_chunk = ChatCompletionStreamResponse(
                            model=self._model_name,
                            choices=[
                                ChatCompletionResponseStreamChoice(
                                    index=0,
                                    delta=DeltaMessage(content=""),
                                    finish_reason="stop"
                                )
                            ]
                        )
                        yield f"data: {final_chunk.model_dump_json()}\n\n"

                    yield "data: [DONE]\n\n"

                    if isinstance(input.data, dict):
                        data = { "reranked_docs": reranked_docs_output }
                        logger.debug(f"[llm - chat_stream] appending json data: {data}")
                        yield f"json: {json.dumps(data)}\n\n"
                    else:
                        logger.debug("Not appending json data since it is not a dict")
                except httpx.ReadTimeout as e:
                    error_message = f"Failed to invoke the Generic VLLM Connector. Connection established with '{e.request.url}' but " \
                        "no response received in set timeout. Check if the model is running and all optimizations are set correctly."
                    logger.error(error_message)
                    raise httpx.ReadTimeout(error_message)
                except httpx.ConnectError as e:
                    error_message = f"Failed to invoke the Generic VLLM Connector. Unable to connect to '{e.request.url}'. Check if the endpoint is available and running."
                    logger.error(error_message)
                    raise httpx.ConnectError(error_message)
                except RequestException as e:
                    error_code = e.response.status_code if e.response else 'No response'
                    error_message = f"Failed to invoke the Generic VLLM Connector. Unable to connect to '{self._endpoint}', status_code: {error_code}. Check if the endpoint is available and running."
                    logger.error(error_message)
                    raise RequestException(error_message)
                except Exception as e:
                    logger.error(f"Error streaming from VLLM: {e}")
                    raise Exception(f"Error streaming from VLLM: {e}")

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            choices = [ChatCompletionResponseChoice(**c.dict()) for c in generator.choices if c.message and c.message.content]
            return GeneratedDoc(choices=choices, text=generator.choices[0].message.content, prompt=user_prompt, stream=input.stream,
                                output_guardrail_params=input.output_guardrail_params, data={"reranked_docs": reranked_docs_output})

SUPPORTED_INTEGRATIONS = {
    "vllm": VLLMConnector
}

class GenericLLMConnector(LLMConnector):
    _instance = None
    def __new__(cls, model_name: str, model_server: str, endpoint: str, disable_streaming: bool, llm_output_guard_exists: bool, openai_format_streaming: bool, headers: object):
        if cls._instance is None:
            cls._instance = super(GenericLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, disable_streaming, llm_output_guard_exists, openai_format_streaming, headers)
        else:
            if (cls._instance._endpoint != endpoint or
                cls._instance._model_server != model_server or
                cls._instance._disable_streaming != disable_streaming or
                cls._instance._llm_output_guard_exists != llm_output_guard_exists or
                cls._instance._openai_format_streaming != openai_format_streaming):
                logger.warning(f"Existing GenericLLMConnector instance has different parameters: "
                              f"{cls._instance._endpoint} != {endpoint}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              f"{cls._instance._disable_streaming} != {disable_streaming}, "
                              f"{cls._instance._llm_output_guard_exists} != {llm_output_guard_exists}, "
                              f"{cls._instance._openai_format_streaming} != {openai_format_streaming}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str, disable_streaming: bool, llm_output_guard_exists: bool, openai_format_streaming: bool, headers: object):
        super().__init__(model_name, model_server, endpoint, disable_streaming, llm_output_guard_exists, openai_format_streaming, headers)
        self._connector = self._get_connector()
        asyncio.run(self._validate())

    def _get_connector(self):
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"

            logger.error(error_message)
            raise ValueError(error_message)
        kwargs = {
            "model_name": self._model_name,
            "endpoint": self._endpoint,
            "disable_streaming": self._disable_streaming,
            "llm_output_guard_exists": self._llm_output_guard_exists,
            "openai_format_streaming": self._openai_format_streaming
        }
        if self._model_server == "vllm":
            kwargs["headers"] = self._headers
        return SUPPORTED_INTEGRATIONS[self._model_server](**kwargs)

    async def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return await self._connector.generate(input)

    def change_configuration(self, **kwargs) -> None:
        logger.error("Change configuration not supported for GenericLLMConnector")
        raise NotImplementedError

import logging
from fastapi.responses import StreamingResponse
from comps import (
    LLMParamsDoc,
    GeneratedDoc,
)
from comps.llms.utils.connectors.connector import LLMConnector
from typing import Union

class TGIConnector:
    def __init__(self, model_name: str, endpoint: str, model_server: str):
        self._endpoint = endpoint
        self._model_name = model_name
        self._model_server = model_server

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        from langchain_huggingface import HuggingFaceEndpoint
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
                        chunk_repr = repr(text.encode("utf-8"))
                        yield f"data: {chunk_repr}\n\n"
                    print(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            except Exception as e:
                logging.error(f"Error streaming from VLLM: {str(e)}")
                raise
        else:
            try:
                response = connector.invoke(input.query)
                return GeneratedDoc(text=response, prompt=input.query)
            except Exception as e:
                logging.error(f"Error invoking TGI: {str(e)}")
                raise

class VLLMConnector:
    def __init__(self, model_name: str, endpoint: str, model_server: str):
        self._endpoint = endpoint+"/v1"
        self._model_name = model_name
        self._model_server = model_server

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        from langchain_community.llms import VLLMOpenAI
        llm = VLLMOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=self._endpoint,
            max_tokens=input.max_new_tokens,
            model_name=self._model_name,
            top_p=input.top_p,
            temperature=input.temperature,
            streaming=input.streaming,
        )

        if input.streaming:
            try:
                def stream_generator():
                    chat_response = ""
                    for text in llm.stream(input.query):
                        chat_response += text
                        chunk_repr = repr(text.encode("utf-8"))
                        yield f"data: {chunk_repr}\n\n"
                    print(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            except Exception as e:
                logging.error(f"Error invoking VLLM: {str(e)}")
                raise
        else:
            try:
                response = llm.invoke(input.query)
                return GeneratedDoc(text=response, prompt=input.query)
            except Exception as e:
                logging.error(f"Error invoking VLLM: {str(e)}")
                raise

SUPPORTED_INTEGRATIONS = {
    "tgi": TGIConnector,
    "vllm": VLLMConnector
}

class LangchainLLMConnector(LLMConnector):
    _instance = None
    def __new__(cls, model_name: str, endpoint: str, model_server: str):
        if cls._instance is None:
            cls._instance = super(LangchainLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, model_server)
        else:
            if (cls._instance._endpoint!= endpoint or 
                cls._instance._model_server != model_server):
                logging.warning(f"Existing LangchainLLMConnector instance has different parameters: "
                              f"{cls._instance._endpoint} != {endpoint}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, endpoint: str, model_server: str):
        super().__init__(model_name, endpoint, model_server)
        self._connector = self._get_connector(model_name, endpoint, model_server)
        # TODO: fix validate false positive
        self._validate()

    def _get_connector(self, model_name: str, endpoint: str, model_server: str):
        if model_server not in SUPPORTED_INTEGRATIONS:
            raise ValueError("Invalid model server")
        return SUPPORTED_INTEGRATIONS[model_server](model_name, endpoint, model_server)

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return self._connector.generate(input)

    def change_configuration(self, **kwargs) -> None:
        raise NotImplementedError
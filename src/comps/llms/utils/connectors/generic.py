from comps.llms.utils.connectors.connector import LLMConnector
from huggingface_hub import InferenceClient
import time
import logging
from fastapi.responses import StreamingResponse
from comps import (
    LLMParamsDoc,
    GeneratedDoc,
    statistics_dict,
)
from typing import Union

class TGIConnector:
    def __init__(self, model_name: str, endpoint: str, model_server: str):
        self._endpoint = endpoint
        self._client = InferenceClient(model=endpoint, timeout=600)

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        generator = self._client.text_generation(
                        prompt=input.query,
                        stream=input.streaming,
                        max_new_tokens=input.max_new_tokens,
                        repetition_penalty=input.repetition_penalty,
                        temperature=input.temperature,
                        top_k=input.top_k,
                        top_p=input.top_p,
                    )

        if input.streaming:
            stream_gen_time = []
            start_local = time.time()
            def stream_generator():
                chat_response = ""
                try:
                    for text in generator:
                        stream_gen_time.append(time.time() - start_local)
                        chat_response += text
                        chunk_repr = repr(text.encode("utf-8"))
                        logging.debug("[llm - chat_stream] chunk:{chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                    logging.debug("[llm - chat_stream] stream response: {chat_response}")
                    statistics_dict[self.name].append_latency(stream_gen_time[-1], stream_gen_time[0])
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logging.error(f"Error streaming from TGI: {str(e)}")
                    yield "data: [ERROR]\n\n"
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            return GeneratedDoc(text=generator, prompt=input.query)

class VLLMConnector:
    def __init__(self, model_name: str, endpoint: str, model_server: str):
        import openai
        self._model_name = model_name
        self._endpoint = endpoint+"/v1"
        self._client = openai.OpenAI(
            api_key="EMPTY",
            base_url=self._endpoint,
            timeout=600,
        )

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        generator = self._client.completions.create(
            model=self._model_name,
            prompt=input.query,
            max_tokens=input.max_new_tokens,
            temperature=input.temperature,
            top_p=input.top_p,
            stream=input.streaming,
        )

        if input.streaming:
            stream_gen_time = []
            start_local = time.time()

            def stream_generator():
                chat_response = ""
                try:
                    for chunk in generator:
                        text = chunk.choices[0].text
                        print(chunk)
                        print(text)
                        stream_gen_time.append(time.time() - start_local)
                        chat_response += text
                        chunk_repr = repr(text.encode("utf-8"))
                        logging.debug(f"[llm - chat_stream] chunk:{chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                    logging.debug(f"[llm - chat_stream] stream response: {chat_response}")
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logging.error(f"Error streaming from VLLM: {str(e)}")
                    yield "data: [ERROR]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            return GeneratedDoc(text=generator.choices[0].text, prompt=input.query)

SUPPORTED_INTEGRATIONS = {
    "tgi": TGIConnector,
    "vllm": VLLMConnector
}

class GenericLLMConnector(LLMConnector):
    _instance = None
    def __new__(cls, model_name: str, endpoint: str, model_server: str):
        if cls._instance is None:
            cls._instance = super(GenericLLMConnector, cls).__new__(cls)
            cls._instance._initialize(model_name, endpoint, model_server)
        else:
            if (cls._instance._endpoint!= endpoint or
                cls._instance._model_server != model_server):
                logging.warning(f"Existing GenericLLMConnector instance has different parameters: "
                              f"{cls._instance._endpoint} != {endpoint}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, endpoint: str, model_server: str):
        super().__init__(model_name, endpoint, model_server)
        self._connector = self._get_connector(model_name, endpoint, model_server)
        self._validate()

    def _get_connector(self, model_name: str, endpoint: str, model_server: str):
        if model_server not in SUPPORTED_INTEGRATIONS:
            raise ValueError("Invalid model server")
        return SUPPORTED_INTEGRATIONS[model_server](model_name, endpoint, model_server)

    def generate(self, input: LLMParamsDoc) -> Union[GeneratedDoc, StreamingResponse]:
        return self._connector.generate(input)

    def change_configuration(self, **kwargs) -> None:
        raise NotImplementedError